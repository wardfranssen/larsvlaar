from src.snake.app import food_skins
from src.snake.wrapper_funcs import *
import src.snake.main as main
import pymysql
import bleach
import uuid
import time
import re

config = main.config


def is_valid_password(password: str) -> bool:
    if len(password) < 8:
        return False

    if not re.search(r'[A-Z]', password):
        return False

    if not re.search(r'[a-z]', password):
        return False

    if not re.search(r'\d', password):
        return False

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False

    return True


@db_connection()
def is_valid_email(con, cur, email: str) -> dict:
    pattern = r'^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    if not re.match(pattern, email):
        return {
            "error": True,
            "message": "Ongeldig e-mailadres",
            "type": "email",
            "code": 400
        }

    if email in list(config["BANNED_EMAILS"].keys()):
        return {
            "error": True,
            "message": config["BANNED_EMAILS"][email],
            "type": "general",
            "code": 400
        }

    cur.execute("SELECT 1 FROM users WHERE email = %s LIMIT 1", (email,))
    result = cur.fetchone()

    if result:
        return {
            "error": True,
            "message": "E-mailadres is al in gebruik",
            "type": "email",
            "code": 400
        }

    return {
        "error": False
    }


def sanitize_username(username: str):
    allowed_tags = {"i", "small", "b", "u", "strong", "em", "abbr"}

    sanitized_username = bleach.clean(username.strip(), tags=allowed_tags, strip=True)

    # Todo: Add something special for special emails
    return sanitized_username


def is_valid_username(username: str) -> bool:
    if len(username) > config["MAX_USERNAME_LEN"]:
        return False
    return True


@db_connection()
def create_account(con, cur, user_id: str, username: str, email: str, hashed_password: bytes) -> dict:
    try:
        created_at = int(time.time())
        updated_at = created_at
        role = "npc"

        skin = "e479fb65-c1b5-41b4-afa1-159690560f0f"
        background = "e4bc9687-c067-4c67-a9cf-c02f14ffa519"
        food_skin = "4697bfd7-a513-42e0-a629-2dbb40w64876"

        for i in range(5):
            cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            result = cur.fetchone()

            if result:
                user_id = str(uuid.uuid4())
            else:
                break
        try:
            cur.execute("INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (user_id, username, hashed_password, email, skin, background, food_skin, 0, 0, role, created_at, updated_at))

            cur.execute("INSERT INTO user_stats_one_vs_one VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (user_id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

            cur.execute("INSERT INTO user_stats_custom VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (user_id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

            cur.execute("INSERT INTO user_stats_single_player VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (user_id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

            cur.execute("INSERT INTO user_stats_massive_multiplayer VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (user_id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

            items = [
                (user_id, skin, "skin", created_at),
                (user_id, background, "background", created_at),
                (user_id, food_skin, "food_skin", created_at)
            ]
            cur.executemany("""
                INSERT INTO user_items (user_id, item_id, type, unlocked_at) 
                VALUES (%s, %s, %s, %s)
            """, items)
        except pymysql.err.IntegrityError:
            return {
                "error": True,
                "message": "E-mailadres is al in gebruik",
                "type": "general",
                "category": "error",
                "code": 400
            }

        cur.execute("SELECT item_id, path FROM items WHERE item_id = %s OR item_id = %s OR item_id = %s", (skin, background, food_skin))
        result = cur.fetchall()

        skin_data = {
            "item_id": skin,
            "path": result[0][1]
        }

        background_data = {
            "item_id": skin,
            "path": result[1][1]
        }

        food_skin_data = {
            "item_id": skin,
            "path": result[2][1]
        }

        return {
            "error": False,
            "message": "Account aangemaakt!",
            "user_id": user_id,
            "role": role,
            "skin": skin_data,
            "background": background_data,
            "food_skin": food_skin_data,
            "code": 201
        }
    except Exception as e:
        print(e)
        return {
            "error": True,
            "message": "Er is een probleem opgetreden tijdens het aanmaken van je account",
            "type": "general",
            "category": "error",
            "code": 500
        }
