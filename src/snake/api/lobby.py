from src.snake.main import redis_client, redis_prefix, get_lock, redlock
from flask_socketio import emit, join_room, Namespace, leave_room
from src.snake.wrapper_funcs import *
from src.snake.app import socketio
from src.snake.game import generate_snake_spawns
from flask import Blueprint
from copy import deepcopy
from uuid import uuid4
import json
import time

lobby_bp = Blueprint("lobby", __name__, url_prefix="/api/lobby")

default_lobby_state = {
    "players": {},  # {player_id: {snake_pos: [], ready: False, score: int}}
    "allowed_to_join": [],
    "settings": {
        "update_interval": 0.300,  # Interval between updates in seconds
        "board": {
            "rows": 15,
            "cols": 15,
        },
        "spawn_len": 4,
        "grow": 1
    },
    "join_token": "",
    "chat_id": ""
}

default_custom_game_state = {
    "food_pos": [],  # List of food x and y
    "food_positions": [],  # Nested list of food x and y positions
    "started_at": 0,  # At what unix timestamp the game started
    "winner": None,  # Uuid of winner, None if draw
    "started": False,
    "ended": False,
    "owner": "",
    "players": {},
    "settings": {
        "update_interval": 0.300,  # Interval between updates in seconds
        "board": {
            "rows": 15,
            "cols": 15,
        },
        "spawn_len": 4,
        "grow": 1
    },
    "leaderboard": {},
    "chat_id": ""
}


def get_lobby(lobby_id: str) -> tuple | None:
    lock = get_lock(f"{redis_prefix}:lock:lobby:{lobby_id}")
    if not lock:
        return None

    lobby = redis_client.get(f"{redis_prefix}:lobbies:{lobby_id}")
    if not lobby:
        return None
    lobby = json.loads(lobby)
    return lobby, lock


@lobby_bp.post("/<join_token>/join")
@login_required()
@wrap_errors()
def join_lobby(join_token: str):
    lobby_id = redis_client.get(f"{redis_prefix}:join_token:{join_token}")
    if not lobby_id:
        return jsonify({
            "error": True,
            "message": "Lobby bestaat niet",
            "type": "join-token"
        }), 404

    lobby_lock = get_lobby(lobby_id)
    if not lobby_lock:
        return jsonify({
            "error": True,
            "message": "Lobby bestaat niet",
            "type": "join-token"
        }), 404
    lobby, lock = lobby_lock
    try:
        lobby["allowed_to_join"].append(session["user_id"])
        redis_client.set(f"{redis_prefix}:lobbies:{lobby_id}", json.dumps(lobby), ex=15)
    finally:
        try:
            redlock.unlock(lock)
        except Exception as e:
            logger.warning(f"Failed to unlock {lock.resource}: {e}")

    return jsonify({
        "error": False,
        "redirect": f"/lobby/{lobby_id}"
    })



@lobby_bp.post("/<lobby_id>")
@login_required()
@wrap_errors()
def create_game(lobby_id: str):
    lobby = redis_client.get(f"{redis_prefix}:lobbies:{lobby_id}")
    if not lobby:
        return jsonify({
            "error": True,
            "message": "Lobby bestaat niet",
            "type": "general",
            "category": "error"
        }), 404
    lobby = json.loads(lobby)

    if session["user_id"] != lobby["owner"]:
        return jsonify({
            "error": True,
            "message": "Niet genoeg rechten om de game te starten",
            "type": "general",
            "category": "error"
        }), 403

    settings = lobby["settings"]

    rows = int(settings["board"]["rows"])
    cols = int(settings["board"]["cols"])
    update_interval = max(float(settings["update_interval"]), 0.050)
    spawn_len = max(int(settings["spawn_len"]), 1)
    grow = max(int(settings["grow"]), 1)
    food_amount = max(int(settings["food_amount"]), 1)

    if rows > 75:
        rows = 75
    elif rows < 10:
        rows = 10

    if cols > 75:
        cols = 75
    elif cols < 10:
        cols = 10

    players = lobby["players"]

    spawns = generate_snake_spawns(len(players.keys()), cols, rows, spawn_len)

    if spawns["error"]:
        return jsonify({
            "error": True,
            "message": spawns["message"],
            "type": "general",
            "category": "error"
        }), 400

    spawns = spawns["spawns"]

    for i, player_id in enumerate(players):
        snake_spawn = spawns[i]
        body = list(reversed(snake_spawn["body"]))
        players[player_id].update({
            "snake_pos": body,
            "prev_snake_pos": [],
            "current_snake_dir": snake_spawn["direction"],
            "moves_this_update": [snake_spawn["direction"]],
            "moves": [],
            "score": 0,
            "spawn_pos": body,
            "connected": False,
            "rematch": None,
            "alive": True,
            "cause_of_death": None,
            "kills": []
        })

    game_id = str(uuid4())

    game_state = deepcopy(default_custom_game_state)
    game_state.update({
        "owner": session["user_id"],
        "created_at": int(time.time()),
        "players":  players,
        "settings": {
            "update_interval": update_interval,
            "board": {
                "rows": rows,
                "cols": cols,
            },
            "spawn_len": spawn_len,
            "grow": grow,
            "food_amount": food_amount
        },
        "chat_id": lobby["chat_id"]
    })

    redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))

    redis_client.delete(f"{redis_prefix}:lobbies:{lobby_id}")
    redis_client.delete(f"{redis_prefix}:join_token:{lobby["join_token"]}")

    redirect_url = f"/snake/custom?game_id={game_id}"

    socketio.emit("game_start", {"redirect_url": redirect_url}, room=f"lobby:{lobby_id}", namespace="/ws/lobby")
    return jsonify({
        "error": False,
        "redirect": redirect_url
    })



