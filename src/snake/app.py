import eventlet
eventlet.monkey_patch()

import sys
sys.path.append("../../snake/src")

from flask_socketio import SocketIO, emit, join_room, Namespace
from werkzeug.middleware.proxy_fix import ProxyFix
from src.snake.mfa import encrypt_mfa_code
from src.snake.wrapper_funcs import *
from flask import Flask, send_file
from flask_session import Session
from flask_limiter import Limiter
from datetime import timedelta
from src.snake.main import *
from copy import deepcopy
from uuid import uuid4
import secrets
import base64
import psutil
import random
import json
import time
import os

redis_prefix = config["REDIS"]["PREFIX"]

app = Flask(__name__, template_folder="../../templates/snake", static_folder="../../static/snake")

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_NAME='flask_sid',
    SECRET_KEY=config["SECRET_KEY"],
    SESSION_TYPE="redis",
    SESSION_KEY_PREFIX=f"{redis_prefix}:session:",
    SESSION_REDIS=redis_client,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=config["SESSION_TTL"]),
    SESSION_PERMANENT=True,
    SESSION_SERIALIZATION_FORMAT="json",
    MAX_CONTENT_LENGTH=350 * 1024 # 350kB Upload limit
)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

Session(app)

socketio = SocketIO(
    app,
    manage_session=False,
    message_queue=f'redis://:{config["REDIS"]["PASSWORD"]}@{config["REDIS"]["HOST"]}:{config["REDIS"]["PORT"]}/{config["REDIS"]["DB"]}',
    cors_allowed_origins=["https://dev.larsvlaar.nl"],
    ping_interval=25,
    ping_timeout=60,
    # engineio_logger=True,
    # logger=True,
    async_mode='eventlet',
    cookie=None,
    allow_upgrades=True,
    http_compression=True,
    always_connect=False
)

logger = main.logger

quotes = json.loads(open(f"{app.static_folder}/quotes.json").read())

def get_user_or_session_key():
    if session.get("user_id"):
        return f"user:{session["user_id"]}"
    return f"session:{session.sid}"


limiter = Limiter(
    get_user_or_session_key,
    app=app,
    storage_uri=f"redis://{config['REDIS']['HOST']}:{config['REDIS']['PORT']}",
    storage_options={"password": config["REDIS"]["PASSWORD"]}
)


# Todo: Make func like this for general messages (e.g. being kicked from lobby/custom game or logged out cause someone else logged in)
# Todo: Make this a wrapper function
def get_pending_invites(user_id: str) -> dict:
    try:
        invites = {}
        invite_types = [
            "received",
            "sent"
        ]

        for invite_type in invite_types:
            invites_ids = redis_client.smembers(f"{redis_prefix}:user:{user_id}:invites:{invite_type}")
            invites[invite_type] = []

            for invite_id in invites_ids:
                invite = redis_client.getex(f"{redis_prefix}:invite:{invite_id}")

                if not invite:
                    redis_client.srem(f"{redis_prefix}:user:{user_id}:invites:{invite_type}", invite_id)
                    continue

                invite = json.loads(invite)
                created_at = invite["created_at"]

                if int(time.time()) - created_at > 13:
                    redis_client.srem(f"{redis_prefix}:user:{user_id}:invites:{invite_type}", invite_id)
                    continue

                if invite_type == "received":
                    user = "from"
                else:
                    user = "to"

                _user_id = invite[user]
                invite_data = {
                    "invite_id": invite_id,
                    f"{user}_username": get_username(_user_id),
                    f"{user}_user_id": _user_id,
                    f"{user}_pfp_version": get_pfp_version(_user_id),
                    "game_mode": invite["game_mode"],
                    "lobby_id": invite["lobby_id"],
                    "created_at": created_at,
                }
                invites[invite_type].append(invite_data)
        return {
            "server_time": int(time.time()),
            "invites": invites
        }
    except Exception as e:
        logger.error(f"get_pending_invites() for {user_id}: {e}", exc_info=True)
        return {
            "server_time": int(time.time()),
            "invites": []
        }


