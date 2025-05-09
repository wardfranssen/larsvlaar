from flask_socketio import emit, join_room, Namespace
from src.snake.api.lobby import default_lobby_state
from src.snake.app import socketio
from src.snake.game import *
from src.snake.main import *
from copy import deepcopy
import threading
import json
import time


def game_done(game_id: str, game_state: dict, game_mode: str, outcome: str):
    socketio.close_room(f"spectate:{game_id}", namespace=f"/ws/spectate")

    players_ids = list(game_state["players"].keys())
    redis_client.setex(f"{redis_prefix}:just_ended:{game_id}", 15, json.dumps(players_ids))

    game_state["winner"] = outcome
    game_state["ended"] = True

    redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))

    socketio.emit("game_over", {"leaderboard": game_state["leaderboard"]}, room=f"game:custom:{game_id}", namespace="/ws/custom/game")

    save_game(game_id, game_mode)


def custom_game_loop(game_id: str):
    game_mode = "custom"

    lock = get_lock(f"{redis_prefix}:lock:game:custom:{game_id}")
    if not lock:
        return
    try:
        game_state = redis_client.hget(f"{redis_prefix}:games:custom", game_id)
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

        redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))
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

    socketio.emit("game_update", game_update, room=f"game:custom:{game_id}", namespace="/ws/custom/game")

    # Countdown
    time.sleep(5)

    socketio.emit("game_start", room=f"game:custom:{game_id}", namespace="/ws/custom/game")

    while True:
        time.sleep(game_state["settings"]["update_interval"])

        lock = get_lock(f"{redis_prefix}:lock:game:custom:{game_id}")
        if not lock:
            continue

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:custom", game_id)
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
                if not player["alive"]:
                    continue
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
                        socketio.emit("score_update", {player_id: player["score"]}, room=f"game:custom:{game_id}", namespace="/ws/custom/game")
                        break
                else:
                    if (game_settings["grow"] == 1) or (
                            game_settings["grow"] > 1 and (player["score"] + game_settings["spawn_len"]) <= len(
                            player["snake_pos"]) - 1):
                        new_pos.pop(0)

                player["prev_snake_pos"] = current_pos
                snakes_pos.append(new_pos)

            redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")

        # Check for collisions
        for player_id, player in game_state["players"].items():
            if not player["alive"]:
                continue
            player_pos = player["snake_pos"]
            has_hit_border = hit_border(player_pos, game_settings)
            has_hit_self = hit_self(player_pos)

            hit_other = False
            hit_other_user_id = None
            if not has_hit_self and not has_hit_border:
                for other_player_id, other_player in game_state["players"].items():
                    if not other_player["alive"] or player_id == other_player_id:
                        continue
                    if check_collision_with_other_snake(player_pos, other_player["snake_pos"]):
                        hit_other = True
                        hit_other_user_id = other_player_id
                        break


            if hit_other or has_hit_self or has_hit_border:
                try:
                    lock = get_lock(f"{redis_prefix}:lock:game:custom:{game_id}")
                    if not lock:
                        continue

                    game_state = redis_client.hget(f"{redis_prefix}:games:custom", game_id)
                    if not game_state:
                        return
                    game_state = json.loads(game_state)

                    if hit_other:
                        game_state["players"][player_id]["cause_of_death"] = "killed_by_others"
                        game_state["players"][hit_other_user_id]["kills"].append(player_id)
                    elif has_hit_self:
                        game_state["players"][player_id]["cause_of_death"] = "suicides"
                    elif has_hit_border:
                        game_state["players"][player_id]["cause_of_death"] = "border_deaths"

                    placement = 0
                    for _player_id in game_state["players"]:
                        if game_state["players"][_player_id]["alive"]:
                            placement += 1

                    game_state["players"][player_id]["alive"] = False

                    game_state["leaderboard"][placement] = {
                        "user_id": player_id,
                        "username": player["username"],
                        "pfp_version": player["pfp_version"]
                    }
                    game_state["players"][player_id]["placement"] = placement

                    redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))

                    if placement == 2:
                        # Set data for player who is in placement first
                        for _player_id in game_state["players"]:
                            if game_state["players"][_player_id]["alive"]:
                                game_state["players"][_player_id]["alive"] = False
                                game_state["leaderboard"][1] = {
                                    "user_id": _player_id,
                                    "username": game_state["players"][_player_id]["username"],
                                    "pfp_version": game_state["players"][_player_id]["pfp_version"]
                                }
                                game_state["players"][_player_id]["placement"] = 1
                                break
                        redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))
                        game_done(game_id, game_state, game_mode, _player_id)
                        return
                    elif placement == 1:
                        game_done(game_id, game_state, game_mode, player_id)
                        return
                    socketio.emit("died", {"placement": placement}, room=f"{game_id}:{player_id}", namespace="/ws/custom/game")
                    socketio.emit("players", game_state["players"], room=f"game:custom:{game_id}", namespace="/ws/custom/game")
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
            if game_state["players"][player_id]["alive"]:
                game_update["players"][player_id] = {
                    "snake_pos": game_state["players"][player_id]["snake_pos"],
                    "score": game_state["players"][player_id]["score"],
                    "pfp_version": game_state["players"][player_id]["pfp_version"]
                }
        socketio.emit("game_update", game_update, room=f"game:custom:{game_id}", namespace="/ws/custom/game")
        socketio.emit("game_update", game_update, room=f"spectate:{game_id}", namespace="/ws/spectate")


