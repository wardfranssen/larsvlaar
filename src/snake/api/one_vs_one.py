from src.snake.main import redis_client, redis_prefix, get_lock, redlock
from flask_socketio import emit, join_room, Namespace
from src.snake.wrapper_funcs import *
from src.snake.app import socketio
import src.snake.game as game
from copy import deepcopy
from uuid import uuid4
import threading
import json
import time


default_game_state = {
    "players": {},  # {player_id: {snake_pos: [], ready: False, score: int}}
    "food_pos": [],  # List of food x and y
    "food_positions": [],  # Nested list of food x and y positions
    "started_at": 0, # At what unix timestamp the game started
    "winner": None, # Uuid of winner, None if draw
    "started": False,
    "settings": game.game_mode_config["one_vs_one"],
    "deaths": {}
}

default_matchmaking_game = {
    "players": {}
}


def game_done(game_id: str, game_state: dict, game_mode: str, outcome: str):
    socketio.close_room(f"spectate:{game_id}", namespace=f"/ws/spectate")

    players_ids = [
        list(game_state["players"].keys())[0],
        list(game_state["players"].keys())[1]
    ]
    redis_client.setex(f"{redis_prefix}:just_ended:{game_id}", 15, json.dumps(players_ids))

    print(json.dumps(game_state["deaths"]))

    if outcome != "draw":
       game_state["winner"] = outcome

    redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id, json.dumps(game_state))

    socketio.emit("game_over", {"winner": outcome}, room=f"game:one_vs_one:{game_id}", namespace="/ws/one_vs_one/game")

    game.save_game(game_id, game_mode)


def one_vs_one_game_loop(game_id: str):
    game_mode = "one_vs_one"
    game_mode_config = game.game_mode_config[game_mode]
    game_state = redis_client.hget(f"{redis_prefix}:games:one_vs_one", game_id)

    if not game_state:
        return

    game_state = json.loads(game_state)

    # Wait till both players are ready
    while True:
        for player_id in game_state["players"]:
            if not game_state["players"][player_id]["ready"]:
                break
        else:
            break
        time.sleep(0.1)
        game_state = json.loads(redis_client.hget(f"{redis_prefix}:games:one_vs_one", game_id))

    game_state["started_at"] = int(time.time()) + 5
    game_state["started"] = True

    game_state["food"] = {}
    food_positions = []
    for i in range(game_mode_config["food_amount"]):
        food_pos = game.generate_food_pos([player["snake_pos"] for player in game_state["players"].values()], game_mode_config,
                                     food_positions)
        if i == 0:
            food_pos = [int(game_mode_config["board"]["cols"] // 2), int(game_mode_config["board"]["rows"] // 2)]
        game_state["food"][i] = [food_pos]
        food_positions.append(food_pos)

    redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id, json.dumps(game_state))

    # Remove this game from matchmaking
    socketio.close_room(f"matchmaking:{game_id}", namespace="/ws/one_vs_one/matchmaking")
    redis_client.hdel(f"{redis_prefix}:matchmaking:one_vs_one", game_id)

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

    socketio.emit("game_update", game_update, room=f"game:one_vs_one:{game_id}", namespace="/ws/one_vs_one/game")

    # Countdown
    time.sleep(5)

    socketio.emit("game_start", room=f"game:one_vs_one:{game_id}", namespace="/ws/one_vs_one/game")

    while True:
        time.sleep(game_state["settings"]["update_interval"])

        lock = get_lock(f"{redis_prefix}:lock:game:one_vs_one:{game_id}")
        if not lock:
            continue
        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:one_vs_one", game_id)
            if not game_state:
                return
            game_state = json.loads(game_state)

            # Stop game if no players
            if len(game_state["players"]) == 0:
                # This can be called if both players leave in the same game update
                print(game_state["winner"])
                print("Both player left in same update")
                return
            elif len(game_state["players"]) == 1:
                print("1 PLAYER LEFT")
                winner = list(game_state["players"].keys())[0]
                game_state["winner"] = winner

                socketio.emit("game_over", {"winner": winner}, room=f"game:one_vs_one:{game_id}", namespace="/ws/one_vs_one/game")

                redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id, json.dumps(game_state))

                game.save_game(game_id, game_mode)
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


                for i, food_positions in game_state["food"].items():
                    # Check if hit food
                    if new_head == food_positions[-1]:
                        game_state["food"][i].append(game.generate_food_pos([player["snake_pos"] for player in game_state["players"].values()], game_mode_config, active_food_positions))
                        player["score"] += 1
                        break
                else:
                    new_pos.pop(0)

                player["prev_snake_pos"] = current_pos
                snakes_pos.append(new_pos)
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")

        # Check for collisions
        players = list(game_state["players"].items())
        player1_id, player1 = players[0]
        player2_id, player2 = players[1]

        player1_pos = player1["snake_pos"]
        player2_pos = player2["snake_pos"]

        # Check for head-to-head collision (draw)
        if player1_pos[-1] == player2_pos[-1]:
            print("DRAW - Head collision")
            game_state["deaths"][player1_id] = "killed_by_others"
            game_state["deaths"][player2_id] = "killed_by_others"

            game_done(game_id, game_state, game_mode, "draw")
            return

        # Check for simultaneous border collisions (draw)
        player1_border = game.hit_border(player1_pos, game_mode_config)
        player2_border = game.hit_border(player2_pos, game_mode_config)

        if player1_border and player2_border:
            print("DRAW - Both hit borders")
            game_state["players"][player1_id]["cause_of_death"] = "border_deaths"
            game_state["players"][player2_id]["cause_of_death"] = "border_deaths"

            game_done(game_id, game_state, game_mode, "draw")
            return

        # Check individual collisions
        player1_killed_by_other = game.check_collision_with_other_snake(player1_pos, player2_pos)
        player1_suicide = game.hit_self(player1_pos)

        player2_killed_by_other = game.check_collision_with_other_snake(player2_pos, player1_pos)
        player2_suicide = game.hit_self(player2_pos)

        if player1_killed_by_other:
            game_state["players"][player1_id]["cause_of_death"] = "killed_by_others"
            game_state["players"][player2_id]["kills"].append(player1_id)
        elif player1_suicide:
            game_state["players"][player1_id]["cause_of_death"] = "suicides"
        elif player1_border:
            game_state["players"][player1_id]["cause_of_death"] = "border_deaths"

        if player2_killed_by_other:
            game_state["players"][player2_id]["cause_of_death"] = "killed_by_others"
            game_state["players"][player1_id]["kills"].append(player2_id)
        elif player2_suicide:
            game_state["players"][player2_id]["cause_of_death"] = "suicides"
        elif player2_border:
            game_state["players"][player2_id]["cause_of_death"] = "border_deaths"


        player1_dead = (player1_killed_by_other or player1_suicide or player1_border)
        player2_dead = (player2_killed_by_other or player2_suicide or player2_border)

        # If both died in the same frame but not from the same cause
        if player1_dead and player2_dead:
            print("DRAW - Both died same frame")
            game_done(game_id, game_state, game_mode, "draw")
            return

        # Determine winner if only one player died
        if player1_dead:
            print(f"Player {player2_id} wins")
            game_done(game_id, game_state, game_mode, player2_id)
            return

        if player2_dead:
            print(f"Player {player1_id} wins")
            game_done(game_id, game_state, game_mode, player1_id)
            return

        food_positions = []
        for i, food_pos in game_state["food"].items():
            food_positions.append(food_pos[-1])

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

        socketio.emit("game_update", game_update, room=f"game:one_vs_one:{game_id}", namespace="/ws/one_vs_one/game")
        redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id, json.dumps(game_state))
        socketio.emit("game_update", game_update, room=f"spectate:{game_id}", namespace="/ws/spectate")



