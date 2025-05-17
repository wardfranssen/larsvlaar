from src.snake.app import limiter, get_user_or_session_key, app
from src.snake.register import *
from src.snake import send_email
from src.snake.login import *
from src.snake.mfa import *
from flask import Blueprint
from uuid import uuid4
import bcrypt
import random

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
redis_client = main.redis_client


@auth_bp.post("/register")
@limiter.limit("10 per 10 minute", key_func=get_user_or_session_key)
@limiter.limit("5 per 1 minute", key_func=get_user_or_session_key)
@limiter.limit("3 per 10 seconds", key_func=get_user_or_session_key)
@wrap_errors()
def register_post():
    data = request.get_json()

    username = data["username"]
    email = data["email"]
    password = data["password"]

    sanitized_username = sanitize_username(username)

    # Validate user input
    if not is_valid_username(sanitized_username):
        return jsonify({
            "error": True,
            "message": "Gebruikersnaam is te lang",
            "type": "username",
        }), 400
    valid_email = is_valid_email(email)
    if valid_email["error"]:
        return jsonify({
            "error": True,
            "message": valid_email["message"],
            "type": valid_email["type"],
        }), valid_email["code"]
    if not is_valid_password(password):
        return jsonify({
            "error": True,
            "message": "Wachtwoord is niet sterk genoeg",
            "type": "password",
        }), 400

    # Generate user id
    user_id = str(uuid4())

    # Hash password
    salt = bcrypt.gensalt(config["BCRYPT_SALT_STRENGTH"])
    hashed_password = bcrypt.hashpw(password.encode(), salt)

    # Save data
    session["hashed_password"] = hashed_password
    session["user_id"] = user_id
    session["username"] = sanitized_username
    session["email"] = email
    session["state"] = "registering"

    # Generate and send mfa code
    verification_code = generate_code(user_id, email)
    send_email.register_verify_email(verification_code, sanitized_username, email)

    return jsonify({
        "error": False,
        "redirect": "/verify"
    })


@auth_bp.post("/login")
@limiter.limit("10 per 1 minute", key_func=get_user_or_session_key)
@limiter.limit("3 per 10 seconds", key_func=get_user_or_session_key)
@wrap_errors()
def login_post():
    data = request.get_json()

    email = data["email"]
    password = data["password"]

    result = valid_password(email, password)

    if result["error"]:
        return jsonify({
            "error": True,
            "message": result["message"],
            "type": result["type"],
            "category": result["category"]
        }), result["code"]

    user_id = result["user_id"]
    username = result["username"]
    role = result["role"]

    session["email"] = email
    session["user_id"] = user_id
    session["username"] = username
    session["pfp_version"] = result["pfp_version"]
    session["state"] = "logging_in"
    session["role"] = role
    session["is_admin"] = role == "admin"

    session["background"] = result["background"]

    # Generate and send mfa code
    verification_code = generate_code(user_id, email)
    send_email.login_verification_email(verification_code, username, email)

    return jsonify({
        "error": False,
        "redirect": "/verify"
    })


@auth_bp.post("/verify")
@limiter.limit("10 per 1 minute", key_func=get_user_or_session_key)
@limiter.limit("3 per 10 seconds", key_func=get_user_or_session_key)
@wrap_errors()
def verify_post():
    request_json = request.get_json()
    user_id = session["user_id"]

    is_valid = is_valid_code(user_id, request_json["code"], session["email"])

    if is_valid["id_valid"]:
        if session["state"] == "registering":
            hashed_password = base64.b64decode(session["hashed_password"])

            # Insert into db
            result = create_account(user_id, session["username"], session["email"], hashed_password)
            response_code = result["code"]

            if response_code == 201:
                session["user_id"] = result["user_id"]
                session["pfp_version"] = 0
                session["background"] = result["background"]

                role = result["role"]

                session["role"] = role
                session["is_admin"] = role == "admin"

                random_pfp = random.choice(os.listdir(f"{app.static_folder}/pfp/default"))

                if not os.path.isdir(f"{app.static_folder}/pfp/{user_id}"):
                    os.mkdir(f"{app.static_folder}/pfp/{user_id}")
                with open(f"{app.static_folder}/pfp/{user_id}/0.png", "wb") as file:
                    file.write(open(f"{app.static_folder}/pfp/default/{random_pfp}", "rb").read())
                    file.close()

                flash('Account aangemaakt!', 'success')
            else:
                return jsonify({
                    "error": True,
                    "message": result["message"],
                    "type": result["type"],
                    "category": result["category"]
                }), response_code

            session.pop("hashed_password", None)
        elif session["state"] == "logging_in":
            flash('Inloggen geslaagd!', 'success')
            response_code = 200
        elif session["state"] == "logged_in":
            return jsonify({
                "error": True,
                "category": "error",
                "type": "general",
                "message": "Je bent al ingelogd",
            }), 400
        else:
            return jsonify({
                "error": True,
                "category": "error",
                "type": "general",
                "message": "Ongeldige sessie status",
            }), 400

        session["logged_in"] = True
        session["state"] = "logged_in"

        # Remove currently logged-in sessions
        logged_in_sessions = redis_client.smembers(f"{redis_prefix}:user_session:{user_id}")
        for logged_in_session in logged_in_sessions:
            redis_client.delete(f"{redis_prefix}:session:{logged_in_session}")

        redis_client.sadd(f"{redis_prefix}:user_session:{user_id}", session.sid)

        return jsonify({
            "error": False,
            "redirect": "/snake",
            "username": session["username"],
            "user_id": user_id
        }), response_code
    else:
        if is_valid["message"] == "Code expired":
            # Send new mfa code
            verification_code = generate_code(user_id, session["email"])
            send_email.login_verification_email(verification_code, session["username"], session["email"])

            return jsonify({
                "error": True,
                "message": "Code is verlopen, dus er is een nieuwe naar je verstuurd",
                "category": "success",
                "type": "general",
            }), 400

        return jsonify({
            "error": True,
            "message": is_valid["message"],
            "type": "code",
        }), 400


