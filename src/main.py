import sys
# Prevent the creation of .pyc files
sys.dont_write_bytecode = True

from colorama import Fore as color
from flask import *
from flask_limiter import Limiter
from flask_socketio import SocketIO, send
from functions import *
import bcrypt
import json
import pymysql
import random
import signal
import time
import uuid

app = Flask(__name__, template_folder='../templates', static_folder='../static')

info = open(f"../config.json", "r").read()
info = json.loads(info)
app.secret_key = info['secret_key']

domain = 'https://larsvlaar.nl'

db_host = 'localhost'
db_user = 'larsvlaar.nl'
db_password = info['db_password']
db_name = 'db'

socketio = SocketIO(app)


def connect_to_db(cursorclass=None):
    connection_params = {
        'host': db_host,
        'user': db_user,
        'password': db_password,
        'database': db_name,
        'charset': 'utf8mb4'
    }

    if cursorclass:
        connection_params['cursorclass'] = cursorclass

    return pymysql.connect(**connection_params)


@app.teardown_appcontext
def close_db(error):
    """Close the database connection after each request"""
    try:
        db = g.pop('db', None)
        if db is not None:
            db.close()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")


def set_session_identifier():
    """Used to differentiate different sessions."""
    if session['session_id'] == "":
        session['session_id'] = str(f"{uuid.uuid4()}{time.time_ns()}")
    return session['session_id']


limiter = Limiter(
    app=app,
    key_func=set_session_identifier
)


@app.before_request
def before_request():
    """Set default values for the session."""
    session.setdefault('highscore', 0)
    session.setdefault('score', 0)
    session.setdefault('token', None)
    session.setdefault('logged_in', False)

    session.setdefault('session_id', "")
    set_session_identifier()

    session.setdefault('skins', [])
    session.setdefault('pipeskins', [])
    session.setdefault('backgrounds', [])
    session.setdefault('time_since_last_score_update', 0)
    session.setdefault('username', "")
    session.setdefault('last_message', 0)


@app.route('/db_ddl', methods=['GET'])
@limiter.limit("1 per 10 seconds")
def db_ddl():
    """Export the database schema."""
    try:
        not_allowed_tables = ['clans', 'transactions']

        con = connect_to_db()
        cur = con.cursor()
        cur.execute('SHOW TABLES')
        tables = cur.fetchall()
        db_data = {}
        for table in tables:
            table = table[0]
            if table in not_allowed_tables:
                continue
            cur.execute(f'SHOW CREATE TABLE db.{table}')
            db_data[table] = cur.fetchone()[1]

        data = {
            "status": "Success",
            "data": db_data
        }
        response = make_response(jsonify(data), 200)
        return response
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        data = {
            "status": "Failed",
            "message": "An server error occurred"
        }

        response = make_response(jsonify(data), 500)
        return response


@app.route('/db_export', methods=['GET'])
@limiter.limit("1 per 10 seconds")
def db_export():
    """Export data from a table."""

    try:
        not_allowed_columns = ['password', 'email', 'clan', 'jwt']
        not_allowed_tables = ['clans', 'transactions']

        table = request.args.get('table')
        columns = request.args.get('columns')
        username = request.args.get('username')

        if table in not_allowed_tables and table:
            data = {
                "status": "Failed",
                "message": "Not allowed to export this table"
            }

            response = make_response(jsonify(data), 401)
            return response
        if columns in not_allowed_columns and columns:
            data = {
                "status": "Failed",
                "message": "Not allowed to export these columns"
            }

            response = make_response(jsonify(data), 401)
            return response

        con = connect_to_db()
        cur = con.cursor()

        if not table and not columns and not username:
            """Export the entire database. Except passwords in user table and transactions and clans table."""
            cur.execute('SHOW TABLES')
            tables = cur.fetchall()
            db_data = {}
            for table in tables:
                table = table[0]
                if table == 'users':
                    cur.execute(f'SELECT username, highscore, coins, backgrounds, skins, pipeskins FROM db.{table}')
                elif table in not_allowed_tables:
                    continue
                else:
                    cur.execute(f'SELECT * FROM db.{table}')
                db_data[table] = cur.fetchall()

            data = {
                "status": "Success",
                "data": db_data
            }

            response = make_response(jsonify(data), 200)
            return response

        elif username:
            if columns:
                cur.execute(f'SELECT {columns} FROM db.users WHERE username = %s', (username,))
            else:
                cur.execute(f'SELECT username, highscore, coins, backgrounds, skins, pipeskins FROM db.users WHERE username = %s', (username,))
            db_data = cur.fetchall()

            data = {
                "status": "Success",
                "data": db_data
            }

            response = make_response(jsonify(data), 200)
            return response

        elif table:
            if table == 'users' and not columns:
                cur.execute(f'SELECT username, highscore, coins, backgrounds, skins, pipeskins FROM db.users')

            elif columns:
                cur.execute(f'SELECT {columns} FROM db.{table}')
            else:
                cur.execute(f'SELECT * FROM db.{table}')

            db_data = cur.fetchall()
            data = {
                "status": "Success",
                "data": db_data
            }

            response = make_response(jsonify(data), 200)
            return response

        elif columns:
            data = {
                "status": "Failed",
                "message": "Table is required"
            }

            response = make_response(jsonify(data), 400)
            return response
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        data = {
            "status": "Failed",
            "message": "An server error occurred"
        }

        response = make_response(jsonify(data), 500)
        return response


