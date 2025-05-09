from flask_socketio import emit, join_room, Namespace
from src.snake.app import socketio, limiter, get_user_or_session_key
from src.snake.game import *
from src.snake.main import *
from flask import Blueprint
from copy import deepcopy
import threading
import json
import time


single_player_bp = Blueprint("single_player", __name__, url_prefix="/api/single_player")

default_game_state = {
    "players": {},  # {player_id: {snake_pos: [], ready: False, score: int}}
    "food_pos": [],  # List of food x and y
    "food_positions": [],  # Nested list of food x and y positions
    "started_at": 0, # At what unix timestamp the game started
    "winner": None, # Uuid of winner, None if draw
    "started": False,
    "ended": False,
    "settings": game_mode_config["single_player"],
    "deaths": {}
}


@single_player_bp.post("/create")
@login_required()
@wrap_errors()
@limiter.limit("3 per 10 seconds", key_func=get_user_or_session_key)
@limiter.limit("10 per minute", key_func=get_user_or_session_key)
def create_game():
    user_id = session["user_id"]
    game_id = str(uuid4())

    game_state = deepcopy(default_game_state)
    game_settings = game_state["settings"]

    spawn_len = game_settings["spawn_len"]
    spawn_y = int(game_settings["board"]["rows"] / 2)

    spawn_position = []
    for i in range(spawn_len):
        spawn_position.append([i, spawn_y])
    spawn_dir = "right"

    game_state["players"][user_id] = {
        "username": get_username(user_id),
        "pfp_version": get_pfp_version(user_id),
        "connected": False,
        "snake_pos": spawn_position,
        "prev_snake_pos": [],
        "current_snake_dir": spawn_dir,
        "moves_this_update": [spawn_dir],
        "moves": [],
        "score": 0,
        "spawn_pos": spawn_position,
        "kills": [],
        "cause_of_death": None
    }

    # Save to Redis
    redis_client.hset(f"{redis_prefix}:games:single_player", game_id, json.dumps(game_state))

    return jsonify({
        "error": False,
        "redirect": f"/snake/single_player?game_id={game_id}"
    })


def game_done(game_id: str, game_state: dict, game_mode: str):
    socketio.close_room(f"spectate:{game_id}", namespace=f"/ws/spectate")

    players_ids = list(game_state["players"].keys())
    redis_client.setex(f"{redis_prefix}:just_ended:{game_id}", 15, json.dumps(players_ids))

    game_state["ended"] = True

    redis_client.hset(f"{redis_prefix}:games:single_player", game_id, json.dumps(game_state))

    socketio.emit("game_over", game_state["players"][players_ids[0]]["score"], room=f"game:single_player:{game_id}", namespace="/ws/single_player/game")

    save_game(game_id, game_mode)


