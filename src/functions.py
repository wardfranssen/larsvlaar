import time
import uuid


def get_jwt() -> str:
    return str(f"{uuid.uuid4()}~{time.time()}")


def is_valid_jwt(jwt) -> bool:
    jwt_creation_time = float(jwt.split("~")[1])
    if time.time() - jwt_creation_time > 25 or jwt == "":
        return False
    return True