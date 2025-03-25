import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, send_file, session, flash, redirect, jsonify
from flask_socketio import SocketIO, emit, join_room, disconnect
from flask_cors import CORS, cross_origin
from flask_limiter import Limiter
from flask_session import Session
from datetime import timedelta
from uuid import uuid4
import send_email
import threading
import argparse
import register
import logging
import bcrypt
import random
import login
import copy
import game
import json
import main
import time
import mfa
import os

config = main.config
redis_client = main.redis_client

redis_prefix = config["REDIS"]["PREFIX"]

parser = argparse.ArgumentParser()
parser.add_argument('-p', type=int, default=5000, help='Port to run the server on')
args = parser.parse_args()

port = args.p

app = Flask(__name__, template_folder="../../templates/snake", static_folder="../../static/snake")

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
    SECRET_KEY=config["SECRET_KEY"],
    SESSION_TYPE="redis",
    SESSION_KEY_PREFIX=f"{redis_prefix}-session:",
    SESSION_REDIS=redis_client,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=config["SESSION_TTL"]),
    SESSION_PERMANENT=True,
    SESSION_SERIALIZATION_FORMAT="json"
)

Session(app)
cors = CORS(app, resources={
    r"/*": {
        "origins": ["https://dev.larsvlaar.nl"]  # Restrict to your frontend domain
    }
})

