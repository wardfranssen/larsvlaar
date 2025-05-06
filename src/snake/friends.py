from src.snake.wrapper_funcs import *
import src.snake.main as main


@db_connection()
def has_friend_request_from_user(con, cur, from_user_id: str, to_user_id: str) -> bool:
    cur.execute("SELECT id FROM friend_requests WHERE from_user_id = %s AND to_user_id = %s LIMIT 1", (from_user_id, to_user_id))
    result = cur.fetchone()

    if not result:
        return False

    return True


@db_connection()
def remove_friend_request(con, cur, from_user_id: str, to_user_id: str) -> dict:
    has_friend_request = has_friend_request_from_user(from_user_id, to_user_id)
    if not has_friend_request:
        return {
            "error": True,
            "message": "Geen vriendschapsverzoek van deze gebruiker",
            "category": "error",
            "type": "general",
        }

    cur.execute("DELETE FROM friend_requests WHERE from_user_id = %s AND to_user_id = %s", (from_user_id, to_user_id))
    con.commit()

    return {
        "error": False
    }


@db_connection()
def are_already_friends(con, cur, from_user_id: str, to_user_id: str) -> bool:
    cur.execute("SELECT id FROM friends WHERE (user1_id = %s AND user2_id = %s) OR (user1_id = %s AND user2_id = %s) LIMIT 1", (from_user_id, to_user_id, to_user_id, from_user_id))
    result = cur.fetchone()

    if result:
        return True
    return False


def parse_friend_requests(users: tuple) -> dict:
    friend_requests = {}
    for user in users:
        friend_request = {}

        user_id = user[0]
        created_at = user[1]

        friend_request["username"] = main.get_username(user_id)
        friend_request["pfp_version"] = main.get_pfp_version(user_id)
        friend_request["status"] = main.get_status(user_id)
        friend_request["created_at"] = created_at

        friend_requests[user_id] = friend_request

    return friend_requests