class CustomNamespace(Namespace):
    @login_required()
    def on_connect(self):
        game_id = request.args.get("game_id")
        player_id = session["user_id"]

        lock = get_lock(f"{redis_prefix}:lock:game:custom:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:custom", game_id)

            if not game_state:
                flash("Game bestaat niet of is afgelopen", "error")
                emit("leave_game")
                return

            game_state = json.loads(game_state)

            if game_state["ended"]:
                flash("Game bestaat niet of is afgelopen", "error")
                emit("leave_game")

            if player_id not in game_state["players"]:
                print("NOT ALLOWED TO JOIN")
                flash("Geen toegang tot dat spel", "error")
                emit("leave_game")
                return
            if game_state["started"]:
                print("GAME HAS ALREADY STARTED")
                emit("game_start")

            if player_id == game_state["owner"]:
                emit("owner_status")

            join_room(f"game:custom:{game_id}")
            join_room(f"{game_id}:{session['user_id']}")

            game_state["players"][player_id]["connected"] = True

            redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")
                disconnect()
                return
        emit("board", game_state["settings"]["board"])
        socketio.emit("players", game_state["players"], room=f"game:custom:{game_id}", namespace="/ws/custom/game")


    def on_kick_user(self, to_kick_user_id):
        game_id = request.args.get("game_id")
        player_id = session["user_id"]

        lock = get_lock(f"{redis_prefix}:lock:game:custom:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:custom", game_id)

            if not game_state:
                flash("Game is afgelopen", "error")
                emit("leave_game")
                return

            game_state = json.loads(game_state)

            if player_id != game_state["owner"] or to_kick_user_id not in game_state["players"] or game_state["started"]:
                return

            del game_state["players"][to_kick_user_id]

            redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")
                disconnect()
                return
        socketio.emit("players", game_state["players"], room=f"game:custom:{game_id}", namespace="/ws/custom/game")


    def on_start_game(self):
        game_id = request.args.get("game_id")
        player_id = session["user_id"]

        game_state = redis_client.hget(f"{redis_prefix}:games:custom", game_id)

        if not game_state:
            flash("Game bestaat niet of is afgelopen", "error")
            emit("leave_game")
            return

        game_state = json.loads(game_state)

        if game_state["started"] or player_id != game_state["owner"]:
            return

        threading.Thread(target=custom_game_loop, args=[game_id], daemon=True).start()
        socketio.emit("countdown_start", room=f"game:custom:{game_id}", namespace="/ws/custom/game")


    def on_snake_dir(self, data):
        game_id = request.args.get("game_id")
        if not game_id:
            return

        lock = get_lock(f"{redis_prefix}:lock:game:custom:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:custom", game_id)

            if not game_state:
                return
            game_state = json.loads(game_state)

            player_id = session["user_id"]
            if not game_state["players"][player_id]["alive"]:
                return

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

            redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")


    def on_rematch(self):
        game_id = request.args.get("game_id")
        if not game_id:
            return

        if redis_client.exists(f"{redis_prefix}:lobbies:{game_id}"):
            emit("join_lobby")
            pass

        lock = get_lock(f"{redis_prefix}:lock:game:custom:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:custom", game_id)

            if not game_state:
                return
            game_state = json.loads(game_state)
            user_id = session["user_id"]

            if not game_state["ended"] or game_state["players"][user_id]["rematch"] is not None:
                return

            game_state["players"][user_id]["rematch"] = True
            join_room(f"rematch:{game_id}")

            if game_state["owner"] == user_id:
                allowed_to_join = []
                players = {}
                for player_id, player in game_state["players"].items():
                    allowed_to_join.append(player_id)
                    is_owner = user_id == player_id
                    if player["rematch"]:
                        players[player_id] = {
                            "username": player["username"],
                            "pfp_version": player["pfp_version"],
                            "owner": is_owner
                        }

                join_token = generate_join_token()

                lobby_state = deepcopy(default_lobby_state)
                lobby_state.update({
                    "owner": user_id,
                    "allowed_to_join": allowed_to_join,
                    "players": players,
                    "join_token": join_token,
                    "settings": game_state["settings"]
                })


                redis_client.set(f"{redis_prefix}:lobbies:{game_id}", json.dumps(lobby_state), 30)
                redis_client.set(f"{redis_prefix}:join_token:{join_token}", game_id, 30)

                socketio.emit("join_lobby", room=f"rematch:{game_id}", namespace="/ws/custom/game")

            rematch_players = []
            for player_id, player in game_state["players"].items():
                if player["rematch"]:
                    rematch_players.append(player_id)
            socketio.emit("player_rematch", {"users": rematch_players}, room=f"game:custom:{game_id}", namespace="/ws/custom/game")

            redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))
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

        lock = get_lock(f"{redis_prefix}:lock:game:custom:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:custom", game_id)

            if game_state:
                game_state = json.loads(game_state)

                game_state["players"][player_id].update({
                    "connected": False
                })
                redis_client.hset(f"{redis_prefix}:games:custom", game_id, json.dumps(game_state))
                socketio.emit("players", game_state["players"],  room=f"game:custom:{game_id}", namespace="/ws/custom/game")
            else:
                socketio.close_room(f"game:custom:{game_id}", namespace=f"/ws/custom/game")
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")