@auth_bp.post("/request_password_change")
@limiter.limit("10 per 10 minute", key_func=get_user_or_session_key)
@limiter.limit("3 per 10 seconds", key_func=get_user_or_session_key)
@wrap_errors()
@db_connection()
def request_password_change_post(con, cur):
    email = request.get_json()["email"]

    token = str(uuid4().hex)

    salt = bcrypt.gensalt(config["BCRYPT_SALT_STRENGTH"])
    hashed_token = bcrypt.hashpw(token.encode(), salt)

    time_created = int(time.time())

    # Check if email exists and fetch user_id
    cur.execute("SELECT user_id, username FROM users WHERE email = %s", (email))

    result = cur.fetchone()
    if not result:
        return jsonify({
            "error": True,
            "message": "Geen account met dat email",
            "type": "email"
        }), 400

    user_id = result[0]
    username = result[1]

    cur.execute("DELETE FROM change_password WHERE user_id = %s", (user_id))

    cur.execute("INSERT INTO change_password VALUES (%s, %s, %s)", (user_id, hashed_token, time_created))

    send_email.change_password(user_id, token, username, email)
    return jsonify({
        "error": False,
        "message": "Email verstuurd",
        "type": "general",
        "category": "success"
    }), 200


@auth_bp.post("/change_password")
@limiter.limit("3 per 10 seconds", key_func=get_user_or_session_key)
@wrap_errors()
@db_connection()
def change_password_post(con, cur):
    request_json = request.get_json()

    user_id = request_json["user_id"]
    token = request_json["token"]
    password = request_json["password"]

    if not is_valid_password(password):
        return jsonify({
            "error": True,
            "message": "Wachtwoord is niet sterk genoeg",
            "type": "password",
        }), 400

    cur.execute("SELECT token, created_at FROM change_password WHERE user_id = %s", (user_id))
    result = cur.fetchone()

    if not result:
        return jsonify({
            "error": True,
            "message": "Gebruiker heeft geen wachtwoord wijziging aangevraagd",
            "type": "general",
            "category": "error"
        }), 400

    hashed_token = result[0]
    exp = result[1]

    if not bcrypt.checkpw(token.encode(), hashed_token):
        return jsonify({
            "error": True,
            "message": "Ongeldige token",
            "type": "general",
            "category": "error"
        }), 400

    if int(time.time()) > exp + config["CHANGE_PASSWORD_EXP"]:
        return jsonify({
            "error": True,
            "message": "Wachtwoord wijzigen verlopen",
            "type": "general",
            "category": "error"
        }), 410

    salt = bcrypt.gensalt(config["BCRYPT_SALT_STRENGTH"])
    hashed_password = bcrypt.hashpw(password.encode(), salt)

    cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, user_id))

    logged_in_sessions = redis_client.smembers(f"{redis_prefix}:user_session:{user_id}")
    for logged_in_session in logged_in_sessions:
        redis_client.delete(f"{redis_prefix}:session:{logged_in_session}")

    flash("Wachtwoord gewijzigd", "success")
    return jsonify({
        "error": False,
        "redirect": "/login"
    })


@auth_bp.get("/resend_email")
@limiter.limit("2 per 1 minute", key_func=get_user_or_session_key)
@limiter.limit("1 per 20 seconds", key_func=get_user_or_session_key)
def resend_email():
    try:
        if session["state"] == "logged_in":
            flash("Je bent al ingelogd", "success")
            return redirect("/")

        encrypted_code = redis_client.get(f"{redis_prefix}:mfa:{session['user_id']}")

        if not encrypted_code:
            verification_code = generate_code(session["user_id"], session["email"])
        else:
            verification_code = decrypt_mfa_code(encrypted_code, session["email"])

        if session["state"] == "registering":
            send_email.register_verify_email(verification_code, session["username"], session["email"])
        elif session["state"] == "logging_in":
            send_email.login_verification_email(verification_code, session["username"], session["email"])
        else:
            flash("Ongeldige sessie status", "error")
            return redirect("/")

        flash("Verificatie code verstuurd", "success")
        return redirect("/verify")
    except Exception as e:
        logger.error(f"resend: {e}", exc_info=True)
        flash("Er is een probleem opgetreden tijdens het versturen", "error")
        return redirect("/verify")


@auth_bp.route("/logout", methods=["GET", "POST"])
@wrap_errors()
def log_out():
    user_id = session['user_id']
    redis_client.delete(f"{redis_prefix}:session:{session.sid}")
    redis_client.delete(f"{redis_prefix}:user:{user_id}")
    redis_client.delete(f"{redis_prefix}:online:{user_id}")
    session.clear()

    if request.method == "GET":
        return redirect("/")
    return jsonify({
        "error": False,
        "redirect": "/"
    })

