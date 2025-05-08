from src.snake.api.friend_request import friend_request_bp
from src.snake.api.auth import auth_bp
from src.snake.api.account import account_bp
from src.snake.api.games import games_bp
from src.snake.api.users import users_bp
from src.snake.api.invites import invites_bp
from src.snake.api.lobby import lobby_bp
from src.snake.api.friends import friends_bp
from src.snake.api.leaderboard import leaderboard_bp
from src.snake.api.chat import chat_bp


def register_routes(app):
    app.register_blueprint(account_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(friend_request_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(invites_bp)
    app.register_blueprint(lobby_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(chat_bp)