@app.route('/open_lootbox/<box_id>', methods=['POST'])
@limiter.limit("3 per 10 seconds")
def open_lootbox(box_id):
    """Open a lootbox."""
    if not session['logged_in']:
        return "Error: Not logged in"

    con = connect_to_db()
    cur = con.cursor()
    cur.execute('SELECT coins FROM db.users WHERE username = %s', (session['username'],))
    coins = cur.fetchone()[0]
    cur.execute('SELECT price, odds FROM db.lootboxes WHERE name = %s', (box_id,))
    price, odds = cur.fetchone()

    if coins < price:
        return "Error: Not enough coins"

    winner = open_a_lootbox(box_id, con, cur)
    while winner == "Reroll":
        winner = open_a_lootbox(box_id, con, cur)

    print(winner)

    cur.execute('UPDATE db.users SET coins = coins - %s WHERE username = %s', (price, session['username'],))
    con.commit()
    cur.close()
    con.close()

    return json.dumps({'winner': winner, 'price': price})


@app.route('/get_lootboxes')
def get_lootboxes():
    """Return all lootboxes and their info."""
    con = connect_to_db(cursorclass=pymysql.cursors.DictCursor)
    cur = con.cursor()
    cur.execute('SELECT * FROM db.lootboxes')
    loot_boxes = cur.fetchall()
    return json.dumps(loot_boxes)


@app.route('/messages')
def get_messages():
    """Return the last 250 messages and make sure we only save the most recent 250 messages."""
    check_message_limit()

    con = connect_to_db()
    cur = con.cursor()
    cur.execute("SELECT text FROM messages ORDER BY id DESC LIMIT 250")
    messages = cur.fetchall()
    cur.execute("SELECT username FROM messages ORDER BY id DESC LIMIT 250")
    usernames = cur.fetchall()
    cur.execute("SELECT time FROM messages ORDER BY id DESC LIMIT 250")
    times = cur.fetchall()

    msg_list = []
    for i in range(len(messages)):
        msg_list.append(f"[{time.strftime('%H:%M:%S', time.localtime(times[i][0]))}] {usernames[i][0]}: {messages[i][0]}")
    return jsonify(msg_list)


@socketio.on('message')
def handle_message(msg):
    """Receive a message and save it in the db."""

    if not session['logged_in'] or msg.replace(' ', '') == "":
        return
    if len(msg) > 50:
        send("Error: Character limit of 50 has been exceeded", broadcast=False)
        return

    for bad_word in open(f"{app.static_folder}/bad_words.txt", "r").read().splitlines():
        if bad_word in msg.lower():
            return

    """Enforce a message limit cause limiter doesn't work with websockets."""
    if session['last_message'] != 0 and time.time() - session['last_message'] < 5:
        send(f"Error: Please wait {5-(int(time.time() -session['last_message']))} seconds before sending another message", broadcast=False)
        return
    session['last_message'] = time.time()

    """Save message in db."""
    con = connect_to_db()
    cur = con.cursor()
    cur.execute("INSERT INTO messages (username, text, time) VALUES (%s, %s, %s)", (session['username'], msg, time.time(),))
    con.commit()
    send(f"[{time.strftime('%H:%M:%S', time.localtime(time.time()))}] {session['username']}: {msg}", broadcast=True)


@app.route('/jump', methods=['POST'])
def jump():
    """If someone has a very high score I check if I see this request, if so they probably did not cheat"""
    print(f"jump: {session['username']}")
    return "200"


