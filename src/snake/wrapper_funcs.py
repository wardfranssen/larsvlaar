from flask import request, session, flash, redirect, jsonify, render_template
from werkzeug.exceptions import UnsupportedMediaType, RequestEntityTooLarge
from flask_limiter.errors import RateLimitExceeded
from flask_socketio import disconnect
from src.snake.main import *
from functools import wraps


def login_required(message="Je moet ingelogd zijn om dit te doen", redirect_to="/login"):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("logged_in"):
                if request.path == "/socket.io/":
                    disconnect()
                    return
                elif request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                    return jsonify({
                        "error": True,
                        "message": message,
                        "type": "general",
                        "category": "error"
                    }), 401
                else:
                    # Redirect to login page, optionally with next URL
                    flash(message, "error")
                    return redirect(redirect_to)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def wrap_errors(html_template="404.html"):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except KeyError as e:
                return jsonify({
                    "error": True,
                    "message": "Vul aub alle velden in",
                    "type": "general",
                    "category": "error"
                }), 400
            except RequestEntityTooLarge:
                return jsonify({
                    "error": True,
                    "message": "Bestand is te groot",
                    "type": "general",
                    "category": "error"
                }), 413
            except UnsupportedMediaType:
                return jsonify({
                    "error": True,
                    "message": "Media type wordt niet ondersteund",
                    "type": "general",
                    "category": "error"
                }), 415
            except RateLimitExceeded:
                return jsonify({
                    "error": True,
                    "message": "Wow, niet zo snel!",
                    "type": "general",
                    "category": "error"
                }), 429
            except Exception as e:
                logger.error(f"{f.__name__}: {e}", exc_info=True)
                if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                    return jsonify({
                        "error": True,
                        "message": "Er is een probleem opgetreden",
                        "category": "error",
                        "type": "general",
                    }), 500
                else:
                    return render_template(html_template), 500
        return decorated_function
    return decorator


def db_connection(cursor_type=None):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            con = connect_to_db(cursor_type)
            cur = con.cursor()
            try:
                result = func(con, cur, *args, **kwargs)
                con.commit()
                return result
            finally:
                cur.close()
                con.close()
        return decorated_function
    return decorator


def render_with_user_info():
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            invites = get_pending_invites(user_id) if user_id else []

            context, template = view_func(*args, **kwargs)
            print(session.get("background"))

            background_image = session.get("background", {"path": "/img/boze_lars.jpg"})["path"]
            if not isinstance(context, dict) or not isinstance(template, str):
                raise ValueError("Your view must return (context_dict, template_name)")

            context.update({
                "username": session.get("username"),
                "user_id": user_id,
                "pfp_version": session.get("pfp_version"),
                "is_admin": session.get("is_admin"),
                "invites": invites,
                "general_messages": get_general_messages(user_id),
                "background_image": background_image,
                "balance": get_user_info("balance", user_id)
            })

            return render_template(template, **context)
        return wrapped
    return decorator

