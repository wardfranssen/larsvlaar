from src.snake.wrapper_funcs import *
from src.snake.app import socketio
from flask import Blueprint
from src.snake import main

friends_bp = Blueprint("friends", __name__, url_prefix="/api/friends")
redis_client = main.redis_client
redis_prefix = main.redis_prefix


@friends_bp.get("/")
@login_required()
@wrap_errors()
@db_connection()
def my_friends_get(con, cur):
    user_id = session["user_id"]

    cur.execute("SELECT user1_id, user2_id FROM friends WHERE user1_id = %s OR user2_id = %s", (user_id, user_id))
    friendships = cur.fetchall()

    friends = {}
    for friendship in friendships:
        friend = {}
        if friendship[0] == user_id:
            friend_id = friendship[1]
        else:
            friend_id = friendship[0]

        friend["username"] = main.get_user_info("username", friend_id)
        friend["status"] = main.get_status(friend_id)
        friend["pfp_version"] = int(main.get_user_info("pfp_version", friend_id))
        friends[friend_id] = friend

    return jsonify({
        "error": False,
        "friends": friends
    })


@friends_bp.delete("/<to_remove_id>")
@login_required()
@wrap_errors()
@db_connection()
def remove_friend_post(con, cur, to_remove_id: str):
    user_id = session["user_id"]

    cur.execute("DELETE FROM friends WHERE user1_id = %s AND user2_id = %s OR user1_id = %s AND user2_id = %s",
                (to_remove_id, user_id, user_id, to_remove_id))

    data = {
        "user_id": user_id
    }
    socketio.emit("friend_removed", data, room=f"notifications:{to_remove_id}", namespace="/ws/notifications")

    return jsonify({
        "error": False,
        "message": "Daar gaat je vriend...",
        "type": "general",
        "category": "success"
    }), 201