@app.route('/buy/<category>/<itemID>', methods=['POST'])
@limiter.limit("1 per 3 seconds")
def buy(category, itemID):
    """Buy an item from the shop."""
    if not session['logged_in']:
        return "Error: Not logged in"

    try:
        con = connect_to_db()
        cur = con.cursor()
        cur.execute(f'SELECT price FROM db.{category} WHERE name = %s', (itemID,))
        price = cur.fetchone()[0]

        cur.execute(f'SELECT coins, {category} FROM db.users WHERE username = %s', (session['username'],))
        coins, already_unlocked = cur.fetchone()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"

    if price == -1:
        return "Error: Item not for sale"

    if itemID in already_unlocked:
        return "Error: Already unlocked"

    cur.execute(f'SELECT COUNT(*) FROM db.{category}')
    total_items = cur.fetchone()[0]
    if itemID == 'virgin' and len(already_unlocked.split(',')) != total_items-1:
        return f"Error: Unlock all other {category} first"
    if coins < price:
        return "Error: Not enough coins"

    session[category].append(itemID)
    session.modified = True

    try:
        cur.execute(f'UPDATE db.users SET {category} = %s WHERE username = %s', (json.dumps(session[category]), session['username']))
        cur.execute('UPDATE db.users SET coins = coins - %s WHERE username = %s', (price, session['username']))
        con.commit()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"

    return str(coins-price)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/flappy')
def flappy():
    if not session['logged_in']:
        return render_template('flappy.html', loggedin="false", highscore = -1)
    try:
        con = connect_to_db()
        cur = con.cursor()
        cur.execute('SELECT * FROM db.users WHERE username = %s', (session['username'],))
        user = cur.fetchone()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"

    try:
        highscore = user[2]
        session['backgrounds'] = json.loads(user[4])
        session['skins'] = json.loads(user[5])
        session['pipeskins'] = json.loads(user[6])
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "L"
    coins = user[3]

    return render_template('flappy.html', loggedin="true", username=session['username'], highscore=highscore, coins=coins)


@app.route('/login_form')
def login():
    return render_template('login.html')


@app.route('/register_form')
def register():
    return render_template('register.html')


@app.route('/shop')
def shop():
    if not session['logged_in']:
        return "Error: Not logged in"
    return render_template('shop.html')


@app.route('/inventory')
def inventory():
    if not session['logged_in']:
        return render_template('inventory.html')
    return render_template('inventory.html')


@app.route('/login', methods=['POST'])
def login_post():
    """Log in a user."""
    username = request.get_json()['username']
    password = request.get_json()['password']


    try:
        con = connect_to_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM db.users WHERE username = %s", (username,))
        user = cur.fetchone()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"

    if user is None:
        return "Error: User does not exist"

    """Check if the provided password is correct. If so, log the user in."""
    if bcrypt.checkpw(bytes(password, 'utf-8'), bytes(user[1], 'utf-8')):
        session.clear()
        session['username'] = username
        session['logged_in'] = True
        return "200"
    return "Error: Incorrect password"