class OneVsOneNamespace(Namespace):
    @login_required()
    def on_connect(self):
        game_id = request.args.get("game_id")
        player_id = session["user_id"]

        lock = get_lock(f"{redis_prefix}:lock:game:one_vs_one:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:one_vs_one", game_id)

            if not game_state:
                print("GAME DOES NOT EXIST")
                flash("Game bestaat niet of is afgelopen", "error")
                emit("leave_game")
                return

            game_state = json.loads(game_state)

            if player_id not in game_state["players"]:
                print("NOT ALLOWED TO JOIN")
                flash("Geen toegang tot dat spel", "error")
                emit("leave_game")
                return
            if game_state["started"]:
                print("GAME HAS ALREADY STARTED")
                emit("game_start")

            join_room(f"game:one_vs_one:{game_id}")
            join_room(f"{game_id}:{session['user_id']}")

            opponent_id = next((user_id for user_id in game_state["players"].keys() if user_id != player_id), None)
            if game_state["players"][opponent_id]["connected"]:
                socketio.emit("opp_connected", room=f"{game_id}:{opponent_id}", namespace="/ws/one_vs_one/game")

            if game_state["players"][opponent_id]["ready"]:
                emit("opp_ready")

            game_state["players"][player_id]["connected"] = True

            redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")


    def on_ready(self):
        game_id = request.args.get("game_id")
        if not game_id:
            return

        player_id = session["user_id"]

        lock = get_lock(f"{redis_prefix}:lock:game:one_vs_one:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:one_vs_one", game_id)
            if not game_state:
                disconnect()
                return
            game_state = json.loads(game_state)

            opponent_id = next((user_id for user_id in game_state["players"].keys() if user_id != player_id), None)

            if not opponent_id:
                emit("opp_disconnected")

            if not game_state["players"][opponent_id].get("connected"):
                emit("not_ready")
                return

            game_mode_config = game.game_mode_config["one_vs_one"]

            spawn_y = int(game_mode_config["board"]["rows"] / 2)
            spawn_len = game_mode_config["spawn_len"]
            if game_state["players"][opponent_id]["ready"]:
                spawn_position = []
                for i in range(spawn_len):
                    spawn_position.append([i, spawn_y])
                spawn_dir = "right"
            else:
                spawn_position = []
                for i in range(spawn_len):
                    spawn_position.append([game_mode_config["board"]["cols"] - i - 1, spawn_y])
                spawn_dir = "left"

            game_state["players"][player_id].update({
                "snake_pos": spawn_position,
                "prev_snake_pos": [],
                "current_snake_dir": spawn_dir,
                "moves_this_update": [spawn_dir],
                "moves": [],
                "score": 0,
                "ready": True,
                "spawn_pos": spawn_position,
                "kills": [],
                "cause_of_death": None
            })

            redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")

        # Start the game if all players are ready
        for user_id in game_state["players"]:
            if not game_state["players"][user_id]["ready"]:
                break
        else:
            threading.Thread(target=one_vs_one_game_loop, args=[game_id], daemon=True).start()
            socketio.emit("countdown_start", room=f"game:one_vs_one:{game_id}", namespace="/ws/one_vs_one/game")
            return

        socketio.emit("opp_ready", room=f"{game_id}:{opponent_id}", namespace="/ws/one_vs_one/game")


    def on_snake_dir(self, data):
        game_id = request.args.get("game_id")
        if not game_id:
            return

        lock = get_lock(f"{redis_prefix}:lock:game:one_vs_one:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:one_vs_one", game_id)

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

            redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id, json.dumps(game_state))
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")


    def on_disconnect(self, message):
        """Handle player disconnection."""
        print("DISCONNECT")
        game_id = request.args.get("game_id")
        if not game_id:
            return

        socketio.emit("opp_disconnected", room=f"game:one_vs_one:{game_id}", namespace="/ws/one_vs_one/game")

        lock = get_lock(f"{redis_prefix}:lock:game:one_vs_one:{game_id}")
        if not lock:
            return

        try:
            game_state = redis_client.hget(f"{redis_prefix}:games:one_vs_one", game_id)

            if game_state:
                game_state = json.loads(game_state)
                player_id = session["user_id"]
                opponent_id = next((user_id for user_id in game_state["players"].keys() if user_id != player_id), None)

                game_state["players"][opponent_id]["ready"] = False

                game_state["players"][player_id].update({
                    "connected": False,
                    "ready": False
                })
                redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id, json.dumps(game_state))
            else:
                socketio.close_room(f"game:one_vs_one:{game_id}", namespace=f"/ws/one_vs_one/game")
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")


