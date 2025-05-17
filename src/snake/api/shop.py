from pymysql.cursors import DictCursor
from src.snake.wrapper_funcs import *
from flask import Blueprint
from src.snake.main import *
import random

shop_bp = Blueprint("shop", __name__, url_prefix="/api/shop")
items_types = {
    "skins": "skin",
    "backgrounds": "background",
    "food_skins": "food_skin"
}


@shop_bp.get("/loot_boxes")
@login_required()
@wrap_errors()
@db_connection(DictCursor)
def items_get(con, cur):
    cur.execute(f"SELECT * FROM loot_boxes")
    loot_boxes = cur.fetchall()

    return jsonify({
        "error": False,
        "items": loot_boxes
    })


@shop_bp.post("/loot_boxes/<loot_box_id>")
@login_required()
@db_connection()
def buy_lootbox(con, cur, loot_box_id):
    user_id = session["user_id"]

    cur.execute(f"SELECT price, type FROM loot_boxes WHERE loot_box_id = %s", (loot_box_id,))
    result = cur.fetchone()

    if not result:
        return jsonify({
            "error": True,
            "message": "Lootbox bestaat niet",
            "type": "general",
            "category": "error"
        }), 404

    price = result[0]
    box_type = result[1]

    cur.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
    balance = cur.fetchone()

    balance = balance[0]

    if balance < price:
        return jsonify({
            "error": True,
            "message": "Niet genoeg vlaar coins",
            "type": "general",
            "category": "error"
        }), 400

    if box_type == "all":
        cur.execute("SELECT item_id, rarity FROM items")
        loot_box_items = cur.fetchall()

        cur.execute("SELECT item_id FROM user_items")
        unlocked_items_result = cur.fetchall()
    else:
        cur.execute("SELECT item_id, rarity FROM items WHERE type = %s", (box_type,))
        loot_box_items = cur.fetchall()

        cur.execute("SELECT item_id FROM user_items WHERE type = %s", (box_type,))
        unlocked_items_result = cur.fetchall()

    unlocked_items = []
    for item in unlocked_items_result:
        unlocked_items.append(item[0])

    odds = {}
    commons = []

    total_odds = 0
    for item in loot_box_items:
        item_id = item[0]
        rarity = item[1]

        if item_id in unlocked_items:
            continue

        if rarity == "rare":
            odds[item_id] = 3
            total_odds += 3
        elif rarity == "ultra_rare":
            odds[item_id] = 1
            total_odds += 1
        elif rarity == "common":
            commons.append(item_id)

    remaining_odds = 100 - total_odds

    if len(commons) != 0:
        odds_per_common = remaining_odds / len(commons)
        for common in commons:
            odds[common] = odds_per_common

    total_weight = sum(odds.values())
    normalized_odds = {item_id: (weight / total_weight) * 100 for item_id, weight in odds.items()}

    item_ids = list(normalized_odds.keys())
    weights = list(normalized_odds.values())

    try:
        chosen_item_id = random.choices(item_ids, weights=weights, k=1)[0]
    except IndexError:
        return jsonify({
            "error": True,
            "message": "Je alle items in deze categorie al",
            "type": "general",
            "category": "error"
        }), 400

    cur.execute("INSERT INTO user_loot_boxes VALUES (%s, %s, %s, %s)", (user_id, loot_box_id, chosen_item_id, int(time.time())))
    cur.execute("INSERT INTO user_items VALUES (%s, %s, %s, %s)", (user_id, chosen_item_id, box_type, int(time.time())))

    cur.execute("SELECT path, type FROM items WHERE item_id = %s", (chosen_item_id,))
    path = cur.fetchone()[0]

    cur.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (price, user_id))
    cur.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
    balance = cur.fetchone()[0]

    redis_client.hset(f"{redis_prefix}:user:{user_id}", "balance", balance)
    redis_client.expire(f"{redis_prefix}:user:{user_id}", 3600)

    return jsonify({
        "error": False,
        "item": {
            "item_id": chosen_item_id,
            "path": path,
            "price": price
        }
    })
