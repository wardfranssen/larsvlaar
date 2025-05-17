from pymysql.err import IntegrityError
from src.snake.wrapper_funcs import *
import src.snake.main as main
from uuid import uuid4
import random
import json
import time

config = main.config
redis_prefix = config["REDIS"]["PREFIX"]

game_mode_config = {
    "one_vs_one": {"board": {"rows": 15, "cols": 15}, "spawn_len": 5, "grow": 1, "update_interval": 0.210, "food_amount": 1},
    "massive_multiplayer": {"board": {"rows": 50, "cols": 50}, "spawn_len": 3, "grow": 1, "update_interval": 0.200, "food_amount": 25},
    "single_player": {"board": {"rows": 15, "cols": 15}, "spawn_len": 4, "grow": 1, "update_interval": 0.210, "food_amount": 1}
}


def generate_food_pos(snakes: list[list[list[int]]], game_mode_config: dict, food_positions=None) -> list[int] | None:
    """Generate a food position that doesn't overlap with snakes or existing food. Returns None if no valid spot is left."""
    if food_positions is None:
        food_positions = []

    board_cols = game_mode_config["board"]["cols"]
    board_rows = game_mode_config["board"]["rows"]

    # All possible positions
    all_positions = {(x, y) for x in range(board_cols) for y in range(board_rows)}

    # Flatten snake positions
    occupied = {tuple(pos) for snake in snakes for pos in snake}
    for pos in food_positions:
        if pos:
            occupied.add(tuple(pos))

    # Available positions
    available = list(all_positions - occupied)

    if not available:
        return None

    return list(random.choice(available))



def hit_border(snake: list[list[int, int]], game_mode_config: dict) -> bool:
    """Check if snake hit the border"""
    head = snake[-1]
    return (head[0] < 0 or head[0] >= game_mode_config["board"]["cols"] or
            head[1] < 0 or head[1] >= game_mode_config["board"]["rows"])


def hit_self(snake: list[list[int, int]]) -> bool:
    head = snake[-1]

    for i in range(len(snake)):
        if i == len(snake)-1:
            continue
        if snake[i] == head:
            return True
    return False


def check_collision_with_other_snake(snake1: list[list[int, int]], snake2: list[list[int, int]]):
    """Check if the snake1 collides with snake2"""
    head = snake1[-1]

    # Check self-collision
    for i in range(len(snake2)):
        if snake2[i] == head:
            return True
    return False


@db_connection()
def save_game(con, cur, game_id: str, game_mode: str):
    ended_at = int(time.time())
    game_state = json.loads(main.redis_client.hget(f"{redis_prefix}:games:{game_mode}", game_id))

    winner = game_state["winner"]
    game_settings = game_state["settings"]
    started_at = game_state["started_at"]

    for i in range(5):
        try:
            cur.execute("INSERT INTO games_metadata VALUES(%s, %s, %s, %s, %s, %s, %s)", (game_id, game_mode, winner, json.dumps(game_settings), json.dumps(game_state["food"]), started_at, ended_at))
            break
        except IntegrityError:
            game_id = str(uuid4())

    for player_id, player in game_state["players"].items():
        if player_id == winner:
            outcome = "wins"
        elif not winner:
            outcome = "draws"
        else:
            outcome = "losses"

        score = player["score"]
        play_time = ended_at - started_at

        query = f"""
            UPDATE user_stats_{game_mode}
            SET
                highscore = GREATEST(highscore, %s),
                total_score = total_score + %s,
                kills = kills + %s,
                playtime = playtime + %s,
        """

        if player["cause_of_death"]:
            query += f"""
                {player["cause_of_death"]} = {player["cause_of_death"]} + 1,
            """
        if game_mode != "single_player":
            query += f"""
            {outcome} = {outcome} + 1,
            """

        cur.execute(
            f"""{query}
                last_played = %s
            WHERE user_id = %s
            """,
            (score, score, len(player["kills"]), play_time, ended_at, player_id)
        )

        if game_mode != "custom":
            cur.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (score, player_id))
            cur.execute("SELECT balance FROM users WHERE user_id = %s", (player_id,))

            redis_client.hset(f"{redis_prefix}:user:{player_id}", "balance", cur.fetchone()[0])
            redis_client.expire(f"{redis_prefix}:user:{player_id}", 3600)

        player_data = {
            "score": player["score"],
            "moves": player["moves"],
            "spawn_pos": player["spawn_pos"],
            "pfp_version": player["pfp_version"],
            "skin": player["skin"]
        }

        cur.execute("INSERT INTO player_games VALUES(%s, %s, %s, %s, %s)", (game_id, player_id, json.dumps(player_data), game_mode, ended_at))