@app.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register_post():
    """Register a new user."""
    try:
        username = request.get_json()['username']
        password = request.get_json()['password']
        if len(username) > 30:
            return "Error: Name is too long"

        """
        Hash the password and insert the user into the database if the user does not yet exist.
        """
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            con = connect_to_db()
            cur = con.cursor()
            cur.execute("SELECT * FROM db.users WHERE username = %s", (username,))
            user = cur.fetchone()
            if user is None:
                cur.execute("INSERT INTO db.users (username, password, highscore, coins, backgrounds, skins, pipeskins) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (username, hashed_password, 0, 0, '["kussendeZwarteMannen"]', '["drake"]', '["greenPipe"]',))
                con.commit()
            else:
                return "Error: User already exists"
        except Exception as e:
            print(f"{color.RED}Error: {e}{color.WHITE}")
            return "Error: An error occurred"

        session['username'] = username
        session['logged_in'] = True


        return "200"
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"


@app.route('/died', methods=['POST'])
def died():
    if session['logged_in']:
        highscore = save_highscore()
        session['score'] = 0
        return json.dumps({'score': highscore})

    session['score'] = 0

    return json.dumps({'score': -1})


@app.route('/update_score', methods=['POST'])
@limiter.limit("3 per second")
def update_score():
    """Update the score of the user."""

    if session['logged_in']:
        print(session['username'])

    """
    Check if the token is correct. If not, return an error.
    """
    if request.headers.get('Authorization') != f"t{session['token']}":
        print(f"{color.RED}Token: {request.headers.get('Authorization')}{color.WHITE}")
        print(session['token'])
        abort(401)

    """
    Check if the size is correct. If not, reset the score.
    """
    if request.get_json()['size'] != "11%" and session['username'] != "Ward":
        print(f"L: {request.get_json()['size']}")
        session['score'] = 0
        if session['logged_in']:
            print(session['username'])
        return json.dumps({'score': 'nice try'})

    session['score'] += 1
    session['time_since_last_score_update'] = time.time()

    """
    Check if the user is cheating by not updating the score for a long time.
    """
    if time.time() - session['time_since_last_score_update'] > 5:
        print(f"{color.RED}Took too long: {time.time() - session['time_since_last_score_update']}{color.WHITE}")
        session['score'] = 0
        return json.dumps({'score': 'you a cheater?'})

    return json.dumps({'score': session['score']})


@app.route('/get_token')
def get_token():
    if session['token'] is None:
        session['token'] = str(uuid.uuid4())
    session['score'] = 0
    return json.dumps({'token': session['token']})


@app.route('/suggestions', methods=['POST'])
@limiter.limit("3 per minute")
def suggestions():
    """Save a suggestion to a file."""
    suggestion = request.get_json()['suggestion']
    print(suggestion)
    if len(suggestion) > 300:
        return "Error: Suggestion is too long"
    with open(f'{app.static_folder}/suggestions.txt', 'a') as f:
        f.write(f'{session["username"]}: {suggestion}\n\n')
        f.close()
    return "200"


@app.route('/suggestions_form')
def suggestions_form():
    return render_template('suggestions.html')


@app.route('/clear_session', methods=['POST', 'GET'])
def clear_session():
    session.clear()
    return redirect(url_for('home'))


@app.route('/unlocked')
def unlocked():
    """Return all unlocked items."""
    if not session['logged_in']:
        return "Error: Not logged in"
    return json.dumps({"backgrounds": session['backgrounds'], "skins": session['skins'], "pipeskins": session['pipeskins']})


@app.route('/img/<name>')
def img(name):
    return send_from_directory(app.static_folder, f'img/{name}')


@app.route('/img/shop/<name>')
def shop_img(name):
    """Return the image if the user has unlocked it. If not, return the watermarked image."""
    if name.replace('.jpg', '') not in session['skins'] and name.replace('.jpg', '') not in session['backgrounds'] and name.replace('.jpg', '') not in session['pipeskins']:
        return send_from_directory(app.static_folder, f'img/watermarked/{name}')
    return send_from_directory(app.static_folder, f'img/items/{name}')


@app.route('/img/unlocked/<name>')
def unlocked_img(name):
    """Return the image if the user has unlocked it. If not, return the watermarked image."""
    if not session['logged_in']:
        if name == "drake.jpg" or name == "kussendeZwarteMannen.jpg":
            return send_from_directory(app.static_folder, f'img/items/{name}')

    if name.replace('.jpg', '') not in session['skins'] and name.replace('.jpg', '') not in session['backgrounds'] and name.replace('.jpg', '') not in session['pipeskins']:
        return send_from_directory(app.static_folder, f'img/watermarked/{name}')
    return send_from_directory(app.static_folder, f'img/items/{name}')


@app.route('/js/<name>')
def javascript(name):
    return send_from_directory(app.static_folder, f'js/{name}')


@app.route('/styles')
def styles():
    return send_from_directory(app.static_folder, f'styles.css')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, f'img/favicon.ico')


@app.route('/highscore_leaderboard')
def highscore_leaderboard():
    """Return the top 20 highscores."""
    top_scores = get_top_scores()
    response = make_response(top_scores, 200)
    return response


@app.route('/coins_leaderboard')
def coins_leaderboard():
    """Return the top 20 coin scores."""
    top_scores = get_top_coins()
    response = make_response(top_scores, 200)
    return response


@app.route('/backgrounds')
def backgrounds():
    """Get all backgrounds from the database."""
    try:
        con = connect_to_db()
        cur = con.cursor()
        cur.execute('SELECT * FROM db.backgrounds ORDER BY price ASC')
        items = cur.fetchall()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"
    return json.dumps(items)


