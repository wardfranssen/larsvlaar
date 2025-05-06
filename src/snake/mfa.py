from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken
import src.snake.main as main
import os
import base64
import secrets

config = main.config
iterations = config["ENCRYPTION"]["ITERATIONS"]
redis_prefix = config["REDIS"]["PREFIX"]
mfa_exp = config["MFA"]["EXP"]


def derive_key(data: bytes, salt: bytes, iterations: int) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=32, salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    key = kdf.derive(data)
    return key


def encrypt_mfa_code(mfa_code: str, email: str) -> str:
    salt = os.urandom(32)
    user_key = base64.urlsafe_b64encode(derive_key(email.encode(), salt, iterations))

    cipher = Fernet(user_key)
    encrypted_code = cipher.encrypt(mfa_code.encode())

    return base64.b64encode(salt + encrypted_code).decode()


def decrypt_mfa_code(encrypted_data: str, email: str) -> str:
    raw_data = base64.b64decode(encrypted_data)
    salt, encrypted_code = raw_data[:32], raw_data[32:]

    user_key = base64.urlsafe_b64encode(derive_key(email.encode(), salt, iterations))
    cipher = Fernet(user_key)

    return cipher.decrypt(encrypted_code).decode()


def is_valid_code(user_id: str, code: str, email: str) -> dict:
    code_data = main.redis_client.get(f"{redis_prefix}:mfa:{user_id}")

    if not code_data:
        return {
            "id_valid": False,
            "message": "Code is verlopen"
        }

    try:
        decrypted_code = decrypt_mfa_code(code_data, email)
    except InvalidToken:
        return {
            "id_valid": False,
            "message": "Ongeldige token"
        }

    if not secrets.compare_digest(decrypted_code, code):
        return {
            "id_valid": False,
            "message": "Onjuiste code"
        }

    return {
        "id_valid": True
    }


def generate_code(user_id: str, email: str) -> str:
    code = f"{secrets.choice(['#', ''])}{secrets.choice(main.boodschappen_lijstje).lower()}{int(secrets.randbelow(1_000_000))}"
    code_data = encrypt_mfa_code(code, email)

    main.redis_client.setex(f"{redis_prefix}:mfa:{user_id}", mfa_exp, code_data)
    return code

