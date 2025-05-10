from src.snake.main import redis_client, redis_prefix
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename
from src.snake.app import app, send_file
from pymysql.cursors import DictCursor
from src.snake.wrapper_funcs import *
from flask import Blueprint
import base64
import json
import os
import io

games_bp = Blueprint("games", __name__, url_prefix="/api/games")


@games_bp.get("/<game_id>")
@login_required()
@wrap_errors()
@db_connection(DictCursor)
def game_data_get(con, cur, game_id):
    cur.execute("SELECT game_mode, winner, settings, food, started_at, ended_at FROM games_metadata WHERE game_id = %s", (game_id,))
    result = cur.fetchone()

    if not result:
        return jsonify({
            "error": True,
            "message": "Game bestaat niet",
            "type": "general",
            "category": "error"
        }), 404

    game_data = result
    for key in ["settings", "food"]:
        if result[key] and isinstance(result[key], str):
            game_data[key] = json.loads(result[key])

    cur.execute("SELECT user_id, player_data FROM player_games WHERE game_id = %s", (game_id,))
    players = cur.fetchall()

    game_data["players"] = {}
    for player in players:
        game_data["players"][player["user_id"]] = json.loads(player["player_data"])

    return jsonify({
        "error": False,
        "data": game_data
    })


@games_bp.get("/<game_id>/thumbnail")
def game_thumbnail_get(game_id):
    if not os.path.isfile(f"{app.static_folder}/game_thumbnails/{game_id}.png"):
        # Todo: Make default thumbnails(A.H)
        return send_file(f"{app.static_folder}/images/default_game_thumbnail.png"), 404

    return send_file(f"{app.static_folder}/game_thumbnails/{game_id}.png")


@games_bp.post("/<game_id>/upload_thumbnail")
@login_required()
@wrap_errors()
def upload_thumbnail(game_id):
    data = request.get_json()
    game_id = secure_filename(game_id)
    image_data = data.get("image", "")

    save_path = os.path.join(f"{app.static_folder}", "game_thumbnails", f"{game_id}.png")
    if os.path.exists(save_path):
        return jsonify({}), 400

    if not game_id or not image_data.startswith("data:image/png;base64,"):
        return jsonify({}), 400

    just_ended = redis_client.getex(f"{redis_prefix}:just_ended:{game_id}")
    if not just_ended:
        return jsonify({}), 400

    players = json.loads(just_ended)
    if session["user_id"] not in players:
        return jsonify({}), 400

    try:
        image_bytes = base64.b64decode(image_data.split(",")[1])
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except (UnidentifiedImageError, IndexError, ValueError):
        print("UnidentifiedImageError")
        return jsonify({}), 400

    MAX_FILE_SIZE = 50 * 1024
    if len(image_bytes) > MAX_FILE_SIZE:
        print("TOO MASSIVE")
        return jsonify({}), 400
    save_path = os.path.join(f"{app.static_folder}", "game_thumbnails", f"{game_id}.png")
    if not os.path.exists(save_path):
        with open(save_path, "xb") as f:
            f.write(image_bytes)

    return jsonify({
        "error": False
    })
