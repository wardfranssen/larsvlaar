import uuid

from pymysql.err import IntegrityError
import random
import main
import json

config = main.config
rows = 15
columns = 15
redis_prefix = config["REDIS"]["PREFIX"]


def generate_food_pos(snakes: list[list[int]]) -> list:
    while True:
        random_pos = [random.randint(0, rows - 1), random.randint(0, columns - 1)]

        for snake in snakes:
            if random_pos in snake:
                break
        else:
            return random_pos


def calc_new_speed(speed: float) -> float:
    if speed > 185:
        speed = speed * 0.995 + speed * 0.0001 + 0.2
    elif speed > 175:
        speed = speed * 0.997 + speed * 0.0005 + 0.1
    elif speed > 163:
        speed = speed * 0.994 + speed * 0.002 + 0.3
    elif speed > 150:
        speed = speed * 0.997 + speed * 0.0008 + 0.1
    elif speed > 125:
        speed *= 0.999
    return speed


def check_collision(snake):
    """Check if the snake collides with itself or the walls."""
    head = snake[-1]

    # Check border collision
    if head[0] < 0 or head[0] >= rows or head[1] < 0 or head[1] >= columns:
        print("border")
        return True

    # Check self-collision
    for i in range(len(snake)):
        if i == 0 or i == len(snake)-1:
            continue
        if snake[i] == head:
            return True
    return False


def check_collision_with_other_snake(snake1, snake2):
    """Check if the snake1 collides with snake2"""
    head = snake1[-1]

    # Check self-collision
    for i in range(len(snake2)):
        if snake2[i] == head:
            return True
    return False


def save_game(game_id: str, game_mode: str):
    # Move to game.py (have to save games to Redis first prob(so it doesn't clear games on restart))

    print("SAVVVVVING")
    game_state = json.loads(main.redis_client.hget(f"{redis_prefix}-games-{game_mode}", game_id))

    main.redis_client.hdel(f"{main.config}-games-{game_mode}", game_id)

    con = main.connect_to_db()
    cur = con.cursor()

    try:
        cur.execute("INSERT INTO snake_games VALUES(%s, %s, %s, %s)", (game_id, json.dumps(game_state["players"]), game_state["game_start"], game_state["winner"],))
        con.commit()
    except IntegrityError:
        game_id = str(uuid.uuid4())

        cur.execute("INSERT INTO snake_games VALUES(%s, %s, %s, %s)", (game_id, json.dumps(game_state["players"]), game_state["game_start"], game_state["winner"],))
        con.commit()

    cur.close()
    con.close()