def reset_metrics():
    while True:
        for endpoint in redis_client.smembers(f"{redis_prefix}:metrics:endpoints"):
            total_request = redis_client.get(f"{redis_prefix}:metrics:requests:{endpoint}")

            redis_client.set(f"{redis_prefix}:metrics:requests:{endpoint}", 0)

            redis_client.incr(f"{redis_prefix}:metrics:total_requests:{endpoint}", total_request)
        redis_client.set(f"{redis_prefix}:metrics:start_time", time.time())
        time.sleep(60)  # Reset every minute


@app.before_request
def before_request():
    if request.headers.get("User-Agent") not in config["ALLOWED_USER_AGENTS"] and request.headers.get("Cf-Connecting-Ip") not in config["ALLOWED_IPS"]:
        return redirect("https://test.larsvlaar.nl")

    # Todo: Keep track of rps/session

    session.setdefault("user_id", None)
    session.setdefault("username", None)
    session.setdefault("email", None)
    session.setdefault("hashed_password", None)
    session.setdefault("state", None)
    session.setdefault("logged_in", None)
    session.setdefault("highscore", None)
    session.setdefault("game_id", None)

    # Expire sessions
    if not session.get("created_at"):
        session["created_at"] = int(time.time())

    created_at = session["created_at"]
    expire_at = created_at + app.config['PERMANENT_SESSION_LIFETIME'].total_seconds()

    redis_client.expireat(f"{app.config['SESSION_KEY_PREFIX']}{session.sid}", int(expire_at))

    if request.path != '/monitoring':
        redis_client.incr(f"{redis_prefix}:metrics:requests:{request.path}")
        redis_client.sadd(f"{redis_prefix}:metrics:endpoints", request.path)


@app.get("/monitoring")
@login_required()
def monitoring():
    # Get request counts
    endpoint_stats = {}
    total_requests = 0
    all_time_total_requests = 0

    start_time = float(redis_client.get(f"{redis_prefix}:metrics:start_time"))
    # Time passed since last metrics reset
    time_passed = int(time.time() - start_time)
    if time_passed == 0:
        time_passed = 1

    for endpoint in redis_client.smembers(f"{redis_prefix}:metrics:endpoints"):
        count = redis_client.get(f"{redis_prefix}:metrics:requests:{endpoint}")

        if count:
            count = int(count)
            total_requests += count

            all_time_total = redis_client.get(f"{redis_prefix}:metrics:total_requests:{endpoint}")
            if not all_time_total:
                all_time_total = 0
            all_time_total = int(all_time_total)

            all_time_total_requests += all_time_total

            endpoint_stats[endpoint] = {
                "rps": count / time_passed,
                "total": count,
                "all_time_total": all_time_total
            }

    # Todo: Get active games
    # Todo: Get requests past hour and day and so on
    return jsonify({
        "endpoints": endpoint_stats,
        "system": {
            "memory": psutil.Process().memory_info().rss,
            "cpu": psutil.cpu_percent()
        },
        "total_rps": total_requests / time_passed,
        "all_time_total_requests": all_time_total_requests
    })


class SpectateNamespace(Namespace):
    @login_required()
    def on_connect(self):
        game_id = request.args.get("game_id")
        game_mode = redis_client.getex(f"{redis_prefix}:game_mode:{game_id}")

        if not game_mode:
            print("Game mode not found")
            disconnect()
            return

        game_state = redis_client.hget(f"{redis_prefix}:games:{game_mode}", game_id)

        if not game_state:
            flash("Game is al afgelopen")
            emit("game_not_exist")
            return
        game_state = json.loads(game_state)

        # Only works for 1v1
        player1_id = list(game_state["players"].keys())[0]
        player2_id = list(game_state["players"].keys())[1]

        game_settings = {
            "players": {
                player1_id: game_state["players"][player1_id]["username"],
                player2_id: game_state["players"][player2_id]["username"]
            },
            "settings": {
                "board": game_state["board"]
            }
        }

        join_room(f"spectate:{game_id}")
        emit("game_settings", game_settings)


    def on_disconnect(self, message):
        print(f"Spectate on_disconnect(): {message}")