class MatchmakingOneVsOneNamespace(Namespace):
    @login_required()
    def on_connect(self):
        try:
            game_mode = "one_vs_one"
            max_players = 2
            default_player_state = {
                "username": session["username"],
                "pfp_version": session["pfp_version"],
                "ready": False,
                "connected": False
            }

            game_id = session["game_id"]
            player_id = session["user_id"]

            matchmaking_games = redis_client.hgetall(f"{redis_prefix}:matchmaking:one_vs_one")

            if game_id:
                matchmaking_lock = get_lock(f"{redis_prefix}:lock:matchmaking:{game_id}")
                if not matchmaking_lock:
                    return
                try:
                    # Remove player from current game
                    if game_id in matchmaking_games:
                        game_state = redis_client.hget(f"{redis_prefix}:matchmaking:one_vs_one", game_id)
                        if game_state:
                            game_state = json.loads(game_state)

                            if player_id in game_state["players"]:
                                del game_state["players"][player_id]
                                redis_client.hset(f"{redis_prefix}:matchmaking:one_vs_one", game_id, json.dumps(game_state))
                    else:
                        game_lock = get_lock(f"{redis_prefix}:lock:game:one_vs_one:{game_id}")
                        if not game_lock:
                            return
                        try:
                            game_state = redis_client.hget(f"{redis_prefix}:games:one_vs_one", game_id)
                            if game_state:
                                game_state = json.loads(game_state)

                                if player_id in game_state["players"]:
                                    del game_state["players"][player_id]
                                    redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id,
                                                      json.dumps(game_state))
                        finally:
                            try:
                                redlock.unlock(game_lock)
                            except Exception as e:
                                logger.warning(f"Failed to unlock {game_lock.resource}: {e}")
                finally:
                    try:
                        redlock.unlock(matchmaking_lock)
                    except Exception as e:
                        logger.warning(f"Failed to unlock {matchmaking_lock.resource}: {e}")


            for game_id, raw_game_state in matchmaking_games.items():
                game_state = json.loads(raw_game_state)
                if len(game_state["players"]) >= max_players:
                    continue

                lock = get_lock(f"{redis_prefix}:lock:matchmaking:{game_id}")
                if not lock:
                    continue

                try:
                    game_state = redis_client.hget(f"{redis_prefix}:matchmaking:one_vs_one", game_id)
                    if not game_state:
                        continue
                    game_state = json.loads(game_state)

                    if len(game_state["players"]) < max_players:
                        # Add player to game
                        game_state["players"][player_id] = default_player_state
                        redis_client.hset(f"{redis_prefix}:matchmaking:one_vs_one", game_id, json.dumps(game_state))

                        players = game_state["players"]

                        # Let player know that found a match
                        emit("found_match", game_state)

                        join_room(f"matchmaking:{game_id}")
                        session["game_id"] = game_id

                        if len(game_state["players"]) == max_players:
                            # Let both players know that game can start
                            socketio.emit("game_start", {"game_id": game_id, "players": players}, room=f"matchmaking:{game_id}", namespace="/ws/one_vs_one/matchmaking")

                            game_state = deepcopy(default_game_state)
                            game_state["players"] = players
                            game_state["settings"]["board"] = game.game_mode_config[game_mode]["board"]
                            redis_client.hset(f"{redis_prefix}:games:one_vs_one", game_id, json.dumps(game_state))
                            redis_client.setex(f"{redis_prefix}:game_mode:{game_id}", 3600, game_mode)
                        break
                finally:
                    try:
                        redlock.unlock(lock)
                    except Exception:
                        logger.warning(f"Failed to unlock {lock.resource}: {e}")
            else:
                # Create new game
                game_id = str(uuid4())

                game_state = deepcopy(default_matchmaking_game)
                game_state["players"][player_id] = default_player_state

                # Save to Redis
                redis_client.hset(f"{redis_prefix}:matchmaking:one_vs_one", game_id, json.dumps(game_state))

                join_room(f"matchmaking:{game_id}")

                # Let client know to wait till other user joins
                emit("looking_for_players", "test")
                print("Created a match: ", game_id)
                session["game_id"] = game_id
        except Exception as e:
            logger.error(f"handle_connect_matchmaking_one_vs_one: {e}", exc_info=True)


    def joining_game_one_vs_one(self):
        try:
            game_id = session["game_id"]
            player_id = session["user_id"]
            session["game_id"] = None

            # Remove player from current matchmaking
            if game_id:
                lock = get_lock(f"{redis_prefix}:lock:matchmaking:{game_id}")
                if not lock:
                    return
                try:
                    game_state = redis_client.hget(f"{redis_prefix}:matchmaking:one_vs_one", game_id)
                    if game_state:
                        game_state = json.loads(game_state)

                        if player_id in game_state["players"]:
                            if len(game_state["players"]) == 1:
                                redis_client.hdel(f"{redis_prefix}:matchmaking:one_vs_one", game_id)
                            else:
                                del game_state["players"][player_id]
                                redis_client.hset(f"{redis_prefix}:matchmaking:one_vs_one", game_id, json.dumps(game_state))
                finally:
                    try:
                        redlock.unlock(lock)
                    except Exception as e:
                        logger.warning(f"Failed to unlock {lock.resource}: {e}")
            else:
                disconnect()
        except Exception as e:
            logger.error(f"joining_game_one_vs_one: {e}", exc_info=True)


    def on_disconnect(self, message):
        try:
            game_id = session["game_id"]
            player_id = session["user_id"]
            session["game_id"] = None

            # Remove player from current game if in one
            if game_id:
                lock = get_lock(f"{redis_prefix}:lock:matchmaking:{game_id}")
                if not lock:
                    return
                try:
                    game_state = redis_client.hget(f"{redis_prefix}:matchmaking:one_vs_one", game_id)
                    if game_state:
                        game_state = json.loads(game_state)

                        if player_id in game_state["players"]:
                            socketio.emit("player_left", {"player_id": player_id}, room=f"matchmaking:{game_id}",
                                          namespace="/ws/one_vs_one/matchmaking")

                            del game_state["players"][player_id]
                            redis_client.hset(f"{redis_prefix}:matchmaking:one_vs_one", game_id, json.dumps(game_state))
                finally:
                    try:
                        redlock.unlock(lock)
                    except Exception as e:
                        logger.warning(f"Failed to unlock {lock.resource}: {e}")
        except Exception as e:
            logger.error(f"handle_disconnect_matchmaking_one_vs_one: {e}", exc_info=True)