socketio = SocketIO(
    app,
    manage_session=False,
    message_queue=f'redis://:{config["REDIS"]["PASSWORD"]}@{config["REDIS"]["HOST"]}:{config["REDIS"]["PORT"]}/0',
    cors_allowed_origins="*",  # Allow all origins (restrict in prod)
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

quotes = json.loads(open(f"{app.static_folder}/quotes.json").read())
motivational_quotes = json.loads(open(f"{app.static_folder}/motivational_quotes.json").read())


def get_user_or_session_key():
    if session.get("user_id"):
        return f"user:{session['user_id']}"
    return f"session:{session.sid}"


limiter = Limiter(
    get_user_or_session_key,
    app=app,
    storage_uri=f"redis://{config['REDIS']['HOST']}:{config['REDIS']['PORT']}",
    storage_options={"password": config["REDIS"]["PASSWORD"]}
)

# Multiplayer
# -------------------------------------------------------------------------

default_game_state = {
    "players": {},  # {player_id: {snake_pos: [], ready: False, score: int}}
    "game_mode": "",
    "food_pos": [],  # List of food x and y
    "update_interval": 0.300, # Interval between updates in seconds
    "game_start": 0, # At what unix timestamp the game started
    "winner": "", # Uuid of winner
    "started": False
}

default_matchmaking_game = {
    "players": {},  # List of player ids
    "game_mode": ""
}

game_modes = [
    "massive_multiplayer",
    "one_vs_one",
    "single_player",
    "custom"
]


def one_vs_one_game_loop(game_id: str):
    game_mode = "one_vs_one"

    # Wait till both players are ready
    while True:
        game_state = json.loads(redis_client.hget(f"{redis_prefix}-games-one_vs_one", game_id))
        for player_id in game_state["players"]:
            if not game_state["players"][player_id]["ready"]:
                break
        else:
            break
        time.sleep(0.1)


    game_state["game_start"] = int(time.time())
    game_state["started"] = True

    redis_client.hset(f"{redis_prefix}-games-one_vs_one", game_id, json.dumps(game_state))

    # Remove this game from matchmaking
    socketio.close_room(f"matchmaking:{game_id}", namespace="/matchmaking_one_vs_one")
    redis_client.hdel(f"{redis_prefix}-matchmaking-one_vs_one", game_id)

    if not game_state:
        return


    while True:
        time.sleep(game_state["update_interval"])

        game_state = json.loads(redis_client.hget(f"{redis_prefix}-games-one_vs_one", game_id))

        if not game_state:
            return

        # Stop game if no players
        if len(game_state["players"]) == 0:
            # This can be called if both players leave in the same game update
            print(game_state["winner"])
            print("Both player left in same update")
            return
        elif len(game_state["players"]) == 1:
            winner = list(game_state["players"].keys())[0]
            game_state["winner"] = winner

            socketio.emit("game_over", {"winner": winner}, room=f"game:{game_id}", namespace="/one_vs_one")

            redis_client.hset(f"{redis_prefix}-games-one_vs_one", game_id, json.dumps(game_state))

            game.save_game(game_id, game_mode)
            return

        snakes_pos = []

        for player_id, player in game_state["players"].items():
            current_pos = player["snake_pos"]
            opponent_id = next((user_id for user_id in game_state["players"].keys() if user_id != player_id), None)

            if current_pos == player["prev_snake_pos"]:
                print("SAME LOCATION")

            direction = game_state["players"][player_id]["snake_dir"]

            current_head = current_pos[-1]

            # print(direction)

            directions = {
                "right": [1, 0],
                "left": [-1, 0],
                "up": [0, -1],
                "down": [0, 1],
            }

            new_head = [current_head[0] + directions[direction][0], current_head[1] + directions[direction][1]]

            new_pos = current_pos + [new_head]

            game_state["players"][player_id]["snake_pos"] = new_pos

            # Check if hit food
            if new_head == game_state["food_pos"]:
                game_state["food_pos"] = None
            else:
                new_pos.pop(0)

            player["prev_snake_pos"] = current_pos
            snakes_pos.append(new_pos)

            # print(new_pos)

            # COMMENTED FOR TESTING PURPOSES
            # COMMENTED FOR TESTING PURPOSES
            # COMMENTED FOR TESTING PURPOSES
            # COMMENTED FOR TESTING PURPOSES
            # Check collision with other snake
            # Todo: Add winner to game_state and save to Redis
            # if game.check_collision_with_other_snake(new_pos, game_state["players"][opponent_id]["snake_pos"]):
            #     print("HIT OPP")
            #     winner = opponent_id
            #
            #     socketio.emit("game_over", {"winner": winner}, room=f"game:{game_id}", namespace="/one_vs_one")
            #
            #     game_state["winner"] = winner
            #     redis_client.hset(f"{redis_prefix}-games-one_vs_one", game_id, json.dumps(game_state))
            #
            #     game.save_game(game_id, game_mode)
            #     return
            #
            # # Check for collisions
            # if game.check_collision(new_pos):
            #     print("DIED")
            #
            #     winner = opponent_id
            #
            #     socketio.emit("game_over", {"winner": winner}, room=f"game:{game_id}", namespace="/one_vs_one")
            #
            #     game_state["winner"] = winner
            #     redis_client.hset(f"{redis_prefix}-games-one_vs_one", game_id, json.dumps(game_state))
            #
            #     game.save_game(game_id, game_mode)
            #     return

        if len(game_state["players"]) == 2:
            socketio.emit("snakes_pos", snakes_pos, room=f"game:{game_id}", namespace="/one_vs_one")

        if not game_state["food_pos"]:
            game_state["food_pos"] = game.generate_food_pos([player["snake_pos"] for player in game_state["players"].values()])
            print(game_state["food_pos"])
            socketio.emit("food_pos", game_state["food_pos"], room=f"game:{game_id}", namespace="/one_vs_one")

        redis_client.hset(f"{redis_prefix}-games-one_vs_one", game_id, json.dumps(game_state))


@socketio.on("connect", namespace="/one_vs_one")
def handle_connect_one_vs_one():
    """Handle new player connection."""
    if not session["logged_in"]:
        disconnect()
        return

    game_id = request.args.get("game_id")
    player_id = session["user_id"]

    game_state = redis_client.hget(f"{redis_prefix}-games-one_vs_one", game_id)

    if not game_state:
        print("GAME DOES NOT EXIST")
        session["game_id"] = None
        socketio.emit("game_not_exist", room=f"game:{game_id}", namespace="/one_vs_one")
        disconnect()
        return

    game_state = json.loads(game_state)

    if player_id not in game_state["players"]:
        print("NOT ALLOWED TO JOIN")
        disconnect()
        return
    if game_state["started"]:
        print("GAME HAS ALREADY STARTED")
        disconnect()
        return

    session["game_id"] = game_id

    join_room(f"game:{game_id}")
    join_room(f"{game_id}:{session['user_id']}")

    # Todo: Make better spawn positions
    y = random.randint(0, game.rows-1)
    spawn_position = [
        [3, y],
        [4, y],
        [5, y],
        [6, y],
        [7, y],
    ]

    player_id = session["user_id"]
    game_state["players"][player_id].update({
        "snake_pos": spawn_position,
        "prev_snake_pos": [],
        "snake_dir": "right",
        "score": 0,
        "ready": True
    })

    redis_client.hset(f"{redis_prefix}-games-one_vs_one", game_id, json.dumps(game_state))

    print(json.dumps(game_state, indent=4))

    # Start the game if all players are ready
    for player_id in game_state["players"]:
        if not game_state["players"][player_id]["ready"]:
            break
    else:
        threading.Thread(target=one_vs_one_game_loop, args=[game_id], daemon=True).start()

    # Todo: send info on opp and when the game starts
    emit("game_state", game_state, room=f"game:{game_id}")


@socketio.on("snake_dir", namespace="/one_vs_one")
def snake_dir(data):
    print(f"TOOK: {(time.time()-data['time'])*1000}")
    game_id = session["game_id"]
    game_state = json.loads(redis_client.hget(f"{redis_prefix}-games-one_vs_one", game_id))

    player_id = session["user_id"]
    direction = data["snake_dir"]

    game_state["players"][player_id]["snake_dir"] = direction

    redis_client.hset(f"{redis_prefix}-games-one_vs_one", game_id, json.dumps(game_state))


@socketio.on("disconnect", namespace="/one_vs_one")
def handle_disconnect():
    """Handle player disconnection."""
    game_id = session["game_id"]
    game_state = redis_client.hget(f"{redis_prefix}-games-one_vs_one", game_id)


    if game_state:
        game_state = json.loads(game_state)
        player_id = session["user_id"]

        if len(game_state["players"]) == 2:
            game_state["winner"] = next((user_id for user_id in game_state["players"].keys() if user_id != player_id), None)

        if player_id in game_state["players"]:
            del game_state["players"][player_id]
            redis_client.hset(f"{redis_prefix}-games-one_vs_one", game_id, json.dumps(game_state))
    session["game_id"] = None


@app.route("/clear_games", methods=["POST"])
def clear_games():
    redis_client.delete(f"{redis_prefix}-matchmaking-one_vs_one")
    redis_client.delete(f"{redis_prefix}-games-one_vs_one")

    return jsonify({
        "error": False,
        "message": "Cleared games"
    })


@socketio.on("connect", namespace="/matchmaking_one_vs_one")
def handle_connect_matchmaking_one_vs_one():
    try:
        game_mode = "one_vs_one"
        max_players = 2

        if not session["logged_in"]:
            disconnect()
            return jsonify({
                "error": True,
                "message": "Je moet ingelogd zijn om te kunnen spelen",
                "type": "general",
                "category": "error"
            }), 401

        # Make sure session["game_id"] is cleared after a user is done with a game so they can join a new match
        # Or remove player from current game and allow them to join a new match(safer for when a player's session isn't properly cleared)
        # Also need to handle user refreshing /matchmaking page(this would make them try to join a new game when they might already be in a game)(this won't be a problem I think though)
        game_id = session["game_id"]
        session["game_id"] = None
        player_id = session["user_id"]

        matchmaking_games = redis_client.hgetall(f"{redis_prefix}-matchmaking-one_vs_one")

        # Make this a function in game.py cause also need this in handle_disconnect_matchmaking_one_vs_one()
        if game_id:
            # Remove player from current game
            if game_id in matchmaking_games:
                game_state = json.loads(matchmaking_games[game_id])

                if player_id in game_state["players"]:
                    del game_state["players"][player_id]
                    redis_client.hset(f"{redis_prefix}-matchmaking-one_vs_one", game_id, json.dumps(game_state))


        for game_id in matchmaking_games.keys():
            game_state = json.loads(matchmaking_games[game_id])

            if game_state["game_mode"] == game_mode and len(game_state["players"]) < max_players:
                # Add player to game
                game_state["players"][player_id] = {
                    "username": session["username"],
                    "ready": False
                }
                redis_client.hset(f"{redis_prefix}-matchmaking-one_vs_one", game_id, json.dumps(game_state))

                # Let player know that found a match
                players = game_state["players"]

                emit("found_match", game_state)

                join_room(f"matchmaking:{game_id}")
                print("Joined a match: ", game_id)

                if len(game_state["players"]) == max_players:
                    # Let both players know that game can start(maybe add a 3 sec delay client side)
                    socketio.emit("game_start", {"game_id": game_id, "players": players}, room=f"matchmaking:{game_id}", namespace="/matchmaking_one_vs_one")
                    print("Match can start...")

                    game_state = copy.deepcopy(default_game_state) # Deep copy so it doesn't make changes to default state
                    game_state["players"] = players
                    game_state["game_mode"] = game_mode
                    redis_client.hset(f"{redis_prefix}-games-one_vs_one", game_id, json.dumps(game_state))
                break
        else:
            # Create new game
            game_id = str(uuid4())

            game_state = copy.deepcopy(default_matchmaking_game) # Deep copy so it doesn't make changes to default state
            game_state["game_mode"] = game_mode
            game_state["players"][player_id] = {
                "username": session["username"],
                "ready": False
            }

            # Save to Redis
            redis_client.hset(f"{redis_prefix}-matchmaking-one_vs_one", game_id, json.dumps(game_state))

            join_room(f"matchmaking:{game_id}")

            # Let client know to wait till other user joins
            emit("looking_for_players", "test")
            print("Created a match: ", game_id)

        # Maybe add delay before other people can join the match

        session["game_id"] = game_id
        print(matchmaking_games)

        return jsonify({
            "error": False,
            "message": "Game joinen was zeer succesvol"
        })
    except Exception as e:
        logger.error(f"handle_connect_matchmaking_one_vs_one(): {e}", exc_info=True)
        return jsonify({
            "error": True,
            "message": "Er is een probleem opgetreden tijdens de matchmaking",
            "category": "error",
            "type": "general",
        }), 500


@socketio.on("joining_game", namespace="/matchmaking_one_vs_one")
def joining_game_one_vs_one(data):
    try:
        session_game_id = session["game_id"]
        game_id = data["game_id"]
        player_id = session["user_id"]

        print("JOINING_GAME: ", game_id)

        if session_game_id != game_id:
            print("GAME IDS NOT SAME")
            disconnect()
            return

        # Remove player from current game if in one
        if game_id:
            game_state = json.loads(redis_client.hget(f"{redis_prefix}-matchmaking-one_vs_one", game_id))
            if game_state:
                if player_id in game_state["players"]:
                    print("DELLLLLLELTE")
                    del game_state["players"][player_id]
                    redis_client.hset(f"{redis_prefix}-matchmaking-one_vs_one", game_id, json.dumps(game_state))

        session["game_id"] = None
    except Exception as e:
        logger.error(f"joining_game_one_vs_one(): {e}", exc_info=True)
        return jsonify({
            "error": True,
            "message": "Er is een probleem opgetreden tijdens de matchmaking",
            "category": "error",
            "type": "general",
        }), 500


@socketio.on("disconnect", namespace="/matchmaking_one_vs_one")
def handle_disconnect_matchmaking_one_vs_one():
    try:
        game_id = session["game_id"]
        player_id = session["user_id"]
        print("DISCONNECTED")

        # Remove player from current game if in one
        if game_id:
            matchmaking_games = redis_client.hgetall(f"{redis_prefix}-matchmaking-one_vs_one")
            if matchmaking_games and game_id in matchmaking_games:
                print("PLAYER_LEFT")
                socketio.emit("player_left", {"player_id": player_id}, room=f"matchmaking:{game_id}",
                              namespace="/matchmaking_one_vs_one")

                game_state = json.loads(matchmaking_games[game_id])

                if player_id in game_state["players"]:
                    del game_state["players"][player_id]
                    redis_client.hset(f"{redis_prefix}-matchmaking-one_vs_one", game_id, json.dumps(game_state))

        session["game_id"] = None
    except Exception as e:
        logger.error(f"handle_disconnect_matchmaking_one_vs_one(): {e}", exc_info=True)
        return jsonify({
            "error": True,
            "message": "Er is een probleem opgetreden tijdens de matchmaking",
            "category": "error",
            "type": "general",
        }), 500


@app.route("/matchmaking", methods=["GET"])
def matchmaking_get():
    if not session["logged_in"]:
        flash("Je moet ingelogd zijn om te kunnen spelen", "error")
        return redirect("/")

    if not request.args.get("game_mode"):
        flash("Kon game mode niet vinden", "error")
        return redirect("/snake")

    game_mode = request.args["game_mode"]

    if game_mode not in game_modes:
        flash("Geen geldige game mode", "error")
        return redirect("/snake")
    print(game_mode)
    return render_template("matchmaking.html", game_mode=game_mode)


# End of multiplayer
# -------------------------------------------------------------------------


@app.before_request
def before_request():
    # if request.headers.get("User-Agent") != "Dev Flame" and request.headers.get("Cf-Connecting-Ip") not in config["ALLOWED_IPS"]:
    #     return "Wax Flame keurt uw aanwezigheid niet goed, <br><a href='https://youtu.be/WXrf_tedbAg'>Klik dan als je durft!</a>", 403

    session.setdefault("user_id", None)
    session.setdefault("username", None)
    session.setdefault("email", None)
    session.setdefault("hashed_password", None)
    session.setdefault("state", None)
    session.setdefault("logged_in", None)
    session.setdefault("highscore", None)
    session.setdefault("game_id", None)

    # session.permanent = True

    # Expire sessions
    if not session.get('created_at'):
        session['created_at'] = int(time.time())

    created_at = session['created_at']
    expire_at = created_at + app.config['PERMANENT_SESSION_LIFETIME'].total_seconds()

    redis_key = f"{app.config['SESSION_KEY_PREFIX']}{session.sid}"
    redis_client.expireat(redis_key, int(expire_at))


@app.route("/", methods=["GET"])
def home():
    if session["logged_in"]:
        return render_template("snake.html", username=session["username"])

    quote_data = random.choice(quotes)

    flash("Test", "success")

    return render_template("index.html", quote=quote_data["quote"], author=quote_data["author"])


@app.route("/snake", methods=["GET"])
def game_modes_get():
    if not session["logged_in"]:
        return redirect("/")

    return render_template("game_modes.html", username=session["username"])


@app.route("/snake/<game_mode>", methods=["GET"])
def game_mode_get(game_mode):
    if not session["logged_in"]:
        return redirect("/")

    if not os.path.isfile(f"{app.template_folder}/{game_mode}.html") or not game_modes:
        return redirect("/snake")

    return render_template(f"{game_mode}.html", username=session["username"])


@app.route("/js/<file_name>", methods=["GET"])
def js(file_name):
    return send_file(f"{app.static_folder}/js/{file_name}")


@app.route("/js/background/<file_name>", methods=["GET"])
def background_js(file_name):
    return send_file(f"{app.static_folder}/js/background/{file_name}")


@app.route("/styles", methods=["GET"])
def styles():
    return send_file(f"{app.static_folder}/styles.css")


@app.route("/icon/<file_name>", methods=["GET"])
def icon(file_name):
    return send_file(f"{app.static_folder}/icons/{file_name}")


@app.route("/img/<file_name>", methods=["GET"])
def img(file_name):
    return send_file(f"{app.static_folder}/images/{file_name}")


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    return send_file(f"{app.static_folder}/images/lars_met_hond.png")


@app.route('/motivational_quotes')
@cross_origin()
def get_quotes():
    return jsonify(motivational_quotes)


@app.route("/login", methods=["GET"])
def login_get():
    if session["logged_in"]:
        return redirect("/")

    return render_template("login.html")


@app.route("/login", methods=["POST"])
@limiter.limit("10 per 1 minute", key_func=get_user_or_session_key)
@limiter.limit("4 per 10 seconds", key_func=get_user_or_session_key)
def login_post():
    try:
        data = request.get_json()

        email = data["email"]
        password = data["password"]

        valid_password = login.valid_password(email, password)

        if valid_password["error"]:
            return jsonify({
                "error": True,
                "message": valid_password["message"],
                "type": valid_password["type"],
            }), valid_password["code"]

        user_id = valid_password["user_id"]
        username = valid_password["username"]

        session["email"] = email
        session["user_id"] = user_id
        session["username"] = username
        session["state"] = "logging_in"
        session["highscore"] = valid_password["highscore"]

        # Generate and send mfa code
        verification_code = mfa.generate_code(user_id, email)
        send_email.login_verification_email(verification_code, username, email)

        return jsonify({
            "error": False,
            "redirect": "/verify"
        })
    except KeyError:
        return jsonify({
            "error": True,
            "message": "Vul aub alle velden in",
            "category": "error",
            "type": "general",
        }), 400
    except Exception as e:
        logger.error(f"login_post(): {e}", exc_info=True)
        return jsonify({
            "error": True,
            "message": "Er is een probleem opgetreden tijdens het inloggen",
            "category": "error",
            "type": "general",
        }), 500


@app.route("/register", methods=["GET"])
def register_get():
    if session["logged_in"]:
        return redirect("/")

    return render_template("register.html")


@app.route("/register", methods=["POST"])
@limiter.limit("10 per 1 minute", key_func=get_user_or_session_key)
@limiter.limit("4 per 10 seconds", key_func=get_user_or_session_key)
def register_post():
    try:
        data = request.get_json()

        username = data["username"]
        email = data["email"]
        password = data["password"]

        # Validate user input
        if not register.is_valid_username(username):
            return jsonify({
                "error": True,
                "message": "Gebruikersnaam naam mag max 20 karakters lang zijn",
                "type": "username",
            }), 400
        valid_email = register.is_valid_email(email)
        if valid_email["error"]:
            return jsonify({
                "error": True,
                "message": valid_email["message"],
                "type": valid_email["type"],
            }), valid_email["code"]
        if not register.is_valid_password(password):
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
        session["username"] = data["username"]
        session["email"] = email
        session["state"] = "registering"

        # Generate and send mfa code
        verification_code = mfa.generate_code(user_id, email)
        send_email.register_verify_email(verification_code, data["username"], email)

        return jsonify({
            "error": False,
            "redirect": "/verify"
        })
    except KeyError:
        return jsonify({
            "error": True,
            "message": "Vul aub alle velden in",
            "category": "error",
            "type": "general",
        }), 400
    except Exception as e:
        logger.error(f"register_post(): {e}", exc_info=True)
        return jsonify({
            "error": True,
            "message": "Er is een probleem opgetreden tijdens het registeren",
            "category": "error",
            "type": "general",
        }), 500


@app.route("/verify", methods=["GET"])
def verify():
    valid_states = [
        "logging_in",
        "registering"
    ]

    if session["logged_in"] or session["state"] not in valid_states:
        return redirect("/")
    return render_template("verify.html")


@app.route("/verify", methods=["POST"])
@limiter.limit("4 per 10 seconds", key_func=get_user_or_session_key)
def verify_post():
    try:
        request_json = request.get_json()

        is_valid = mfa.is_valid_code(session["user_id"], request_json["code"], session["email"])

        if is_valid["id_valid"]:
            if session["state"] == "registering":
                hashed_password = session["hashed_password"]

                # Insert into db
                result = register.create_account(session["user_id"], session["username"], session["email"], hashed_password)
                response_code = result["code"]

                if response_code == 201:
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

            return jsonify({
                "error": False,
                "redirect": "/",
                "username": session["username"],
                "user_id": session["user_id"]
            }), response_code
        else:
            if is_valid["message"] == "Code expired":
                # Resend mfa code
                verification_code = mfa.generate_code(session["user_id"], session["email"])
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
    except KeyError:
        return jsonify({
            "error": True,
            "message": "Vul aub alle velden in",
            "category": "error",
            "type": "general",
        }), 400
    except Exception as e:
        logger.error(f"verify_post(): {e}", exc_info=True)
        return jsonify({
            "error": True,
            "message": "Er is een probleem opgetreden tijdens het verifiëren",
            "type": "general",
            "category": "error"
        }), 500


@app.route("/resend", methods=["GET"])
@limiter.limit("2 per 1 minute", key_func=get_user_or_session_key)
@limiter.limit("1 per 20 seconds", key_func=get_user_or_session_key)
def resend():
    try:
        if session["state"] == "logged_in":
            flash("Je bent al ingelogd", "success")
            return redirect("/")

        encrypted_code = redis_client.get(f"{redis_prefix}-mfa:{session['user_id']}")

        if not encrypted_code:
            verification_code = mfa.generate_code(session["user_id"], session["email"])
        else:
            verification_code = mfa.decrypt_mfa_code(encrypted_code, session["email"])

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
        logger.error(f"resend(): {e}", exc_info=True)

        flash("Er is een probleem opgetreden tijdens het versturen", "error")

        return redirect("/verify")


@app.route("/request_password_change", methods=["GET"])
def request_password_change_get():
    return render_template("request_password_change.html")


@app.route("/request_password_change", methods=["POST"])
@limiter.limit("10 per 10 minute", key_func=get_user_or_session_key)
@limiter.limit("4 per 10 seconds", key_func=get_user_or_session_key)
def request_password_change_post():
    try:
        email = request.get_json()["email"]

        token = str(uuid4().hex)

        salt = bcrypt.gensalt(config["BCRYPT_SALT_STRENGTH"])
        hashed_token = bcrypt.hashpw(token.encode(), salt)

        time_created = time.time()

        con = main.connect_to_db()
        cur = con.cursor()

        # Check if email exists and fetch user_id
        cur.execute("SELECT user_id, username FROM users WHERE email = %s", (email,))

        result = cur.fetchone()
        if not result:
            return jsonify({
                "error": True,
                "message": "Geen account met dat email",
                "type": "email"
            }), 400

        user_id = result[0]
        username = result[1]

        cur.execute("DELETE FROM change_password WHERE user_id = %s", (user_id,))
        con.commit()

        cur.execute("INSERT INTO change_password VALUES (%s, %s, %s)", (user_id, hashed_token, time_created,))
        con.commit()

        cur.close()
        con.close()

        send_email.change_password(user_id, token, username, email)

        return jsonify({
            "error": False
        }), 200
    except KeyError:
        return jsonify({
            "error": True,
            "message": "Vul aub alle velden in",
            "category": "error",
            "type": "general",
        }), 400
    except Exception as e:
        logger.error(f"request_password_change_post(): {e}", exc_info=True)
        return jsonify({
            "error": True,
            "message": "Er is een probleem opgetreden tijdens je aanvraag",
            "type": "general",
            "category": "error"
        }), 500


@app.route("/change_password", methods=["GET"])
def change_password_get():
    return render_template("change_password.html")


@app.route("/change_password", methods=["POST"])
@limiter.limit("4 per 10 seconds", key_func=get_user_or_session_key)
def change_password_post():
    try:
        request_json = request.get_json()

        user_id = request_json["user_id"]
        token = request_json["token"]
        password = request_json["password"]

        if not register.is_valid_password(password):
            return jsonify({
                "error": True,
                "message": "Wachtwoord is niet sterk genoeg",
                "type": "password",
            }), 400

        con = main.connect_to_db()
        cur = con.cursor()

        cur.execute("SELECT token, created_at FROM change_password WHERE user_id = %s", (user_id,))
        result = cur.fetchone()

        cur.close()
        con.close()

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

        if time.time() > exp + config["CHANGE_PASSWORD_EXP"]:
            return jsonify({
                "error": True,
                "message": "Wachtwoord wijzigen verlopen",
                "type": "general",
                "category": "error"
            }), 410

        salt = bcrypt.gensalt(config["BCRYPT_SALT_STRENGTH"])
        hashed_password = bcrypt.hashpw(password.encode(), salt)

        con = main.connect_to_db()
        cur = con.cursor()

        cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, user_id,))
        con.commit()

        cur.close()
        con.close()

        flash("Wachtwoord gewijzigd", "success")
        return jsonify({
            "error": False,
            "redirect": "/login"
        })
    except KeyError:
        return jsonify({
            "error": True,
            "message": "Vul aub alle velden in",
            "category": "error",
            "type": "general",
        }), 400
    except Exception as e:
        logger.error(f"change_password_post(): {e}", exc_info=True)
        return jsonify({
            "error": True,
            "message": "Er is een probleem opgetreden tijdens het wijzigen van je wachtwoord",
            "type": "general",
            "category": "error"
        }), 500


@app.route("/logout", methods=["GET"])
def log_out():
    redis_client.delete(f"{redis_prefix}-session:{session.sid}")
    session.clear()
    return redirect("/")


# Redirects
# -------------------------------------------------------------------


@app.route("/doneer", methods=["GET"])
def go_fund_me():
    return redirect("https://gofundme.com/larsvlaar")


@app.route("/of", methods=["GET"])
def of():
    return redirect("https://of.com/larsvlaar")


# End of redirects
# -------------------------------------------------------------------


if __name__ == '__main__':
    # app.run("0.0.0.0", port=8004, debug=True)

    socketio.run(app, host='0.0.0.0', port=port, debug=True)

    # socketio.run(app, "0.0.0.0", port=8004, debug=True)