@app.get("/matchmaking")
@login_required(redirect_to="/")
def matchmaking_get():
    game_mode = request.args.get("game_mode")
    if not game_mode:
        flash("Kon game mode niet vinden", "error")
        return redirect("/snake")


    if game_mode not in game_modes:
        flash("Geen geldige game mode", "error")
        return redirect("/snake")

    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    return render_template("matchmaking.html", game_mode=game_mode, invites=invites)


@app.get("/lobby/create")
@limiter.limit("10 per 1 minute", key_func=get_user_or_session_key)
@login_required(redirect_to="/")
def create_lobby():
    user_id = session["user_id"]
    lobby_id = str(uuid4())

    want_het_is_zo_belangrijk_want_we_denken_dat_iedereen_genoeg_te_eten_heeft_dat_is_gewoon_dit_zo = secrets.choice(boodschappen_lijstje)
    secret = secrets.token_hex()

    join_token = base64.b64encode(encrypt_mfa_code(want_het_is_zo_belangrijk_want_we_denken_dat_iedereen_genoeg_te_eten_heeft_dat_is_gewoon_dit_zo, secret).encode()).decode()[:6]
    join_token_exists = redis_client.exists(f"{redis_prefix}:join_token:{join_token}")

    while join_token_exists:
        secret = secrets.token_hex()
        join_token = base64.b64encode(encrypt_mfa_code(want_het_is_zo_belangrijk_want_we_denken_dat_iedereen_genoeg_te_eten_heeft_dat_is_gewoon_dit_zo, secret).encode()).decode()[:6]
        join_token_exists = redis_client.exists(f"{redis_prefix}:join_token:{join_token}")

    lobby_state = deepcopy(default_lobby_state)
    lobby_state.update({
        "owner": user_id,
        "allowed_to_join": [user_id],
        "players": {
            user_id: {
                "username": session["username"],
                "pfp_version": session["pfp_version"],
                "owner": True
            }
        },
        "join_token": join_token
    })

    redis_client.set(f"{redis_prefix}:lobbies:{lobby_id}", json.dumps(lobby_state), 30)
    redis_client.set(f"{redis_prefix}:join_token:{join_token}", lobby_id, 30)

    return redirect(f"/lobby/{lobby_id}")


@app.get("/lobby/<lobby_id>")
@login_required(redirect_to="/")
def join_lobby(lobby_id):
    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    lobby = redis_client.get(f"{redis_prefix}:lobbies:{lobby_id}")
    if not lobby:
        flash("Lobby bestaat niet of is verlopen", "error")
        return redirect("/snake")
    lobby = json.loads(lobby)
    if user_id not in lobby["allowed_to_join"]:
        flash("Je hebt geen toestemming om deze lobby te joinen", "error")
        return redirect("/snake")

    join_token = lobby["join_token"]

    return render_template("create_custom_game.html", user_id=session["user_id"], username=session["username"], pfp_version=session["pfp_version"], invites=invites, join_token=join_token)


@app.post("/api/feedback")
@limiter.limit("1 per 1 minute", key_func=get_user_or_session_key)
@wrap_errors()
@login_required()
@db_connection()
def kritiek(con, cur):
    kritiek = str(request.get_json()["kritiek"])

    if len(kritiek) < 10:
        return jsonify({
            "error": True,
            "message": "Feedback is te kort",
            "type": "feedback"
        })

    user_id = session["user_id"]
    created_at = int(time.time())

    cur.execute("INSERT INTO kritiek VALUES(%s, %s, %s)", (user_id, kritiek, created_at))
    con.commit()

    return jsonify({
        "error": False,
        "message": "Kritiek is verstuurt",
        "type": "general",
        "category": "success"
    })


