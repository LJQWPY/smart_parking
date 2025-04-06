from flask import Blueprint, request, jsonify
import sqlite3
import bcrypt
import logging
import threading

# 配置日志记录，将错误信息记录下来方便后续排查问题
logging.basicConfig(level=logging.ERROR)

# 创建一个蓝图，用于管理用户认证相关的路由
auth_bp = Blueprint('auth', __name__)

# 数据库操作锁
db_lock = threading.Lock()

def init_db():
    """
    初始化数据库，创建用户表
    """
    try:
        with db_lock:
            # 连接到SQLite数据库
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            # 创建用户表，包含用户名和密码字段
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (username TEXT PRIMARY KEY, password TEXT)''')
            # 提交数据库操作
            conn.commit()
            # 关闭数据库连接
            conn.close()
    except Exception as e:
        # 若数据库初始化出错，记录详细错误信息
        logging.error(f"数据库初始化出错: {str(e)}，错误类型: {type(e).__name__}")


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    处理用户注册请求的路由
    :return: 根据注册结果返回相应的JSON消息
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password').encode()
    # 使用bcrypt对密码进行加密
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())

    try:
        with db_lock:
            # 连接到SQLite数据库
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            # 将用户信息插入到用户表中
            c.execute("INSERT INTO users VALUES (?, ?)", (username, hashed))
            # 提交数据库操作
            conn.commit()
            return jsonify({"msg": "User created", "status": 201}), 201
    except sqlite3.IntegrityError:
        # 若用户名已存在，返回错误消息
        return jsonify({"msg": "Username exists", "status": 400}), 400
    except Exception as e:
        # 若数据库操作出错，记录详细错误信息并返回错误消息
        logging.error(f"数据库操作出错: {str(e)}，错误类型: {type(e).__name__}")
        return jsonify({"msg": "Database error", "status": 500}), 500
    finally:
        if conn:
            # 关闭数据库连接
            conn.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    处理用户登录请求的路由
    :return: 根据登录结果返回相应的JSON消息或JWT令牌
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password').encode()

    try:
        with db_lock:
            # 连接到SQLite数据库
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            # 从用户表中查询指定用户名的用户信息
            c.execute("SELECT * FROM users WHERE username=?", (username,))
            user = c.fetchone()
            # 关闭数据库连接
            conn.close()
    except Exception as e:
        # 若数据库操作出错，记录详细错误信息并返回错误消息
        logging.error(f"数据库操作出错: {str(e)}，错误类型: {type(e).__name__}")
        return jsonify({"msg": "Database error", "status": 500}), 500

    if user and bcrypt.checkpw(password, user[1]):
        from flask_jwt_extended import create_access_token
        # 若用户名和密码匹配，生成JWT令牌
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)
    # 若用户名或密码不匹配，返回错误消息
    return jsonify({"msg": "Invalid credentials", "status": 401}), 401

    