from flask import Flask, Response, send_from_directory, request, jsonify, send_file
from flask_jwt_extended import JWTManager, jwt_required, verify_jwt_in_request
from auth import auth_bp, init_db
from camera_manager import CameraManager
import eventlet
import base64
from dotenv import load_dotenv
import os
import logging
import threading

# 加载环境变量，用于配置应用的密钥等信息
load_dotenv()

# 配置日志记录，将错误信息记录下来方便后续排查问题
logging.basicConfig(level=logging.DEBUG)  # 调整为 DEBUG 级别以获取更多日志

# 检查环境变量是否设置
SECRET_KEY = os.getenv('SECRET_KEY')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not SECRET_KEY or not JWT_SECRET_KEY:
    logging.error("环境变量 SECRET_KEY 或 JWT_SECRET_KEY 未设置，请检查配置。")
    raise ValueError("环境变量 SECRET_KEY 或 JWT_SECRET_KEY 未设置，请检查配置。")

# 打印密钥信息，方便调试
logging.debug(f"SECRET_KEY: {SECRET_KEY}")
logging.debug(f"JWT_SECRET_KEY: {JWT_SECRET_KEY}")

# 初始化核心应用，指定静态文件夹，用于存放前端的静态资源
app = Flask(__name__, static_folder='../frontend/static')
# 从环境变量中获取密钥，用于应用的安全认证
app.config['SECRET_KEY'] = SECRET_KEY
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

# 注册蓝本，将用户认证相关的路由添加到应用中
app.register_blueprint(auth_bp)

# 初始化JWT，用于实现用户的身份验证和授权
jwt = JWTManager(app)

# 异步支持，使用eventlet实现异步处理，提高应用的性能
eventlet.monkey_patch()

# 数据库操作锁
db_lock = threading.Lock()

try:
    # 初始化摄像头管理器，用于管理摄像头的连接、视频帧获取等操作
    camera_manager = CameraManager()
    logging.info("摄像头管理器初始化成功")
except Exception as e:
    # 若摄像头管理器初始化失败，记录错误信息并抛出异常
    logging.error(f"摄像头管理器初始化失败: {str(e)}")
    raise


@app.route('/')
def index():
    return send_file('../frontend/index.html')


@app.route('/video_feed')
@jwt_required()
def video_feed():
    try:
        logging.info("开始验证 JWT 令牌")
        verify_jwt_in_request()
        logging.info("JWT 令牌验证成功")
    except Exception as e:
        logging.error(f"JWT 验证失败: {str(e)}")
        return jsonify({"msg": "JWT 验证失败"}), 401

    def generate_frame(cam_id):
        try:
            logging.info(f"开始获取摄像头 {cam_id} 的视频帧")
            while True:
                frame = camera_manager.get_frame(cam_id)
                if frame:
                    yield f"data: {base64.b64encode(frame).decode()}\n\n"
                eventlet.sleep(0.1)
        except Exception as e:
            logging.error(f"摄像头 {cam_id} 视频流推送出错: {str(e)}")
        finally:
            pass

    def generate():
        for cam_id in camera_manager.cameras.keys():
            logging.info(f"启动摄像头 {cam_id} 的视频流线程")
            thread = threading.Thread(target=generate_frame, args=(cam_id,))
            thread.daemon = True
            thread.start()

    return Response(generate(), mimetype='text/event-stream')


# 静态资源路由，用于返回前端的静态文件，如CSS、JavaScript等
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory(app.static_folder, path)


@app.route('/toggle_camera', methods=['POST'])
@jwt_required()
def toggle_camera():
    """
    处理摄像头开关控制的路由，需要用户进行身份验证
    :return: 根据操作结果返回相应的JSON消息
    """
    try:
        logging.info("开始处理摄像头开关控制请求")
        verify_jwt_in_request()
        logging.info("JWT 令牌验证成功，继续处理请求")
        data = request.get_json()
        cam_id = data.get('cam_id')
        if cam_id is not None:
            # 调用摄像头管理器的toggle_camera方法切换摄像头的开关状态
            camera_manager.toggle_camera(cam_id)
            logging.info(f"摄像头 {cam_id} 开关状态已切换")
            return jsonify({"msg": "Camera toggled successfully"}), 200
        logging.error("无效的摄像头 ID")
        return jsonify({"msg": "Invalid camera ID"}), 400
    except Exception as e:
        logging.error(f"处理摄像头开关控制请求出错: {str(e)}")
        return jsonify({"msg": "请求处理出错，请稍后重试"}), 500


if __name__ == '__main__':
    try:
        # 初始化数据库
        with db_lock:
            init_db()
        # 启动Flask应用，使用多线程模式，监听端口5000
        app.run(threaded=True, port=5000)
    except Exception as e:
        # 若应用启动出错，记录错误信息
        logging.error(f"应用启动出错: {str(e)}")