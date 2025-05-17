from src.snake.login import *
from src.snake.main import *
from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/kritiek")
@login_required()
@wrap_errors()
@db_connection()
def get_kritiek(con, cur):
    if not session["is_admin"]:
        return jsonify({
            "error": True,
            "message": "Niet genoeg rechten",
            "type": "general",
            "category": "error"
        })

    cur.execute("SELECT * FROM kritiek")
    result = cur.fetchall()

    if not result:
        return jsonify({
            "error": True,
            "message": "Geen kritiek",
            "type": "general",
            "category": "error"
        })

    kritiek_data = {}
    for kritiek in result:
        user_id = kritiek[1]

        kritiek_data[kritiek[0]] = {
            "user_id": user_id,
            "username": get_user_info("username", user_id),
            "pfp_version": get_user_info("pfp_version", user_id),
            "status": get_status(user_id),
            "kritiek": kritiek[2],
            "created_at": kritiek[3]
        }

    return jsonify({
        "error": False,
        "kritiek": kritiek_data
    })


@admin_bp.delete("/kritiek/<kritiek_id>")
@login_required()
@wrap_errors()
@db_connection()
def delete_kritiek(con, cur, kritiek_id):
    if not session["is_admin"]:
        return jsonify({
            "error": True,
            "message": "Niet genoeg rechten",
            "type": "general",
            "category": "error"
        })

    cur.execute("DELETE FROM kritiek WHERE kritiek_id = %s", (kritiek_id,))

    return jsonify({
        "error": False,
        "message": "Kritiek verwijdert",
        "type": "general",
        "category": "success"
    })


@admin_bp.get("/sessions")
@login_required()
@wrap_errors()
def get_sessions():
    if not session["is_admin"]:
        return jsonify({
            "error": True,
            "message": "Niet genoeg rechten",
            "type": "general",
            "category": "error"
        })

    session_keys = redis_client.keys(f"{redis_prefix}:session:*")

    sessions_data = {}
    for key in session_keys:
        session_data = json.loads(redis_client.get(key))

        # Todo: Get active game

        sessions_data[key.replace(f"{redis_prefix}:session:", "")] = {
            "user_id": session_data.get("user_id"),
            "username": session_data.get("username"),
            "pfp_version": session_data.get("pfp_version"),
            "requests": session_data.get("requests"),
            "status": get_status(session_data.get("user_id"))
        }

    return jsonify({
        "error": False,
        "sessions": sessions_data,
        "server_time": int(time.time() * 1000)
    })


@admin_bp.get("/sessions/<session_id>")
@login_required()
@wrap_errors()
def get_session_data(session_id):
    if not session["is_admin"]:
        return jsonify({
            "error": True,
            "message": "Niet genoeg rechten",
            "type": "general",
            "category": "error"
        })

    result = redis_client.get(f"{redis_prefix}:session:{session_id}")
    if not result:
        return jsonify({
            "error": True,
            "message": "Sessie bestaat niet",
            "type": "general",
            "category": "error"
        })

    result = json.loads(result)

    session_data = {
        "user_id": result.get("user_id"),
        "username": result.get("username"),
        "pfp_version": result.get("pfp_version"),
        "requests": result.get("requests"),
        "status": get_status(result.get("user_id"))
    }

    return jsonify({
        "error": False,
        "data": session_data,
        "server_time": int(time.time() * 1000)
    })


@admin_bp.delete("/sessions/<session_id>")
@login_required()
@wrap_errors()
def delete_session(session_id):
    if not session["is_admin"]:
        return jsonify({
            "error": True,
            "message": "Niet genoeg rechten",
            "type": "general",
            "category": "error"
        })

    redis_client.delete(f"{redis_prefix}:session:{session_id}")

    return jsonify({
        "error": False,
        "message": "Sessie verwijdert",
        "type": "general",
        "category": "success"
    })
