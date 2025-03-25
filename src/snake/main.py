import pymysql
import json
import redis


def connect_to_db(cursorclass=None):
    connection_params = {
        'host': config["DB"]["HOST"],
        'user': config["DB"]["USER"],
        'password': config["DB"]["PASSWORD"],
        'database': config["DB"]["NAME"],
        'charset': 'utf8mb4'
    }

    if cursorclass:
        connection_params['cursorclass'] = cursorclass

    return pymysql.connect(**connection_params)


boodschappen_lijstje = [
    "Groente of fruit in blik",
    "Broodbeleg",
    "Ontbijtkoek",
    "Couscous",
    "Zilvervlies of meergranen rijst",
    "Houdbare pasta",
    "Pastasaus",
    "Beschuit",
    "Smeerkaas",
    "Koffie en thee",
    "Chocoladerepen",
    "Maaltijdsoepen",
    "Mayonaise",
    "Mosterd",
    "Vruchtensap",
    "Toiletpapier",
    "Keukenrol"
]

config = json.loads(open("../../config/config.json").read())
redis_client = redis.Redis(host=config["REDIS"]["HOST"], port=config["REDIS"]["PORT"], db=0, password=config["REDIS"]["PASSWORD"], charset="utf-8", decode_responses=True)
