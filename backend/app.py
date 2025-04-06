from flask import Flask, Response
from flask_jwt_extended import JWTManager, jwt_required
from auth import auth_bp, init_db
from camera_manager import CameraManager
import eventlet
import base64

# 初始化核心应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secure_secret_key_here'
app.config['JWT_SECRET_KEY'] = 'jwt_special_secret_2024'

# 注册蓝本
app.register_blueprint(auth_bp)

# 初始化JWT
jwt = JWTManager(app)

# 异步支持
eventlet.monkey_patch()
camera_manager = CameraManager([0])

@app.route('/video_feed')
@jwt_required()
def video_feed():
    def generate():
        while True:
            frames = camera_manager.get_frames()
            for cam_id, frame in frames.items():
                yield f"data: {base64.b64encode(frame).decode()}\n\n"
            eventlet.sleep(0.1)
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    init_db()
    app.run(threaded=True, port=5000)