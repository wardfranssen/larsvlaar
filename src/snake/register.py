import time
import uuid
import main
import re
import pymysql

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


def is_valid_email(email: str) -> dict:
    try:
        pattern = r'^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
        if not re.match(pattern, email):
            return {
                "error": True,
                "message": "Ongeldig e-mailadres",
                "type": "email",
                "code": 400
            }

        con = main.connect_to_db()
        cur = con.cursor()

        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        result = cur.fetchone()

        cur.close()
        con.close()

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
    finally:
        try:
            if cur:
                cur.close()
            if con:
                con.close()
        except pymysql.err.Error:
            pass


def is_valid_username(username: str) -> bool:
    if len(username) > 20:
        return False

    # pattern = r'^[a-zA-Z0-9 _]+$'
    # if not re.match(pattern, username):
    #     return False

    return True


def create_account(user_id: str, username: str, email: str, hashed_password: bytes) -> dict:
    try:
        created_at = time.time()
        updated_at = created_at

        con = main.connect_to_db()
        cur = con.cursor()

        cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()

        if result:
            user_id = str(uuid.uuid4())

        try:
            cur.execute("INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s)",
                           (user_id, username, hashed_password, email, created_at, updated_at,))

            cur.execute("INSERT INTO snake_data VALUES (%s, %s, %s, %s)",
                           (user_id, 0, 0, 0))
            con.commit()

        except pymysql.err.IntegrityError:
            return {
                "error": True,
                "message": "E-mailadres is al in gebruik",
                "type": "general",
                "category": "error",
                "code": 400
            }
        finally:
            try:
                if cur:
                    cur.close()
                if con:
                    con.close()
            except pymysql.err.Error:
                pass

        return {
            "error": False,
            "message": "Account aangemaakt!",
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
    finally:
        try:
            if cur:
                cur.close()
            if con:
                con.close()
        except pymysql.err.Error:
            pass
