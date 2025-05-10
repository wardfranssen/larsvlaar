from logging.handlers import RotatingFileHandler
from cryptography.fernet import Fernet
import logging
import redlock
import pymysql
import secrets
import base64
import redis
import time
import json


def get_general_messages(user_id: str) -> list:
    try:
        result = redis_client.lrange(f"{redis_prefix}:user:{user_id}:general_messages", 0, -1)
        redis_client.delete(f"{redis_prefix}:user:{user_id}:general_messages")

        messages = []
        for message in result:
            messages.append(json.loads(message))

        return messages
    except Exception as e:
        logger.error(f"get_general_messages() for {user_id}: {e}", exc_info=True)
        return []


# Todo: Make func like this for general messages (e.g. being kicked from lobby/custom game or logged out cause someone else logged in)
# Todo: Make this a wrapper function
def get_pending_invites(user_id: str) -> dict:
    try:
        invites = {}
        invite_types = [
            "received",
            "sent"
        ]

        for invite_type in invite_types:
            invites_ids = redis_client.smembers(f"{redis_prefix}:user:{user_id}:invites:{invite_type}")
            invites[invite_type] = []

            for invite_id in invites_ids:
                invite = redis_client.getex(f"{redis_prefix}:invite:{invite_id}")

                if not invite:
                    redis_client.srem(f"{redis_prefix}:user:{user_id}:invites:{invite_type}", invite_id)
                    continue

                invite = json.loads(invite)
                created_at = invite["created_at"]

                if int(time.time()) - created_at > 13:
                    redis_client.srem(f"{redis_prefix}:user:{user_id}:invites:{invite_type}", invite_id)
                    continue

                if invite_type == "received":
                    user = "from"
                else:
                    user = "to"

                _user_id = invite[user]
                invite_data = {
                    "invite_id": invite_id,
                    f"{user}_username": get_username(_user_id),
                    f"{user}_user_id": _user_id,
                    f"{user}_pfp_version": get_pfp_version(_user_id),
                    "game_mode": invite["game_mode"],
                    "lobby_id": invite["lobby_id"],
                    "created_at": created_at,
                }
                invites[invite_type].append(invite_data)
        return {
            "server_time": int(time.time()),
            "invites": invites
        }
    except Exception as e:
        logger.error(f"get_pending_invites() for {user_id}: {e}", exc_info=True)
        return {
            "server_time": int(time.time()),
            "invites": []
        }


def connect_to_db(cursorclass=None):
    connection_params = {
        'host': config["DB"]["HOST"],
        'user': config["DB"]["USER"],
        'password': config["DB"]["PASSWORD"],
        'database': config["DB"]["NAME"],
        'charset': 'utf8mb4'
    }

    if cursorclass:
        connection_params['cursorclass'] = cursorclass

    return pymysql.connect(**connection_params)


def save_user_to_redis(user_id: str):
    try:
        con = connect_to_db(pymysql.cursors.DictCursor)
        cur = con.cursor()

        cur.execute("SELECT username, pfp_version FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()

        if not user:
            return

        username = user["username"]
        pfp_version = user["pfp_version"]

        redis_client.hset(f"{redis_prefix}:user:{user_id}", "username", username)
        redis_client.hset(f"{redis_prefix}:user:{user_id}", "pfp_version", pfp_version)

        redis_client.expire(f"{redis_prefix}:user:{user_id}", 3600)
        return user
    finally:
        if con:
            try:
                con.close()
                cur.close()
            except Exception:
                pass


def get_username(user_id: str) -> str | None:
    username = redis_client.hget(f"{redis_prefix}:user:{user_id}", "username")
    if username:
        return username

    user = save_user_to_redis(user_id)
    if not user:
        return

    username = user["username"]

    return username


def get_pfp_version(user_id: str) -> int | None:
    pfp_version = redis_client.hget(f"{redis_prefix}:user:{user_id}", "pfp_version")
    if pfp_version:
        return int(pfp_version)

    user = save_user_to_redis(user_id)
    if not user:
        return

    pfp_version = user["pfp_version"]

    return int(pfp_version)


def get_status(user_id: str):
    is_online = redis_client.exists(f"{redis_prefix}:online:{user_id}")
    is_active = redis_client.exists(f"{redis_prefix}:active:{user_id}")

    if not is_online:
        status = "offline"
    elif not is_active:
        status = "inactive"
    else:
        status = "active"

    return status


def get_lock(lock_key: str):
    for attempt in range(redis_max_retries):
        lock = redlock.lock(lock_key, lock_timeout)
        if lock:
            return lock
        else:
            print("RACE CONDITION")
            time.sleep(redis_retry_delay)
    else:
        print("FAILED TO GET REDLOCK")
        logger.error("FAILED TO GET REDLOCK", exc_info=True)
        return


def encrypt_join_token(boodschappen: str) -> str:
    key = Fernet.generate_key()
    cipher = Fernet(key)
    encrypted_code = cipher.encrypt(boodschappen.encode())
    return base64.b64encode(encrypted_code).decode()


def generate_join_token():
    want_het_is_zo_belangrijk_want_we_denken_dat_iedereen_genoeg_te_eten_heeft_dat_is_gewoon_niet_zo = secrets.choice(
        boodschappen_lijstje)

    join_token = base64.b64encode(encrypt_join_token(
        want_het_is_zo_belangrijk_want_we_denken_dat_iedereen_genoeg_te_eten_heeft_dat_is_gewoon_niet_zo).encode()).decode()[32:38]

    join_token_exists = redis_client.exists(f"{redis_prefix}:join_token:{join_token}")

    while join_token_exists:
        join_token = base64.b64encode(encrypt_join_token(
            want_het_is_zo_belangrijk_want_we_denken_dat_iedereen_genoeg_te_eten_heeft_dat_is_gewoon_niet_zo).encode()).decode()[32:38]
        join_token_exists = redis_client.exists(f"{redis_prefix}:join_token:{join_token}")
    return join_token


boodschappen_lijstje = [
    "Groente of fruit in blik",
    "Broodbeleg",
    "Ontbijtkoek",
    "Couscous",
    "Zilvervlies of meergranen rijst",
    "Houdbare pasta",
    "Pastasaus",
    "Beschuit",
    "Smeerkaas",
    "Koffie en thee",
    "Chocoladerepen",
    "Maaltijdsoepen",
    "Mayonaise",
    "Mosterd",
    "Vruchtensap",
    "Toiletpapier",
    "Keukenrol"
]

game_modes = [
    "massive_multiplayer",
    "one_vs_one",
    "single_player",
    "custom"
]

config = json.loads(open("config/config.json").read())

redis_host = config["REDIS"]["HOST"]
redis_port = config["REDIS"]["PORT"]
redis_password = config["REDIS"]["PASSWORD"]
redis_db = config["REDIS"]["DB"]
redis_prefix = config["REDIS"]["PREFIX"]
redis_max_retries = config["REDIS"]["MAX_RETRIES"]
redis_retry_delay = config["REDIS"]["RETRY_DELAY"]
lock_timeout = config["REDIS"]["LOCK_TIMEOUT"]

redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    db=redis_db,
    password=redis_password,
    charset="utf-8",
    decode_responses=True,
    max_connections=100, # Match the thread count
    socket_keepalive=True
)
redlock = redlock.Redlock([{"host": redis_host, "port": redis_port, "db": 0, "password": redis_password}])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.propagate = False

file_handler = RotatingFileHandler("logs/error.log", maxBytes=5242880, backupCount=5)
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s [in %(pathname)s:%(lineno)d]"
))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))
logger.addHandler(console_handler)