def single_player_game_loop(game_id: str):
    game_mode = "single_player"

    lock = get_lock(f"{redis_prefix}:lock:game:single_player:{game_id}")
    if not lock:
        return
    try:
        game_state = redis_client.hget(f"{redis_prefix}:games:single_player", game_id)
        if not game_state:
            return
        game_state = json.loads(game_state)

        game_settings = game_state["settings"]

        game_state["started_at"] = int(time.time()) + 5
        game_state["started"] = True

        game_state["food"] = {}
        food_positions = []
        for i in range(game_settings["food_amount"]):
            food_pos = generate_food_pos([player["snake_pos"] for player in game_state["players"].values()], game_settings, food_positions)
            if i == 0:
                food_pos = [int(game_settings["board"]["cols"] // 2), int(game_settings["board"]["rows"] // 2)]

            game_state["food"][i] = [food_pos]
            food_positions.append(food_pos)

        redis_client.hset(f"{redis_prefix}:games:single_player", game_id, json.dumps(game_state))
    finally:
        try:
            redlock.unlock(lock)
        except Exception as e:
            logger.warning(f"Failed to unlock {lock.resource}: {e}")
            return

    game_update = {
        "food": food_positions,
        "players": {}
    }

    for player_id in game_state["players"]:
        game_update["players"][player_id] = {
            "snake_pos": game_state["players"][player_id]["snake_pos"],
            "score": game_state["players"][player_id]["score"],
            "pfp_version": game_state["players"][player_id]["pfp_version"]
        }

    socketio.emit("game_update", game_update, room=f"game:single_player:{game_id}", namespace="/ws/single_player/game")

    # Countdown
    time.sleep(2.8)

    socketio.emit("game_start", room=f"game:single_player:{game_id}", namespace="/ws/single_player/game")

    while True:
        time.sleep(game_state["settings"]["update_interval"])

        lock = get_lock(f"{redis_prefix}:lock:game:single_player:{game_id}")
        if not lock:
            continue

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:single_player", game_id)
            if not game_state:
                return
            game_state = json.loads(game_state)

            # Stop game if no players
            if len(game_state["players"]) == 0:
                # This can be called if both players leave in the same game update
                print(game_state["winner"])
                print("No players left")
                return

            snakes_pos = []

            # Update player pos and check if hit food
            for player_id, player in game_state["players"].items():
                current_pos = player["snake_pos"]

                next_direction = player["moves_this_update"][-1]
                current_head = current_pos[-1]

                directions = {
                    "right": [1, 0],
                    "left": [-1, 0],
                    "up": [0, -1],
                    "down": [0, 1],
                }

                new_head = [current_head[0] + directions[next_direction][0], current_head[1] + directions[next_direction][1]]
                new_pos = current_pos + [new_head]

                player["snake_pos"] = new_pos
                player["current_snake_dir"] = next_direction
                player["moves_this_update"] = [next_direction]
                player["moves"] += [next_direction]

                active_food_positions = []
                for i, food_pos in game_state["food"].items():
                    active_food_positions.append(food_pos[-1])


                # Check if hit food
                for i, food_positions in game_state["food"].items():
                    if new_head == food_positions[-1]:
                        game_state["food"][i].append(generate_food_pos([player["snake_pos"] for player in game_state["players"].values()], game_settings, active_food_positions))

                        player["score"] += game_settings["grow"]
                        socketio.emit("score_update", {player_id: player["score"]}, room=f"game:single_player:{game_id}", namespace="/ws/single_player/game")
                        break
                else:
                    if (game_settings["grow"] == 1) or (
                            game_settings["grow"] > 1 and (player["score"] + game_settings["spawn_len"]) <= len(
                            player["snake_pos"]) - 1):
                        new_pos.pop(0)

                player["prev_snake_pos"] = current_pos
                snakes_pos.append(new_pos)

            redis_client.hset(f"{redis_prefix}:games:single_player", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")

        # Check for collisions
        for player_id, player in game_state["players"].items():
            player_pos = player["snake_pos"]
            has_hit_border = hit_border(player_pos, game_settings)
            has_hit_self = hit_self(player_pos)

            if has_hit_self or has_hit_border:
                try:
                    lock = get_lock(f"{redis_prefix}:lock:game:single_player:{game_id}")
                    if not lock:
                        continue

                    game_state = redis_client.hget(f"{redis_prefix}:games:single_player", game_id)
                    if not game_state:
                        return
                    game_state = json.loads(game_state)

                    if has_hit_self:
                        game_state["players"][player_id]["cause_of_death"] = "suicides"
                    elif has_hit_border:
                        game_state["players"][player_id]["cause_of_death"] = "border_deaths"

                    redis_client.hset(f"{redis_prefix}:games:single_player", game_id, json.dumps(game_state))

                    socketio.emit("died", room=f"{game_id}:{player_id}", namespace="/ws/single_player/game")

                    game_done(game_id, game_state, game_mode)
                    return
                finally:
                    try:
                        redlock.unlock(lock)
                    except Exception as e:
                        logger.warning(f"Failed to unlock {lock.resource}: {e}")

        food_positions = []
        for i, food_pos in game_state["food"].items():
            food_positions.append(food_pos[-1])

        game_update = {
            "food": food_positions,
            "players": {}
        }

        for player_id in list(game_state["players"].keys()):
            game_update["players"][player_id] = {
                "snake_pos": game_state["players"][player_id]["snake_pos"],
                "score": game_state["players"][player_id]["score"],
                "pfp_version": game_state["players"][player_id]["pfp_version"]
            }
        socketio.emit("game_update", game_update, room=f"game:single_player:{game_id}", namespace="/ws/single_player/game")
        socketio.emit("game_update", game_update, room=f"spectate:{game_id}", namespace="/ws/spectate")


class SinglePlayerNamespace(Namespace):
    @login_required()
    def on_connect(self):
        game_id = request.args.get("game_id")
        player_id = session["user_id"]

        lock = get_lock(f"{redis_prefix}:lock:game:single_player:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:single_player", game_id)
            print(game_state)
            if not game_state:
                flash("Game bestaat niet of is afgelopen", "error")
                emit("leave_game")
                return

            game_state = json.loads(game_state)

            if game_state["ended"]:
                flash("Game is afgelopen", "error")
                emit("leave_game")

            if player_id not in game_state["players"]:
                print("NOT ALLOWED TO JOIN")
                flash("Geen toegang tot dat spel", "error")
                emit("leave_game")
                return

            join_room(f"game:single_player:{game_id}")
            join_room(f"{game_id}:{session['user_id']}")

            if game_state["started"]:
                print("GAME HAS ALREADY STARTED")
                emit("game_start")
            else:
                threading.Thread(target=single_player_game_loop, args=[game_id], daemon=True).start()
                emit("countdown_start")

            game_state["players"][player_id]["connected"] = True

            redis_client.hset(f"{redis_prefix}:games:single_player", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")
                disconnect()
                return
        emit("players", game_state["players"])


    def on_start_game(self):
        game_id = request.args.get("game_id")
        player_id = session["user_id"]

        game_state = redis_client.hget(f"{redis_prefix}:games:single_player", game_id)

        if not game_state:
            flash("Game bestaat niet of is afgelopen", "error")
            emit("leave_game")
            return

        game_state = json.loads(game_state)

        if game_state["started"] or player_id != game_state["owner"]:
            return


    def on_snake_dir(self, data):
        game_id = request.args.get("game_id")
        if not game_id:
            return

        lock = get_lock(f"{redis_prefix}:lock:game:single_player:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:single_player", game_id)

            if not game_state:
                return
            game_state = json.loads(game_state)

            player_id = session["user_id"]

            next_direction = data["snake_dir"]
            current_direction = game_state["players"][player_id]["current_snake_dir"]

            opposite_dirs = {
                "right": "left",
                "left": "right",
                "up": "down",
                "down": "up"
            }

            if next_direction == opposite_dirs.get(current_direction, ""):
                next_direction = game_state["players"][player_id]["moves_this_update"][-1]

            game_state["players"][player_id]["moves_this_update"].append(next_direction)

            redis_client.hset(f"{redis_prefix}:games:single_player", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")


    def on_disconnect(self, message):
        """Handle player disconnection."""
        game_id = request.args.get("game_id")
        player_id = session["user_id"]
        if not game_id:
            return

        lock = get_lock(f"{redis_prefix}:lock:game:single_player:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:single_player", game_id)

            if game_state:
                game_state = json.loads(game_state)

                game_state["players"][player_id].update({
                    "connected": False
                })
                redis_client.hset(f"{redis_prefix}:games:single_player", game_id, json.dumps(game_state))
                emit("players", game_state["players"])
            else:
                socketio.close_room(f"game:single_player:{game_id}", namespace=f"/ws/single_player/game")
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")