@app.post("/clear_games")
def clear_games():
    redis_client.delete(f"{redis_prefix}:matchmaking:one_vs_one")
    redis_client.delete(f"{redis_prefix}:games:one_vs_one")

    return jsonify({
        "error": False,
        "message": "Cleared games"
    })


class NotificationsNamespace(Namespace):
    @login_required()
    def on_connect(self):
        user_id = session.get("user_id")
        join_room(f"notifications:{user_id}")

        redis_client.set(f"{redis_prefix}:notifications:connected:{user_id}", 1)

        redis_client.set(f"{redis_prefix}:active:{user_id}", 1, ex=60)
        redis_client.set(f"{redis_prefix}:online:{user_id}", 1, ex=15)

        socketio.start_background_task(self.heartbeat, user_id)


    def heartbeat(self, user_id: str):
        is_connected = redis_client.exists(f"{redis_prefix}:notifications:connected:{user_id}")
        while is_connected:
            redis_client.expire(f"{redis_prefix}:online:{user_id}", 15)
            time.sleep(10)
            is_connected = redis_client.exists(f"{redis_prefix}:notifications:connected:{user_id}")


    def on_activity(self):
        user_id = session.get("user_id")
        redis_client.set(f"{redis_prefix}:active:{user_id}", 1, ex=60)


    def on_disconnect(self, message):
        user_id = session.get("user_id")

        socketio.close_room(f"notifications:{user_id}")

        redis_client.setex(f"{redis_prefix}:notifications:connected:{user_id}", 3, 1)
        redis_client.expire(f"{redis_prefix}:online:{user_id}", 3)


@app.get("/spectate/<game_id>")
@login_required()
def spectate(game_id):
    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    return render_template("spectate.html", user_id=session["user_id"], username=session["username"], pfp_version=session["pfp_version"], invites=invites)


@app.get("/")
def home():
    if session["logged_in"]:
        return redirect("/snake")

    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    quote_data = random.choice(quotes)
    return render_template("index.html", quote=quote_data["quote"], author=quote_data["author"], invites=invites)


@app.get("/games_history/<user_id>")
@login_required(redirect_to="/")
def games_history_get(user_id):
    username = main.get_username(user_id)
    pfp_version = main.get_pfp_version(user_id)

    if not username:
        return redirect("/404")

    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    # Todo: Separate current user and user that's being fetched
    return render_template("games_history.html", user_id=user_id, username=username, pfp_version=pfp_version, invites=invites)


@app.get("/replay/<game_id>")
@login_required(redirect_to="/")
def replay_get(game_id):
    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    return render_template("replay.html", username=session["username"], user_id=session["user_id"], pfp_version=session["pfp_version"], invites=invites)


@app.get("/leaderboard")
@login_required(redirect_to="/")
def leaderboard_get():
    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    return render_template("leaderboard.html", username=session["username"], user_id=session["user_id"], pfp_version=session["pfp_version"], invites=invites)



@app.get("/snake")
@login_required(redirect_to="/")
def game_modes_get():
    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    return render_template("game_modes.html", username=session["username"], user_id=session["user_id"], pfp_version=session["pfp_version"], invites=invites)


@app.get("/snake/<game_mode>")
@login_required(redirect_to="/")
def game_mode_get(game_mode):
    if not os.path.isfile(f"templates/snake/{game_mode}.html") or game_mode not in game_modes:
        print("NO TEMPLATE")
        return redirect("/snake")

    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    return render_template(f"{game_mode}.html", username=session["username"], user_id=session["user_id"], pfp_version=session["pfp_version"], invites=invites)


@app.get("/settings")
@login_required(redirect_to="/")
def settings_get():
    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    return render_template("settings.html", username=session["username"], user_id=session["user_id"], pfp_version=session["pfp_version"], invites=invites)


