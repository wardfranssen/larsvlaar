from flask_socketio import join_room, Namespace, emit
from src.snake.wrapper_funcs import *
from src.snake.app import socketio
from bs4 import BeautifulSoup
from src.snake.main import *
from flask import Blueprint
import random
import re

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

# Todo: Add more
random_messages = [
    "I don\\'t like the juice",
    "RON JANS",
    "Ik ben racistisch",
    "maar guys ff yusu, ik ben gay",
    "Ik hou van geoliede mannen",
    "Recentelijk heeft Lars Vlaar de 130kg gehaald, hiermee is hij officieel morbide obees, wat een hele prestatie is, maar om dit gewicht vast te houden moet Lars veel eten kopen en dat heeft een hoge prijs. <a href=\"/doneer\">Doneer NU!</a>",
    "<a href=\"/of\">Klik voor GRATIS Voetenfoto\\'s</a>"
]


def replacer(match):
    original = match.group(0)
    return f"<span class='special-word'>{original}</span>"

def sanitize_message(message: str):
    allowed_tags = {"i", "small", "b", "u", "strong", "em", "abbr", "img", "button", "h1", "h2", "h3", "a", "span"}
    allowed_css_properties = {
        "color", "background-color", "font-weight",
        "font-style", "text-decoration", "text-align",
        "letter-spacing", "text-shadow", "cursor"
    }

    soup = BeautifulSoup(message, "html.parser")

    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.decompose()
            continue

        for attr in list(tag.attrs):
            if attr == "onclick":
                tag["onclick"] = "larsVlaar();"
            elif attr.startswith("on"):
                del tag[attr]
            elif attr == "style":
                # Sanitize CSS
                safe_styles = []
                for style in tag["style"].split(";"):
                    if ":" in style:
                        prop, value = style.split(":", 1)
                        prop = prop.strip().lower()
                        value = value.strip()

                        if prop in allowed_css_properties:
                            safe_styles.append(f"{prop}:{value}")

                new_style = ""
                if safe_styles:
                    new_style = ";".join(safe_styles)
                tag["style"] =  new_style
                if not tag["style"]:
                    del tag["style"]
            elif attr == "class":
                if tag["class"] != "special-word":
                    del tag[attr]
            elif attr == "id":
                del tag[attr]

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src.startswith("/img/") and not ((src.startswith("/api/users") or "larsvlaar.nl/api/users" in src) and "/pfp" in src):
            img["src"] = "/img/jon_rans.png"

        img["style"] = "max-height: 150px; height: auto;"

    for button in soup.find_all("button"):
        button["onclick"] = f"chatSocket.emit('send_message', '{random.choice(random_messages)}');"
        button["style"] = "background-color: #c7c7c7; width: 100px; border-radius: 15px;"

    for a in soup.find_all("a"):
        a["target"] = "_blank"

    for _input in soup.find_all("input"):
        _input["disabled"] = True
        _input["placeholder"] = "RON JANS"

    return str(soup)


def get_chat_id(game_id: str=None, lobby_id: str=None):
    if game_id:
        game = redis_client.hget(f"{redis_prefix}:games:custom", game_id)
        if not game:
            return {
                "error": True
            }
        game = json.loads(game)

        allowed_to_join = list(game["players"].keys())
        chat_id = game["chat_id"]
    elif lobby_id:
        lobby = redis_client.get(f"{redis_prefix}:lobbies:{lobby_id}")
        if not lobby:
            return {
                "error": True
            }
        lobby = json.loads(lobby)

        allowed_to_join = list(lobby["players"].keys())
        chat_id = lobby["chat_id"]
    else:
        return {
            "error": True
        }
    return {
        "error": False,
        "allowed_to_join": allowed_to_join,
        "chat_id": chat_id
    }


