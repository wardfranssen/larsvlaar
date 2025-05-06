from src.snake.wrapper_funcs import *
import src.snake.main as main
import bcrypt
import pymysql

config = main.config


@db_connection()
def valid_password(con, cur, email: str, password: str) -> dict:
    try:
        cur.execute("SELECT user_id, username, password, pfp_version FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user:
            return {
                "error": True,
                "message": "Gebruiker bestaat niet",
                "type": "email",
                "category": "",
                "code": 400
            }

        user_id = user[0]
        username = user[1]
        hashed_password = user[2]
        pfp_version = user[3]

        if not bcrypt.checkpw(password.encode(), hashed_password):
            return {
                "error": True,
                "message": "Onjuist wachtwoord",
                "type": "password",
                "category": "",
                "code": 400
            }
        return {
            "error": False,
            "message": "Inloggen geslaagd!",
            "user_id": user_id,
            "username": username,
            "pfp_version": pfp_version,
            "code": 200
        }
    except Exception as e:
        print(e.with_traceback(None))
        print(e)

        return {
            "error": True,
            "message": "Er is een fout opgetreden",
            "type": "general",
            "category": "error",
            "code": 500
        }
