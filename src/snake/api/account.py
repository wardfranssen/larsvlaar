from src.snake.app import limiter, get_user_or_session_key, app
from PIL import Image, UnidentifiedImageError
from src.snake.register import *
from flask import Blueprint
import bcrypt

if config["18+_RESTRICTION"]:
    from opennsfw2 import predict_image


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

        if config["18+_RESTRICTION"]:
            nsfw_score = predict_image(image)

            if nsfw_score > config["MAX_NSFW_SCORE"]:
                return False

        resized_img = image.resize((256, 256))

        resized_img.save(save_path, format="PNG")
        return True
    except UnidentifiedImageError:
        return False


@account_bp.put("/<item_type>/select")
@login_required()
@wrap_errors()
@db_connection()
def select_item(con, cur, item_type):
    user_id = session["user_id"]

    request_json = request.get_json()
    item = request_json[item_type]

    if item_type not in ["skin", "background", "food_skin"]:
        return jsonify({
            "error": True,
            "message": "Item categorie bestaat niet",
            "type": "general",
            "category": "error"
        }), 404

    if item == session.get(item_type):
        return jsonify({
            "error": True,
            "message": "Item is al geselecteerd",
            "type": "general",
            "category": "error"
        }), 400

    cur.execute("SELECT path FROM items WHERE item_id = %s AND type = %s LIMIT 1", (item, item_type))
    result = cur.fetchone()
    if not result:
        return jsonify({
            "error": True,
            "message": "Item bestaat niet",
            "type": "general",
            "category": "error"
        }), 404

    cur.execute(f"UPDATE users SET {item_type} = %s WHERE user_id = %s", (item , user_id))

    item_data = {
        "item_id": item,
        "path": result[0]
    }

    session[item_type] = item_data
    redis_client.hset(f"{redis_prefix}:user:{user_id}", item_type, json.dumps(item_data))

    return jsonify({
        "error": False,
        "path": result[0]
    })


@account_bp.get("/items")
@login_required()
@wrap_errors()
@db_connection()
def get_unlocked_items(con, cur):
    user_id = session["user_id"]

    cur.execute("""
    SELECT 
        ui.item_id, 
        i.name,
        i.type,
        i.path,
        i.price
    FROM 
        user_items ui
    INNER JOIN 
        items i ON ui.item_id = i.item_id
    WHERE 
        ui.user_id = %s;
    """, (user_id,))
    results = cur.fetchall()

    unlocked_items = []
    for result in results:
        unlocked_items.append({
            "item_id": result[0],
            "name": result[1],
            "type": result[2],
            "path": result[3],
            "price": result[4],
        })

    cur.execute("SELECT skin, background, food_skin FROM users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()

    return jsonify({
        "error": False,
        "unlocked_items": unlocked_items,
        "selected_items": {
            "skin": result[0],
            "background": result[1],
            "food_skin": result[2]
        }
    })


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
    # Todo: Add gif support
    file = request.files["file"]
    user_id = session['user_id']

    if file.filename == '':
        return jsonify({
            "error": True,
            "message": "Geen foto",
            "type": "general",
            "category": "error"
        }), 400

    current_pfp_version = main.get_user_info("pfp_version", user_id)

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