@chat_bp.get("/history")
@login_required()
@wrap_errors()
def chat_history():
    game_id = request.args.get("game_id")
    lobby_id = request.args.get("lobby_id")
    user_id = session["user_id"]

    result = get_chat_id(game_id, lobby_id)

    if result["error"]:
        return jsonify({
            "error": True,
            "message": "Chat bestaat niet",
            "type": "general",
            "category": "error"
        })
    allowed_to_join = result["allowed_to_join"]
    chat_id = result["chat_id"]

    if user_id not in allowed_to_join:
        return jsonify({
            "error": True,
            "message": "Niet genoeg rechten",
            "type": "general",
            "category": "error"
        })

    messages = redis_client.lrange(f"{redis_prefix}:chat:{chat_id}:messages", 0, -1)
    parsed_messages = [json.loads(m) for m in messages]

    return jsonify({
        "error": False,
        "messages": parsed_messages
    })


class ChatNamespace(Namespace):
    @login_required()
    def on_connect(self):
        game_id = request.args.get("game_id")
        lobby_id = request.args.get("lobby_id")
        user_id = session["user_id"]

        result = get_chat_id(game_id, lobby_id)
        if result["error"]:
            disconnect()
            return
        allowed_to_join = result["allowed_to_join"]
        chat_id = result["chat_id"]

        if user_id not in allowed_to_join:
            disconnect()
            return

        join_room(f"chat:{chat_id}")

        message_data = {
            "exp": None
        }

        if game_id:
            message_data["message"] = f"{session["username"]} is in de game gekomen"
        else:
            message_data["message"] = f"{session["username"]} is in de lobby gekomen"


        socketio.emit("server_message", message_data, room=f"chat:{chat_id}", namespace="/ws/chat")
        redis_client.lpush(f"{redis_prefix}:chat:{chat_id}:messages", json.dumps(message_data))


    def on_send_message(self, data):
        if not data or not str(data).strip():
            return

        game_id = request.args.get("game_id")
        lobby_id = request.args.get("lobby_id")
        user_id = session["user_id"]

        # Rate limit
        now = int(time.time())
        last_message = redis_client.get(f"{redis_prefix}:user:{user_id}:last_message")
        if last_message and now - int(last_message) < 1:
            message_data = {
                "message": "Rustig aan jij!",
                "exp": 1.5
            }
            emit("server_message", message_data)
            return

        result = get_chat_id(game_id, lobby_id)
        if result["error"]:
            disconnect()
            return
        chat_id = result["chat_id"]

        message = sanitize_message(data)

        message_words = message.split(" ")
        better_message = []

        for i, word in enumerate(message_words):
            if word.lower().endswith("on"):
                if i + 1 < len(message_words) and message_words[i + 1].lower().startswith("jans"):
                    better_message.append(word)
                else:
                    better_message.append(word.replace("on", "on Jans"))
            else:
                better_message.append(word)

        better_message = " ".join(better_message)

        for word in config["SPECIAL_CHAT_WORDS"]:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            better_message = pattern.sub(replacer, better_message)

        message_data = {
            "username": session["username"],
            "message": better_message,
            "timestamp": int(time.time())
        }

        redis_client.set(f"{redis_prefix}:user:{user_id}:last_message", now)
        redis_client.lpush(f"{redis_prefix}:chat:{chat_id}:messages", json.dumps(message_data))

        socketio.emit("message_received", message_data, room=f"chat:{chat_id}", namespace="/ws/chat")


    def on_disconnect(self, message):
        game_id = request.args.get("game_id")
        lobby_id = request.args.get("lobby_id")

        result = get_chat_id(game_id, lobby_id)

        if result["error"]:
            disconnect()
            return
        chat_id = result["chat_id"]

        message_data = {
            "message": f"{session["username"]} is melk gaan halen",
            "exp": None
        }

        socketio.emit("server_message", message_data, room=f"chat:{chat_id}", namespace="/ws/chat")
        redis_client.lpush(f"{redis_prefix}:chat:{chat_id}:messages", json.dumps(message_data))



