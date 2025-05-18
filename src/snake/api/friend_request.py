from src.snake.wrapper_funcs import *
from src.snake.app import socketio
from src.snake.friends import *
from flask import Blueprint
from src.snake import main
from uuid import uuid4
import time

friend_request_bp = Blueprint("friend_request", __name__, url_prefix="/api/friend_request")
redis_client = main.redis_client
redis_prefix = main.redis_prefix


@friend_request_bp.get("/received")
@login_required()
@wrap_errors()
@db_connection()
def received_friend_requests_get(con, cur):
    user_id = session["user_id"]

    cur.execute("SELECT from_user_id, created_at FROM friend_requests WHERE to_user_id = %s", (user_id,))
    users = cur.fetchall()

    friend_requests = parse_friend_requests(users)

    return jsonify({
        "error": False,
        "friend_requests": friend_requests
    })


@friend_request_bp.get("/sent")
@login_required()
@wrap_errors()
@db_connection()
def sent_friend_requests_get(con, cur):
    user_id = session["user_id"]

    cur.execute("SELECT to_user_id, created_at FROM friend_requests WHERE from_user_id = %s", (user_id,))
    users = cur.fetchall()

    friend_requests = parse_friend_requests(users)

    return jsonify({
        "error": False,
        "friend_requests": friend_requests
    })


@friend_request_bp.post("/<from_user_id>/reject")
@login_required()
@wrap_errors()
def reject_friend_request_post(from_user_id: str):
    to_user_id = session["user_id"]

    result = remove_friend_request(from_user_id, to_user_id)
    if result["error"]:
        return jsonify({
            "error": True,
            "message": result["message"],
            "category": result["category"],
            "type": result["type"],
        }), 400

    to_user_username = main.get_user_info("username", to_user_id)

    data = {
        "username": to_user_username
    }
    socketio.emit("friend_request_rejected", data, room=f"notifications:{from_user_id}", namespace="/ws/notifications")

    return jsonify({
        "error": False,
        "message": "Jammer, geen nieuwe vriend",
        "type": "general",
        "category": "success"
    }), 201


@friend_request_bp.post("/<to_user_id>/send")
@login_required()
@wrap_errors()
@db_connection()
def send_friend_request_post(con, cur, to_user_id: str):
    from_user_id = session["user_id"]

    if to_user_id == from_user_id:
        return jsonify({
            "error": True,
            "message": "Je beste vriend ben jezelf",
            "type": "general",
            "category": "error"
        }), 400

    has_friend_request = has_friend_request_from_user(to_user_id, from_user_id)
    if has_friend_request:
        return jsonify({
            "error": True,
            "message": "Je hebt al een vriendschapsverzoek van deze speler ontvangen",
            "type": "general",
            "category": "error"
        }), 400

    cur.execute("SELECT id FROM friend_requests WHERE from_user_id = %s AND to_user_id = %s LIMIT 1",
                (from_user_id, to_user_id))
    result = cur.fetchone()

    if result:
        return jsonify({
            "error": True,
            "message": "Je hebt al een vriendschapsverzoek verstuurd naar deze speler",
            "type": "general",
            "category": "error"
        }), 400

    is_friend = are_already_friends(from_user_id, to_user_id)
    if is_friend:
        return jsonify({
            "error": True,
            "message": "Dit is al je vriend",
            "type": "general",
            "category": "error"
        }), 400

    id = str(uuid4())
    created_at = int(time.time())

    cur.execute("INSERT INTO friend_requests VALUES (%s, %s, %s, %s)", (id, from_user_id, to_user_id, created_at))

    from_username = main.get_user_info("username", from_user_id)
    pfp_version = int(main.get_user_info("pfp_version", from_user_id))

    data = {
        "user_id": from_user_id,
        "username": from_username,
        "pfp_version": pfp_version
    }
    socketio.emit("received_friend_request", data, room=f"notifications:{to_user_id}", namespace="/ws/notifications")

    return jsonify({
        "error": False,
        "message": "Vriendschapsverzoek verstuurd",
        "type": "general",
        "category": "success"
    }), 201


@friend_request_bp.post("/<from_user_id>/accept")
@login_required()
@wrap_errors()
@db_connection()
def accept_friend_request_post(con, cur, from_user_id: str):
    to_user_id = session["user_id"]

    is_friend = are_already_friends(from_user_id, to_user_id)
    if is_friend:
        return jsonify({
            "error": True,
            "message": "Dit is al je vriend",
            "type": "general",
            "category": "error"
        }), 400

    has_friend_request = has_friend_request_from_user(from_user_id, to_user_id)
    if not has_friend_request:
        return {
            "error": True,
            "message": "Geen vriendschapsverzoek van deze gebruiker",
            "category": "error",
            "type": "general",
        }

    id = str(uuid4())
    created_at = int(time.time())
    cur.execute("INSERT INTO friends VALUES(%s, %s, %s, %s)", (id, from_user_id, to_user_id, created_at))

    cur.execute("DELETE FROM friend_requests WHERE from_user_id = %s AND to_user_id = %s", (from_user_id, to_user_id))

    to_user_username = main.get_user_info("username", to_user_id)

    data = {
        "username": to_user_username
    }
    socketio.emit("friend_request_accepted", data, room=f"notifications:{from_user_id}", namespace="/ws/notifications")

    return jsonify({
        "error": False,
        "message": "Wow, een nieuwe vriend",
        "type": "general",
        "category": "success"
    }), 201


@friend_request_bp.post("/<to_user_id>/cancel")
@login_required()
@wrap_errors()
def cancel_friend_request_post(to_user_id: str):
    from_user_id = session["user_id"]

    result = remove_friend_request(from_user_id, to_user_id)
    if result["error"]:
        return jsonify({
            "error": True,
            "message": result["message"],
            "category": result["category"],
            "type": result["type"],
        }), 400

    data = {
        "user_id": from_user_id
    }
    socketio.emit("friend_request_canceled", data, room=f"notifications:{to_user_id}", namespace="/ws/notifications")

    return jsonify({
        "error": False,
        "message": "Jammer, geen nieuwe vriend",
        "type": "general",
        "category": "success"
    }), 201