@app.route('/skins')
def skins():
    """Get all skins from the database."""
    try:
        con = connect_to_db()
        cur = con.cursor()
        cur.execute('SELECT * FROM db.skins ORDER BY price ASC')
        items = cur.fetchall()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"
    return json.dumps(items)


@app.route('/pipeskins')
def pipeskins():
    """Get all pipeskins from the database."""
    try:
        con = connect_to_db()
        cur = con.cursor()
        cur.execute('SELECT * FROM db.pipeskins ORDER BY price ASC')
        items = cur.fetchall()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"
    return json.dumps(items)


@app.route('/get_flashed_messages')
def messages():
    messages_html = render_template_string("""
        {% for category, message in get_flashed_messages(with_categories=true) %}
            <div class='alert alert-{{ category }}' role='alert'>
                <strong>{{ message }}</strong>
                <button type='button' class='close-btn' aria-label='Close'>&#10006;</button>
            </div>
        {% endfor %}
    """)
    return jsonify({'html': messages_html})


@app.route('/refund', methods=['POST'])
@limiter.limit("1 per 10 minutes")
def refund():
    """Refund a user's purchase."""
    con = connect_to_db()
    cur = con.cursor()
    cur.execute('SELECT backgrounds FROM db.users WHERE username = %s', (session['username'],))
    backgrounds = cur.fetchall()
    cur.execute('SELECT skins FROM db.users WHERE username = %s', (session['username'],))
    skins = cur.fetchall()
    cur.execute('SELECT pipeskins FROM db.users WHERE username = %s', (session['username'],))
    pipeskins = cur.fetchall()

    backgrounds_spent = how_much_spent_backgrounds(backgrounds)
    skins_spent = how_much_spent_skins(skins)
    pipeskins_spent = how_much_spent_pipeskins(pipeskins)
    spent = backgrounds_spent + skins_spent + pipeskins_spent

    cur.execute(f'UPDATE db.users SET coins = coins + %s WHERE username = %s', (spent, session['username'],))
    cur.execute(f'UPDATE db.users SET backgrounds = %s WHERE username = %s', ('["kussendeZwarteMannen"]', session['username'],))
    cur.execute(f'UPDATE db.users SET skins = %s WHERE username = %s', ('["drake"]', session['username'],))
    cur.execute(f'UPDATE db.users SET pipeskins = %s WHERE username = %s', ('["greenPipe"]', session['username'],))
    con.commit()
    return json.dumps({'username': session['username'], 'spent': spent})


def open_a_lootbox(box_id, con, cur):
    """All the logic for opening a lootbox."""
    exclusives = ['greenPipe', 'ogBackground', 'flappyBird', 'zuidToren']

    cur.execute('SELECT odds FROM db.lootboxes WHERE name = %s', (box_id,))
    items = json.loads(cur.fetchone()[0])
    total = 0

    for i in items:
        odd = items[i]
        total += eval(odd)*100

    random_number = random.uniform(0, total)
    winner = None
    for i in items:
        odd = items[i]
        if random_number < eval(odd)*100:
            winner = i
            break
        random_number -= eval(odd)*100

    category = winner.split(' ')[1]
    print(winner)

    if "coins" in winner:
        cur.execute('UPDATE db.users SET coins = coins + %s WHERE username = %s', (winner.split(' ')[0], session['username'],))
        con.commit()
        return winner

    if box_id == "allInOneBox":
        if winner.split(' ')[0] in exclusives or winner.split(' ')[0] in session['backgrounds'] or winner.split(' ')[0] in session['skins'] or winner.split(' ')[0] in session['pipeskins']:
            return "Reroll"

        if "other" in winner:
            cur.execute(f'SELECT * FROM db.backgrounds WHERE price > -1')
            items = cur.fetchall()

            all_unlocked_items = session['backgrounds'] + session['skins'] + session['pipeskins']

            winner = random.choice(items)[0]
            while winner in all_unlocked_items or winner.split(' ')[0] in exclusives:
                winner = random.choice(items)[0]
                if winner.split(' ')[0] in exclusives:
                    continue

        winner = winner.split(' ')[0]

        session['backgrounds'].append(winner)
        session.modified = True
        session['skins'].append(winner)
        session.modified = True
        session['pipeskins'].append(winner)
        session.modified = True

        cur.execute(f'UPDATE db.users SET backgrounds = %s, skins = %s, pipeskins = %s WHERE username = %s',
                    (json.dumps(session['backgrounds']), json.dumps(session['skins']), json.dumps(session['pipeskins']), session['username']))
        con.commit()
        return winner

    elif winner.split(' ')[0] in session[category]:
        return "Reroll"

    if "other" in winner:
        if all_unlocked(category):
            return "You have unlocked all items in this category"
        cur.execute(f'SELECT * FROM db.{category} WHERE price > -1')
        items = cur.fetchall()
        winner = random.choice(items)[0]
        while winner in session[category]:
            winner = random.choice(items)[0]

    winner = winner.split(' ')[0]

    session[category].append(winner)
    session.modified = True

    cur.execute(f'UPDATE db.users SET {category} = %s WHERE username = %s', (json.dumps(session[category]), session['username']))
    con.commit()

    return winner


