from src.snake.api.one_vs_one import default_game_state
from src.snake.game import game_mode_config
from src.snake.api.lobby import get_lobby
from src.snake.wrapper_funcs import *
from src.snake.app import socketio
from flask import Blueprint
from copy import deepcopy
from uuid import uuid4
import json

invites_bp = Blueprint("invites", __name__, url_prefix="/api/invites")


def remove_invite(invite_id: str, invite: dict):
    from_user_id = invite["from"]
    to_user_id = invite["to"]

    redis_client.delete(f"{redis_prefix}:invite:{invite_id}")
    redis_client.srem(f"{redis_prefix}:user:{to_user_id}:invites:received", invite_id)
    redis_client.srem(f"{redis_prefix}:user:{from_user_id}:invites:sent", invite_id)
    redis_client.delete(f"{redis_prefix}:invite:{from_user_id}:{to_user_id}")


def is_invite_for_user(invite_id: str, user_id: str) -> dict:
    is_for_user = redis_client.sismember(f"{redis_prefix}:user:{user_id}:invites:received", invite_id)

    if not is_for_user:
        return {
            "error": True,
            "message": "Geen uitnodiging ontvangen",
            "type": "general",
            "category": "error",
            "status_code": 404
        }

    invite = redis_client.getex(f"{redis_prefix}:invite:{invite_id}")
    invite = json.loads(invite)
    return {
        "error": False,
        "invite": invite
    }


@invites_bp.delete("/<invite_id>")
@login_required()
@wrap_errors()
def delete_invite(invite_id: str):
    from_user_id = session["user_id"]
    invite = redis_client.getex(f"{redis_prefix}:invite:{invite_id}")

    if not invite:
        return jsonify({
            "error": True,
            "message": "Uitnodiging bestaat niet",
            "type": "general",
            "category": "error"
        }), 400
    invite = json.loads(invite)
    if from_user_id != invite["from"]:
        return jsonify({
            "error": True,
            "message": "Deze uitnodiging is niet door jou gestuurd",
            "type": "general",
            "category": "error",
        }), 403

    remove_invite(invite_id, invite)

    # Tell client that invite has been canceled
    username = get_user_info("username", invite["from"])
    data = {
        "invite_id": invite_id,
        "username": username
    }
    socketio.emit("invite_canceled", data, room=f"notifications:{invite["to"]}", namespace="/ws/notifications")

    return jsonify({
        "error": False,
    })


@invites_bp.post("/<invite_id>/accept")
@login_required()
@wrap_errors()
def accept_invite_post(invite_id: str):
    user_id = session["user_id"]
    result = is_invite_for_user(invite_id, user_id)

    if result["error"]:
        return jsonify({
            "error": True,
            "message": result["message"],
            "type": result["type"],
            "category": result["category"]
        }), result["status_code"]

    invite = result["invite"]
    lobby_id = invite["lobby_id"]

    from_user_id = invite["from"]
    from_username = get_user_info("username", from_user_id)
    from_pfp_version = get_user_info("pfp_version", from_user_id)

    to_user_id = invite["to"]
    to_username = get_user_info("username", to_user_id)
    to_pfp_version = get_user_info("pfp_version", to_user_id)

    remove_invite(invite_id, invite)

    if lobby_id:
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
            lobby["allowed_to_join"].append(to_user_id)
            redis_client.set(f"{redis_prefix}:lobbies:{lobby_id}", json.dumps(lobby), ex=15)
        finally:
            try:
                redlock.unlock(lock)
            except Exception as e:
                logger.warning(f"Failed to unlock {lock.resource}: {e}")

        data = {
            "invite_id": invite_id,
            "lobby_id": lobby_id
        }

        socketio.emit("invite_accepted", data, room=f"notifications:{from_user_id}", namespace="/ws/notifications")
        return jsonify({
            "error": False,
            "redirect": f"/lobby/{lobby_id}"
        })

    # Create game
    players = {
        to_user_id: {
            "username": to_username,
            "pfp_version": to_pfp_version,
            "skin": json.loads(get_user_info("skin", to_user_id))["path"],
            "food_skin": json.loads(get_user_info("food_skin", to_user_id))["path"],
            "ready": False,
            "connected": False
        },
        from_user_id: {
            "username": from_username,
            "pfp_version": from_pfp_version,
            "food_skin": json.loads(get_user_info("food_skin", to_user_id))["path"],
            "skin": json.loads(get_user_info("skin", from_user_id))["path"],
            "ready": False,
            "connected": False
        }
    }

    game_id = str(uuid4())
    game_mode = invite["game_mode"]
    game_state = deepcopy(default_game_state)

    game_state["players"] = players
    game_state["board"] = game_mode_config[game_mode]["board"]

    # Send game info to clients
    redirect = f"/snake/{game_mode}?game_id={game_id}&from=invite"
    data = {
        "redirect": redirect,
        "opponent": {
            "user_id": to_user_id,
            "username": to_username,
            "pfp_version": to_pfp_version
        }
    }
    socketio.emit("invite_accepted", data, room=f"notifications:{from_user_id}", namespace="/ws/notifications")

    redis_client.hset(f"{redis_prefix}:games:{game_mode}", game_id, json.dumps(game_state))
    redis_client.setex(f"{redis_prefix}:game_mode:{game_id}", 3600, game_mode)

    return jsonify({
        "error": False,
        "redirect": redirect,
        "opponent": {
            "user_id": from_user_id,
            "username": from_username,
            "pfp_version": from_pfp_version
        }
    })


@invites_bp.post("/<invite_id>/reject")
@login_required()
@wrap_errors()
def reject_invite_post(invite_id: str):
    result = is_invite_for_user(invite_id, session["user_id"])

    if result["error"]:
        return jsonify({
            "error": True,
            "message": result["message"],
            "type": result["type"],
            "category": result["category"]
        }), result["status_code"]

    invite = result["invite"]
    from_user_id = invite["from"]
    to_user_id = invite["to"]

    remove_invite(invite_id, invite)

    username = get_user_info("username", to_user_id)
    data = {
        "invite_id": invite_id,
        "username": username
    }
    socketio.emit("invite_rejected", data, room=f"notifications:{from_user_id}", namespace="/ws/notifications")

    return {
        "error": False
    }
