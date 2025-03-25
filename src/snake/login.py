import bcrypt
import main
import pymysql

config = main.config


def valid_password(email: str, password: str) -> dict:
    try:
        con = main.connect_to_db()
        cur = con.cursor()

        cur.execute("SELECT user_id, username, password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user:
            cur.close()
            con.close()
            return {
                "error": True,
                "message": "Gebruiker bestaat niet",
                "type": "email",
                "code": 400
            }

        user_id = user[0]
        username = user[1]
        hashed_password = user[2]

        cur.execute("SELECT highscore FROM snake_data WHERE user_id = %s", (user_id,))
        result = cur.fetchone()

        highscore = result[0]

        cur.close()
        con.close()

        if not bcrypt.checkpw(password.encode(), hashed_password):
            return {
                "error": True,
                "message": "Verkeerde wachtwoord",
                "type": "password",
                "code": 400
            }

        return {
            "error": False,
            "message": "Inloggen geslaagd!",
            "user_id": user_id,
            "username": username,
            "highscore": highscore,
            "code": 200
        }
    except Exception as e:
        print(e.with_traceback(None))
        print(e)

        return {
            "error": True,
            "message": "Er is een fout opgetreden",
            "type": "general",
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
