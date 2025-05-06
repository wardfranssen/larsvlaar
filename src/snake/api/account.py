from src.snake.app import limiter, get_user_or_session_key, app
from src.snake.main import config, redis_client, redis_prefix
from PIL import Image, UnidentifiedImageError
from src.snake.wrapper_funcs import *
# from opennsfw2 import predict_image
from src.snake.register import *
from flask import Blueprint
import bcrypt

account_bp = Blueprint("account", __name__, url_prefix="/api/account")


def validate_and_save_image(file_storage, save_path):
    try:
        image = Image.open(file_storage)

        if image.format.lower() not in config["ALLOWED_PFP_EXTENSIONS"]:
            return False
        image.verify()

        # Re-open to clean and convert
        file_storage.seek(0)  # Reset file pointer
        image = Image.open(file_storage).convert("RGB")

        # Todo: enable opennsfw2 in prod
        # nsfw_score = predict_image(image)
        #
        # if nsfw_score > config["MAX_NSFW_SCORE"]:
        #     return False

        resized_img = image.resize((256, 256))

        resized_img.save(save_path, format="PNG")
        return True
    except UnidentifiedImageError:
        return False


@account_bp.post("/password")
@limiter.limit("4 per 10 seconds", key_func=get_user_or_session_key)
@wrap_errors()
@db_connection()
def change_password_post(con, cur):
    request_json = request.get_json()

    password = request_json["new_password"]

    if not is_valid_password(password):
        return jsonify({
            "error": True,
            "message": "Wachtwoord is niet sterk genoeg",
            "type": "password",
        }), 400

    salt = bcrypt.gensalt(config["BCRYPT_SALT_STRENGTH"])
    hashed_password = bcrypt.hashpw(password.encode(), salt)

    cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, session["user_id"]))
    con.commit()

    return jsonify({
        "error": False,
        "message": "Wachtwoord succesvol aangepast",
        "type": "general",
        "category": "success"
    })


@account_bp.post("/username")
@login_required()
@wrap_errors()
@db_connection()
def change_username_post(con, cur):
    data = request.get_json()
    new_username = data["username"]
    user_id = session["user_id"]

    sanitized_username = sanitize_username(new_username)

    if not is_valid_username(sanitized_username):
        return jsonify({
            "error": True,
            "message": "Gebruikersnaam is te lang",
            "type": "username",
        }), 400

    cur.execute("UPDATE users SET username = %s WHERE user_id = %s", (sanitized_username, user_id))
    con.commit()

    session["username"] = sanitized_username
    redis_client.hset(f"{redis_prefix}:user:{user_id}", "username", sanitized_username)

    flash("Gebruikersnaam is aangepast", "success")
    return jsonify({
        "error": False,
        "reload": True
    })


@account_bp.post("/pfp")
@login_required()
@wrap_errors()
@db_connection()
def change_pfp_post(con, cur):
    # Todo: Add .gif support
    file = request.files["file"]
    user_id = session['user_id']

    if file.filename == '':
        return jsonify({
            "error": True,
            "message": "Geen foto",
            "type": "general",
            "category": "error"
        }), 400

    current_pfp_version = main.get_pfp_version(user_id)

    if file and file.filename.split(".")[-1].lower() in config["ALLOWED_PFP_EXTENSIONS"]:
        is_valid_img = validate_and_save_image(file, f"{app.static_folder}/pfp/{user_id}/{current_pfp_version+1}.png")
        if not is_valid_img:
            return jsonify({
                "error": True,
                "message": "Ongeldig of beschadigd bestand",
                "type": "general",
                "category": "error"
            }), 400

        cur.execute("UPDATE users SET pfp_version = pfp_version + 1 WHERE user_id = %s", (user_id,))
        con.commit()

        user = main.save_user_to_redis(user_id)
        session["pfp_version"] = user["pfp_version"]

        flash("Profielfoto veranderd", "success")
        return jsonify({
            "error": False,
            "reload": True
        })
    return jsonify({
        "error": True,
        "message": "Bestandstype wordt niet ondersteund",
        "type": "general",
        "category": "error"
    }), 400


@account_bp.post("/delete_account")
@login_required()
@wrap_errors()
def delete_account_post():
    # Todo: Actually remove the account

    session.clear()

    flash("Account succesvol verwijderd", "success")
    return jsonify({
        "error": False,
        "redirect": "/"
    })

