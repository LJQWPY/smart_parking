from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import sqlite3
import hashlib

auth_bp = Blueprint('auth', __name__)


def init_db():
    """初始化数据库函数"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, 
                  password TEXT)''')
    conn.commit()
    conn.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = hashlib.sha256(data.get('password').encode()).hexdigest()

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)
    return jsonify({"msg": "Invalid credentials"}), 401


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = hashlib.sha256(data.get('password').encode()).hexdigest()

    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
        conn.commit()
        return jsonify({"msg": "User created"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"msg": "Username exists"}), 400
    finally:
        conn.close()