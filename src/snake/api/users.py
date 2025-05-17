from src.snake.app import app, send_file, socketio
from pymysql.cursors import DictCursor
from src.snake.wrapper_funcs import *
from src.snake.main import *
from flask import Blueprint
from uuid import uuid4
import json
import os

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.get("/")
@login_required()
@wrap_errors()
@db_connection(DictCursor)
def users_get(con, cur):
    query = request.args["query"].strip()
    limit = int(request.args["limit"])
    friendship_status = request.args["friendship_status"]
    user_id = session["user_id"]

    limit = min(limit, 15)

    if friendship_status == "true":
        cur.execute("""
            SELECT u.user_id, u.username, u.pfp_version,
               CASE
                   WHEN f.user1_id IS NOT NULL OR f.user2_id IS NOT NULL THEN 'friend'
                   WHEN fr.from_user_id IS NOT NULL AND fr.to_user_id = %s THEN 'request_received'
                   WHEN fr.to_user_id IS NOT NULL AND fr.from_user_id = %s THEN 'request_sent'
                   ELSE 'none'
               END AS friend_request_status
            FROM users u
            LEFT JOIN friends f ON
                (f.user1_id = u.user_id AND f.user2_id = %s)
                OR (f.user2_id = u.user_id AND f.user1_id = %s)
            LEFT JOIN friend_requests fr ON
                (fr.from_user_id = u.user_id AND fr.to_user_id = %s)
                OR (fr.to_user_id = u.user_id AND fr.from_user_id = %s)
            WHERE LOWER(u.username) LIKE %s
            AND u.user_id != %s
            ORDER BY u.username
            
            LIMIT %s
        """, (user_id, user_id, user_id, user_id, user_id, user_id, f"{query.lower()}%", user_id, limit))

    else:
        cur.execute("""
        SELECT user_id, username, pfp_version
        FROM users
        WHERE LOWER(username) LIKE %s
        AND user_id != %s
        ORDER BY username

        LIMIT %s
        """, (f"{query.lower()}%", user_id, limit))

    users = cur.fetchall()
    for i in range(len(users)):
        user_id = users[i]["user_id"]
        users[i]["status"] = get_status(user_id)

    return jsonify({
        "error": False,
        "users": users
    })

@users_bp.get("/<user_id>/pfp")
@users_bp.get("/<user_id>/pfp/<pfp_version>")
def get_pfp_fallback(user_id, pfp_version=None):
    pfp_version = request.args.get("v", 0)

    if not os.path.isfile(f"{app.static_folder}/pfp/{user_id}/{pfp_version}.png"):
        return send_file(f"{app.static_folder}/pfp/default.png"), 404

    return send_file(f"{app.static_folder}/pfp/{user_id}/{pfp_version}.png")


@users_bp.get("/<user_id>/items")
@login_required()
@wrap_errors()
@db_connection()
def user_items_get(con, cur, user_id: str):
    cur.execute(f"SELECT item_id FROM user_items WHERE user_id = %s ORDER BY unlocked_at desc", (user_id,))
    items = cur.fetchall()

    user_items = []
    for item in items:
        user_items.append(item[0])

    return {
        "error": False,
        "items": user_items
    }


@users_bp.get("/<user_id>/games_history")
@login_required()
@wrap_errors()
@db_connection(pymysql.cursors.DictCursor)
def games_history_get(con, cur, user_id: str):
    limit = 1000
    cur.execute(f"SELECT game_id FROM player_games WHERE user_id = %s ORDER BY ended_at desc LIMIT {limit}", (user_id,))
    games = cur.fetchall()

    if not games:
        return jsonify({
            "error": True,
            "message": "Geen games gevonden",
            "type": "general",
            "category": "error"
        }), 404

    games_data = {}
    for game in games:
        game_id = game["game_id"]
        cur.execute("SELECT game_mode, winner, started_at, ended_at FROM games_metadata WHERE game_id = %s", (game_id,))
        game_data = cur.fetchone()

        cur.execute("SELECT user_id, player_data FROM player_games WHERE game_id = %s", (game_id,))
        players = cur.fetchall()

        game_data["score"] = None
        game_data["players"] = {}
        for player in players:
            player_id = player["user_id"]
            game_data["players"][player_id] = {
                "username": get_user_info("username", player_id)
            }

            if player_id == user_id:
                game_data["score"] = json.loads(player["player_data"])["score"]

        games_data[game_id] = {
            "game_mode": game_data["game_mode"],
            "winner": {
                "user_id": game_data["winner"],
                "username": get_user_info("username", game_data["winner"])
            },
            "score": game_data["score"],
            "players": game_data["players"],
            "started_at": game_data["started_at"],
            "ended_at": game_data["ended_at"]
        }
    return jsonify({
        "error": False,
        "data": games_data
    })


@users_bp.post("/<to_user_id>/invite")
@login_required()
@wrap_errors()
def invite_post(to_user_id: str):
    from_user_id = session["user_id"]
    game_mode = request.json["game_mode"]
    lobby_id = request.json.get("lobby_id")

    invite = redis_client.exists(f"{redis_prefix}:invite:{from_user_id}:{to_user_id}")
    if invite:
        return jsonify({
            "error": True,
            "message": "Je hebt al een uitnodiging gestuurd naar deze speler",
            "type": "general",
            "category": "error"
        }), 400
    if lobby_id:
        lobby = redis_client.get(f"{redis_prefix}:lobbies:{lobby_id}")
        if not lobby:
            return jsonify({
                "error": True,
                "message": "Lobby bestaat niet",
                "type": "general",
                "category": "error"
            }), 404
        lobby = json.loads(lobby)
        if from_user_id != lobby["owner"]:
            return jsonify({
                "error": True,
                "message": "Niet genoeg rechten om mensen uit te nodigen",
                "type": "general",
                "category": "error"
            }), 403

    invite_id = str(uuid4())
    created_at = int(time.time())

    invite_data = {
        "from": from_user_id,
        "to": to_user_id,
        "game_mode": game_mode,
        "lobby_id": lobby_id,
        "created_at": created_at,
    }

    redis_client.setex(f"{redis_prefix}:invite:{from_user_id}:{to_user_id}", 20, 1)

    redis_client.sadd(f"{redis_prefix}:user:{from_user_id}:invites:sent", invite_id)
    redis_client.expire(f"{redis_prefix}:user:{from_user_id}:invites:sent", 20)

    redis_client.sadd(f"{redis_prefix}:user:{to_user_id}:invites:received", invite_id)
    redis_client.expire(f"{redis_prefix}:user:{to_user_id}:invites:received", 20)

    redis_client.setex(
        f"{redis_prefix}:invite:{invite_id}",
        20,
        json.dumps(invite_data)
    )

    from_username = get_user_info("username", from_user_id)
    from_pfp_version = get_user_info("pfp_version", from_user_id)

    data = {
        "invite_id": invite_id,
        "user_id": from_user_id,
        "username": from_username,
        "pfp_version": from_pfp_version,
        "lobby_id": lobby_id,
        "game_mode": game_mode,
        "created_at": created_at,
        "server_time": int(time.time())
    }
    socketio.emit("received_invite", data, room=f"notifications:{to_user_id}", namespace="/ws/notifications")

    username = get_user_info("username", to_user_id)
    pfp_version = get_user_info("pfp_version", to_user_id)

    data = {
        "user_id": to_user_id,
        "username": username,
        "pfp_version": pfp_version,
        "invite_id": invite_id
    }
    return jsonify({
        "error": False,
        "data": data
    }), 201