@lobby_bp.delete("/<lobby_id>/players/<to_kick_user_id>")
@login_required()
@wrap_errors()
def kick_from_lobby(lobby_id: str, to_kick_user_id: str):
    user_id = session["user_id"]

    if user_id == to_kick_user_id:
        return jsonify({
            "error": True,
            "message": "Je kan jezelf niet kicken",
            "type": "general",
            "category": "error"
        }), 400

    lobby_lock = get_lobby(lobby_id)
    if not lobby_lock:
        return jsonify({
            "error": True,
            "message": "Lobby bestaat niet of is verlopen",
            "type": "general",
            "category": "error"
        }), 404
    lobby, lock = lobby_lock
    try:
        if user_id != lobby["owner"]:
            return jsonify({
                "error": True,
                "message": "Niet genoeg rechten om mensen te kicken",
                "type": "general",
                "category": "error"
            }), 403

        del lobby["players"][to_kick_user_id]
        lobby["allowed_to_join"].remove(to_kick_user_id)

        redis_client.set(f"{redis_prefix}:lobbies:{lobby_id}", json.dumps(lobby), ex=15)

        message = {
            "message": "Je bent gekicked",
            "category": "error"
        }
        redis_client.rpush(f"{redis_prefix}:user:{to_kick_user_id}:general_messages", json.dumps(message))
    finally:
        try:
            redlock.unlock(lock)
        except Exception as e:
            logger.warning(f"Failed to unlock {lock.resource}: {e}")

    socketio.emit("player_update", lobby["players"], room=f"lobby:{lobby_id}", namespace="/ws/lobby")

    return jsonify({
        "error": False,
        "message": f"{main.get_username(to_kick_user_id)} is gekicked",
        "type": "general",
        "category": "success"
    })


class LobbyNamespace(Namespace):
    @login_required()
    def on_connect(self):
        lobby_id = request.args.get("lobby_id")
        user_id = session["user_id"]

        lobby_lock = get_lobby(lobby_id)
        if not lobby_lock:
            flash("Lobby bestaat niet of is verlopen", "error")
            emit("leave_lobby")
            return
        lobby, lock = lobby_lock
        try:
            # Check if user is allowed to join
            if user_id not in lobby["allowed_to_join"]:
                flash("Je hebt geen toestemming om deze lobby te joinen", "error")
                emit("leave_lobby")
                return

            is_owner = lobby["owner"] == user_id

            lobby["players"][user_id] = {
                "username": session["username"],
                "pfp_version": session["pfp_version"],
                "owner": is_owner
            }
            exp_at = redis_client.expiretime(f"{redis_prefix}:lobbies:{lobby_id}")
            redis_client.set(f"{redis_prefix}:lobbies:{lobby_id}", json.dumps(lobby), ex=exp_at - int(time.time().__floor__()))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")

        if user_id == lobby["owner"]:
            emit("owner_status")

            join_token = lobby["join_token"]

            redis_client.hset(f"{redis_prefix}:lobby_owners:connected", user_id, 1)
            socketio.start_background_task(self.heartbeat, user_id, lobby_id, join_token)

        join_room(f"lobby:{lobby_id}")

        # Tell connected clients that a person joined
        socketio.emit(f"player_update", lobby["players"], room=f"lobby:{lobby_id}", namespace="/ws/lobby")
        emit("settings_update", lobby["settings"], room=f"lobby:{lobby_id}", namespace="/ws/lobby")


    def on_settings_update(self, settings):
        lobby_id = request.args.get("lobby_id")

        lobby_lock = get_lobby(lobby_id)
        if not lobby_lock:
            print("Lobby doesn't exist")
            flash("Lobby bestaat niet of is verlopen", "error")
            emit("leave_lobby")
            return
        lobby, lock = lobby_lock
        try:
            if session["user_id"] != lobby["owner"]:
                emit("not_allowed")
                return

            lobby["settings"].update(settings)
            redis_client.set(f"{redis_prefix}:lobbies:{lobby_id}", json.dumps(lobby), ex=15)
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")

        emit("settings_update", settings, room=f"lobby:{lobby_id}", namespace="/ws/lobby")


    def on_disconnect(self, message):
        lobby_id = request.args.get("lobby_id")
        user_id = session["user_id"]

        lobby_lock = get_lobby(lobby_id)
        if not lobby_lock:
            return
        lobby, lock = lobby_lock
        try:
            if lobby["players"].get(user_id):
                del lobby["players"][user_id]
                exp_at = redis_client.expiretime(f"{redis_prefix}:lobbies:{lobby_id}")
                redis_client.set(f"{redis_prefix}:lobbies:{lobby_id}", json.dumps(lobby), ex=exp_at - int(time.time().__floor__()))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")

        leave_room(f"lobby:{lobby_id}")

        socketio.emit(f"player_update", lobby["players"], room=f"lobby:{lobby_id}", namespace="/ws/lobby")

        if user_id == lobby["owner"]:
            redis_client.hdel(f"{redis_prefix}:lobby_owners:connected", user_id)


    def heartbeat(self, user_id: str, lobby_id: str, join_token: str):
        is_connected = redis_client.hget(f"{redis_prefix}:lobby_owners:connected", user_id)
        while is_connected:
            redis_client.expire(f"{redis_prefix}:lobbies:{lobby_id}", 15)
            redis_client.expire(f"{redis_prefix}:join_token:{join_token}", 15)
            time.sleep(10)
            is_connected = redis_client.hget(f"{redis_prefix}:lobby_owners:connected", user_id)