@app.get("/profile/<user_id>")
@login_required(redirect_to="/")
@wrap_errors()
def profile_get(user_id):
    profile_user_id = user_id
    profile_username = main.get_username(profile_user_id)
    profile_pfp_version = main.get_pfp_version(profile_user_id)

    if not profile_username:
        return redirect("/404")

    user_id = session["user_id"]
    username = session["username"]
    pfp_version = session["pfp_version"]
    invites = get_pending_invites(user_id)

    return render_template("profile.html",
        profile_username=profile_username,
        profile_user_id=profile_user_id,
        profile_pfp_version=profile_pfp_version,
        user_id=user_id,
        username=username,
        pfp_version=pfp_version,
        invites=invites
   )


@app.get("/test")
def test_page():
    return render_template("test.html", user_id=session["user_id"], username=session["username"], pfp_version=session["pfp_version"])


@app.get("/friends")
@login_required(redirect_to="/")
def friends_get():
    user_id = session["user_id"]
    invites = get_pending_invites(user_id)

    return render_template("friends.html", user_id=user_id, username=session["username"], pfp_version=session["pfp_version"], invites=invites)


@app.get("/js/<file_name>")
def js(file_name):
    if not os.path.isfile(f"{app.static_folder}/js/{file_name}"):
        return render_template("404.html"), 404
    return send_file(f"{app.static_folder}/js/{file_name}")


@app.get("/styles")
def styles():
    return send_file(f"{app.static_folder}/styles.css")


@app.get("/icon/<file_name>")
def icon(file_name):
    if not os.path.isfile(f"{app.static_folder}/icons/{file_name}"):
        return render_template("404.html"), 404
    return send_file(f"{app.static_folder}/icons/{file_name}")


@app.get("/img/<file_name>")
def img(file_name):
    if not os.path.isfile(f"{app.static_folder}/images/{file_name}"):
        return render_template("404.html"), 404
    return send_file(f"{app.static_folder}/images/{file_name}")


@app.get("/favicon.ico")
def favicon():
    return send_file(f"{app.static_folder}/images/lars_met_hond.png")


@app.get("/login")
def login_get():
    if session["logged_in"]:
        return redirect("/")

    return render_template("login.html")


@app.get("/register")
def register_get():
    if session["logged_in"]:
        return redirect("/")

    return render_template("register.html")


@app.get("/verify")
def verify():
    valid_states = [
        "logging_in",
        "registering"
    ]

    if session["logged_in"] or session["state"] not in valid_states:
        return redirect("/")
    return render_template("verify.html")


@app.get("/request_password_change")
def request_password_change_get():
    return render_template("request_password_change.html")


@app.get("/change_password")
def change_password_get():
    return render_template("change_password.html")


# Redirects
# -------------------------------------------------------------------


@app.get("/doneer")
def go_fund_me():
    return redirect("https://gofundme.com/larsvlaar")


@app.get("/of")
def of():
    return redirect("https://of.com/larsvlaar")


# End of redirects
# -------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(429)
def rate_limited(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({
            "error": True,
            "message": "Wow, niet zo snel",
            "type": "general",
            "category": "error"
        }), 429
    else:
    # Redirect to login page, optionally with next URL
        flash("Wow, niet zo snel", "error")
        return redirect("/")


# Comment this out in prod(no if statement)
if __name__ == '__main__':
    from src.snake.api import register_routes
    from src.snake.api.one_vs_one import OneVsOneNamespace, MatchmakingOneVsOneNamespace
    from src.snake.api.custom import CustomNamespace
    from src.snake.api.lobby import LobbyNamespace, default_lobby_state

    register_routes(app)
    socketio.on_namespace(OneVsOneNamespace("/ws/one_vs_one/game"))
    socketio.on_namespace(MatchmakingOneVsOneNamespace("/ws/one_vs_one/matchmaking"))
    socketio.on_namespace(CustomNamespace("/ws/custom/game"))
    socketio.on_namespace(LobbyNamespace("/ws/lobby"))
    socketio.on_namespace(NotificationsNamespace("/ws/notifications"))
    socketio.on_namespace(SpectateNamespace("/ws/spectate"))

    socketio.start_background_task(reset_metrics)

    # Comment this out in prod
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)