def all_unlocked(category):
    """Check if all items in a category have been unlocked."""
    con = connect_to_db()
    cur = con.cursor()
    cur.execute(f'SELECT COUNT(*) FROM db.{category}')
    total_items = cur.fetchone()[0]
    return len(session[category]) >= total_items


def check_message_limit():
    """Check and enforce message limit in the database."""
    con = connect_to_db()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM messages")
    result = cur.fetchone()
    message_count = result[0]

    if message_count > 250:
        delete_count = message_count - 250
        cur.execute(f"DELETE FROM messages ORDER BY id ASC LIMIT {delete_count}")
        con.commit()


def how_much_spent_backgrounds(backgrounds):
    """Calculate how much a user has spent on backgrounds."""
    spent = 0
    con = connect_to_db()
    cur = con.cursor()
    cur.execute('SELECT * FROM db.backgrounds')
    all_items = cur.fetchall()
    backgrounds = json.loads(backgrounds[0][0])
    for i in list(backgrounds):
        for j in all_items:
            if i == j[0]:
                spent += j[2]
    return spent


def how_much_spent_pipeskins(pipeskins):
    """Calculate how much a user has spent on pipeskins."""
    spent = 0
    con = connect_to_db()
    cur = con.cursor()
    cur.execute('SELECT * FROM db.pipeskins')
    all_items = cur.fetchall()
    pipeskins = json.loads(pipeskins[0][0])
    for i in list(pipeskins):
        for j in all_items:
            if i == j[0]:
                spent += j[2]
    return spent


def how_much_spent_skins(skins):
    """Calculate how much a user has spent on skins."""
    spent = 0
    con = connect_to_db()
    cur = con.cursor()
    cur.execute('SELECT * FROM db.skins')
    all_items = cur.fetchall()
    skins = json.loads(skins[0][0])
    for i in list(skins):
        for j in all_items:
            if i == j[0]:
                spent += j[2]
    return spent


def get_top_scores():
    """Get the top 20 highscores from the database."""
    try:
        con = connect_to_db()
        cur = con.cursor()
        cur.execute('SELECT highscore, username FROM db.users ORDER BY highscore DESC LIMIT 20')
        top_scores = cur.fetchall()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"
    return json.dumps(top_scores)


def get_top_coins():
    """
    Get the top 20 coin scores from the database.

    First get highest 21, because Admin account has to be removed.
    then remove the Admin account from the list.
    """
    try:
        con = connect_to_db()
        cur = con.cursor()
        cur.execute('SELECT coins, username FROM db.users ORDER BY coins DESC LIMIT 21')
        top_coins = cur.fetchall()
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"

    top_coins = {key: val for key, val in dict(top_coins).items() if val != 'Ward'}

    return json.dumps(tuple(top_coins.items())[:20])


def save_highscore():
    """Save the highscore and coins in the database."""
    try:
        con = connect_to_db()
        cur = con.cursor()
        cur.execute(f'UPDATE db.users SET coins = coins + %s WHERE username = %s', (session['score'], session['username'],))
        con.commit()

        cur.execute('SELECT highscore FROM db.users WHERE username = %s', (session['username'],))
        highscore = cur.fetchone()[0]

        if highscore < session['score']:
            cur.execute('UPDATE db.users SET highscore = %s WHERE username = %s', (session['score'], session['username']))
            con.commit()
            cur.execute('SELECT highscore FROM db.users WHERE username = %s', (session['username'],))
            highscore = cur.fetchone()[0]
            return highscore
        return highscore
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
        return "Error: An error occurred"


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    try:
        app.run(host='127.0.0.1', port=5100, debug=True)
    except Exception as e:
        print(f"{color.RED}Error: {e}{color.WHITE}")
