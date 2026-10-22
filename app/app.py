import os
import socket

import redis
from flask import Flask, jsonify

app = Flask(__name__)

# підключення до БД за DNS-іменем сервісу
db = redis.Redis(
    host=os.environ.get("REDIS_HOST", "db"),
    port=6379,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)


@app.get("/")
def index():
    try:
        # кожен запит збільшує лічильник у Redis
        hits = db.incr("lab:hits")
        return jsonify(hits=hits, instance=socket.gethostname())
    except redis.exceptions.RedisError:
        return jsonify(error="database unavailable"), 503


@app.get("/health")
def health():
    try:
        # перевірка зв'язку з БД для healthcheck
        db.ping()
        return jsonify(status="ok")
    except redis.exceptions.RedisError:
        return jsonify(error="database unavailable"), 503
