from pymysql.cursors import DictCursor
from src.snake.wrapper_funcs import *
from src.snake.main import *
from flask import Blueprint

leaderboard_bp = Blueprint("leaderboard", __name__, url_prefix="/api/leaderboard")

@db_connection(DictCursor)
def get_leaderboard(con, cur, query: str, stat: str) -> dict:
    cur.execute(query)
    leaderboard = cur.fetchall()

    formatted_leaderboard = []
    for user in leaderboard:
        if user["stat"] is not None:
            user_id = user["user_id"]
            formatted_leaderboard.append({
                "user_id": user_id,
                "stat": f"{user["stat"]} {stat}",
                "pfp_version": get_pfp_version(user_id),
                "username": get_username(user_id)
            })

    return {
        "error": False,
        "leaderboard": formatted_leaderboard
    }


def create_query_parts(column: str, selected_game_modes: list):
    query_parts= []
    for game_mode in selected_game_modes:
        if game_mode not in game_modes:
            return {
                "error": True,
                "message": "Game mode bestaat niet",
                "type": "general",
                "category": "error"
            }
        query_parts.append(f"SELECT user_id, {column} FROM user_stats_{game_mode}")

    return {
        "error": False,
        "query_parts": query_parts
    }


def get_game_modes(game_modes_arg: str):
    selected_game_modes = list(set(game_modes_arg.split(",")))

    if selected_game_modes[0] == "all":
        selected_game_modes = game_modes
    return selected_game_modes


@leaderboard_bp.get("/game_count")
@login_required()
@wrap_errors()
def game_count():
    selected_game_modes = list(set(request.args.get("game_modes", "all").split(",")))

    if selected_game_modes[0] == "all":
        query = """
            SELECT user_id, COUNT(*) AS stat
            FROM player_games
        """
    else:
        query = """
            SELECT user_id, COUNT(*) AS stat
            FROM player_games
            WHERE TRUE
        """

        for game_mode in selected_game_modes:
            if game_mode not in game_modes:
                return jsonify({
                    "error": True,
                    "message": "Game mode bestaat niet",
                    "type": "general",
                    "category": "error"
                })
            query += f"""
                AND game_mode = "{game_mode}"
            """

    query += """
        GROUP BY user_id
        ORDER BY stat DESC;
    """

    result = get_leaderboard(query, "games")

    return jsonify(result)



@leaderboard_bp.get("/highscore")
@login_required()
@wrap_errors()
def highscore():
    selected_game_modes = get_game_modes(request.args.get("game_modes", "all"))

    result = create_query_parts("highscore", selected_game_modes)
    if result["error"]:
        return jsonify(result)
    query_parts = result["query_parts"]

    query = f"""
        SELECT 
            user_id,
            MAX(highscore) AS stat
        FROM (
            {' UNION ALL '.join(query_parts)}
        ) AS combined_stats
        GROUP BY user_id
        ORDER BY stat DESC;
    """

    result = get_leaderboard(query, "puntjes")
    return jsonify(result)


@leaderboard_bp.get("/total_score")
@login_required()
@wrap_errors()
def total_score():
    selected_game_modes = get_game_modes(request.args.get("game_modes", "all"))

    result = create_query_parts("total_score", selected_game_modes)
    if result["error"]:
        return jsonify(result)
    query_parts = result["query_parts"]

    query = f"""
        SELECT 
            user_id,
            SUM(total_score) AS stat
        FROM (
            {' UNION ALL '.join(query_parts)}
        ) AS combined_stats
        GROUP BY user_id
        ORDER BY stat DESC;
    """

    result = get_leaderboard(query, "puntjes")
    return jsonify(result)


@leaderboard_bp.get("/wins")
@login_required()
@wrap_errors()
def wins():
    selected_game_modes = get_game_modes(request.args.get("game_modes", "all"))

    result = create_query_parts("wins", selected_game_modes)
    if result["error"]:
        return jsonify(result)
    query_parts = result["query_parts"]

    query = f"""
        SELECT 
            user_id,
            SUM(wins) AS stat
        FROM (
            {' UNION ALL '.join(query_parts)}
        ) AS combined_stats
        GROUP BY user_id
        ORDER BY stat DESC;
    """

    result = get_leaderboard(query, "wins")
    return jsonify(result)


@leaderboard_bp.get("/kills")
@login_required()
@wrap_errors()
def kills():
    selected_game_modes = get_game_modes(request.args.get("game_modes", "all"))

    result = create_query_parts("kills", selected_game_modes)
    if result["error"]:
        return jsonify(result)
    query_parts = result["query_parts"]

    query = f"""
        SELECT 
            user_id,
            SUM(kills) AS stat
        FROM (
            {' UNION ALL '.join(query_parts)}
        ) AS combined_stats
        GROUP BY user_id
        ORDER BY stat DESC;
    """

    result = get_leaderboard(query, "kills")
    return jsonify(result)


@leaderboard_bp.get("/playtime")
@login_required()
@wrap_errors()
def playtime():
    selected_game_modes = get_game_modes(request.args.get("game_modes", "all"))

    result = create_query_parts("playtime", selected_game_modes)
    if result["error"]:
        return jsonify(result)
    query_parts = result["query_parts"]

    query = f"""
        SELECT 
            user_id,
            CAST(ROUND(SUM(playtime) / 60) AS SIGNED) AS stat
        FROM (
            {' UNION ALL '.join(query_parts)}
        ) AS combined_stats
        GROUP BY user_id
        ORDER BY stat DESC;
    """

    result = get_leaderboard(query, "min")
    return jsonify(result)


@leaderboard_bp.get("/win-loss")
@login_required()
@wrap_errors()
def win_loss_ratio():
    selected_game_modes = get_game_modes(request.args.get("game_modes", "all"))

    result = create_query_parts("wins, losses", selected_game_modes)
    if result["error"]:
        return jsonify(result)
    query_parts = result["query_parts"]

    query = f"""
        SELECT 
            user_id,
            ROUND(SUM(wins) / NULLIF(SUM(losses), 0), 2) AS stat
        FROM (
            {' UNION ALL '.join(query_parts)}
        ) AS combined_stats
        GROUP BY user_id
        ORDER BY stat DESC;
    """

    result = get_leaderboard(query, "wins/loss")
    return jsonify(result)


@leaderboard_bp.get("/k-d")
@login_required()
@wrap_errors()
def k_d_ratio():
    selected_game_modes = get_game_modes(request.args.get("game_modes", "all"))

    result = create_query_parts("kills, suicides, killed_by_others, border_deaths", selected_game_modes)
    if result["error"]:
        return jsonify(result)
    query_parts = result["query_parts"]

    query = f"""
        SELECT 
            user_id,
            ROUND(SUM(kills) / NULLIF(SUM(suicides + killed_by_others + border_deaths), 0), 2) AS stat
        FROM (
            {' UNION ALL '.join(query_parts)}
        ) AS combined_stats
        GROUP BY user_id
        ORDER BY stat DESC;
    """

    result = get_leaderboard(query, "k/d")
    return jsonify(result)
