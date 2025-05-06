import werkzeug.exceptions
from flask import request, session, flash, redirect, jsonify, render_template
from flask_socketio import disconnect
from functools import wraps
import src.snake.main as main

logger = main.logger


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


def wrap_errors(message="Er ging iets mis 😢", html_template="404.html"):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except KeyError as e:
                print(f"KeyError: {e}")
                return jsonify({
                    "error": True,
                    "message": "Vul aub alle velden in",
                    "type": "general",
                    "category": "error"
                }), 400
            except werkzeug.exceptions.UnsupportedMediaType:
                return jsonify({
                    "error": True,
                    "message": "Unsupported media type",
                    "type": "general",
                    "category": "error"
                }), 415
            except werkzeug.exceptions.RequestEntityTooLarge:
                return jsonify({
                    "error": True,
                    "message": "Bestand is te groot",
                    "type": "general",
                    "category": "error"
                }), 413
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
                    return render_template(html_template, error_message=message), 500
        return decorated_function
    return decorator


def db_connection(cursor_type=None):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            con = main.connect_to_db(cursor_type)
            cur = con.cursor()
            try:
                result = func(con, cur, *args, **kwargs)
                con.commit()  # Optional depending on read/write
                return result
            finally:
                cur.close()
                con.close()
        return decorated_function
    return decorator