def generate_snake_spawns(num_snakes: int, map_width: int, map_height: int, snake_length: int):
    if snake_length > max(map_width, map_height):
        return {
            "error": True,
            "message": "Slangen passen niet op het bord"
        }

    margin = 2
    spawns = []

    if num_snakes == 4:
        center_x = map_width // 2
        center_y = map_height // 2

        # Top (faces down)
        spawns.append({
            "direction": "down",
            "body": [[center_x, margin - i] for i in range(snake_length)]
        })

        # Bottom (faces up)
        spawns.append({
            "direction": "up",
            "body": [[center_x, map_height - margin - 1 + i] for i in range(snake_length)]
        })

        # Left (faces right)
        spawns.append({
            "direction": "right",
            "body": [[margin - i, center_y] for i in range(snake_length)]
        })

        # Right (faces left)
        spawns.append({
            "direction": "left",
            "body": [[map_width - margin - 1 + i, center_y] for i in range(snake_length)]
        })

        return {
            "error": False,
            "spawns": spawns
        }

    # Otherwise fallback to general horizontal-preferred logic
    # (reuse previous function here)
    return generate_general_snake_spawns(num_snakes, map_width, map_height, snake_length)


def generate_general_snake_spawns(num_snakes: int, map_width: int, map_height: int, snake_length: int):
    spawns = []

    horizontal_ok = snake_length <= map_width
    vertical_ok = snake_length <= map_height

    if horizontal_ok:
        use_vertical = False
    elif vertical_ok:
        use_vertical = True
    else:
        return {
            "error": True,
            "message": "Bord te klein voor de slangen"
        }

    # Handle 1 snake
    if num_snakes == 1:
        if not use_vertical:
            y = map_height // 2
            tail_x = 0
            spawns.append({
                "direction": "right",
                "body": [[tail_x + j, y] for j in reversed(range(snake_length))]
            })
        else:
            x = map_width // 2
            tail_y = 0
            spawns.append({
                "direction": "down",
                "body": [[x, tail_y + j] for j in reversed(range(snake_length))]
            })
        return {
            "error": False,
            "spawns": spawns
        }

    # Special case: 3 snakes (2 horizontal centered, 1 vertical at top)
    if num_snakes == 3:
        # Center y for horizontal snakes
        y_center = map_height // 2

        # Left snake
        tail_x = 0
        spawns.append({
            "direction": "right",
            "body": [[tail_x + j, y_center] for j in reversed(range(snake_length))]
        })

        # Right snake
        tail_x = map_width - 1
        spawns.append({
            "direction": "left",
            "body": [[tail_x - j, y_center] for j in reversed(range(snake_length))]
        })

        # Top middle snake
        x = map_width // 2
        tail_y = 0
        spawns.append({
            "direction": "down",
            "body": [[x, tail_y + j] for j in reversed(range(snake_length))]
        })

        return {
            "error": False,
            "spawns": spawns
        }

    # General logic
    is_odd = num_snakes % 2 == 1 and num_snakes > 4

    if not use_vertical:
        total_space = map_height
        num_pairs = num_snakes // 2 if not is_odd else (num_snakes - 1) // 2
        spacing = total_space // (num_pairs + 1)
        start_y = (total_space - (spacing * num_pairs)) // 2 + spacing // 2
        y_positions = [start_y + spacing * i for i in range(num_pairs)]

        # Optional center snake first (on the left side)
        if is_odd:
            y = map_height // 2
            tail_x = 0
            spawns.append({
                "direction": "right",
                "body": [[tail_x + j, y] for j in reversed(range(snake_length))]
            })

        for i, y in enumerate(y_positions):
            if len(spawns) < num_snakes:
                # Left
                tail_x = 0
                spawns.append({
                    "direction": "right",
                    "body": [[tail_x + j, y] for j in reversed(range(snake_length))]
                })
            if len(spawns) < num_snakes:
                # Right
                tail_x = map_width - 1
                spawns.append({
                    "direction": "left",
                    "body": [[tail_x - j, y] for j in reversed(range(snake_length))]
                })
    else:
        total_space = map_width
        num_pairs = num_snakes // 2 if not is_odd else (num_snakes - 1) // 2
        spacing = total_space // (num_pairs + 1)
        start_x = (total_space - (spacing * num_pairs)) // 2 + spacing // 2
        x_positions = [start_x + spacing * i for i in range(num_pairs)]

        # Optional center snake first (at top)
        if is_odd:
            x = map_width // 2
            tail_y = 0
            spawns.append({
                "direction": "down",
                "body": [[x, tail_y + j] for j in reversed(range(snake_length))]
            })

        for i, x in enumerate(x_positions):
            if len(spawns) < num_snakes:
                # Top
                tail_y = 0
                spawns.append({
                    "direction": "down",
                    "body": [[x, tail_y + j] for j in reversed(range(snake_length))]
                })
            if len(spawns) < num_snakes:
                # Bottom
                tail_y = map_height - 1
                spawns.append({
                    "direction": "up",
                    "body": [[x, tail_y - j] for j in reversed(range(snake_length))]
                })

    return {
        "error": False,
        "spawns": spawns
    }


