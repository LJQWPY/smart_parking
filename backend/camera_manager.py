# camera_manager.py (修复后完整代码)
import cv2
import threading
from detector import ParkingSpotDetector


class CameraManager:
    def __init__(self, sources):
        self.cameras = {}
        self.frame_lock = threading.Lock()

        for idx, source in enumerate(sources):
            try:
                # 添加分辨率设置
                cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

                if not cap.isOpened():
                    print(f"⚠️ 警告：无法打开摄像头 {source}，已跳过")
                    continue  # 跳过不可用摄像头

                self.cameras[idx] = {
                    'cap': cap,
                    'detector': ParkingSpotDetector(),
                    'active': True
                }
            except Exception as e:
                print(f"摄像头 {source} 初始化失败：{str(e)}")

    def get_frames(self):
        frames = {}
        with self.frame_lock:
            for cam_id, cam in self.cameras.items():
                if cam['active']:
                    ret, frame = cam['cap'].read()
                    if ret:
                        cam['detector'].check_occupancy(frame)
                        cam['detector'].draw_parking_spots(frame)
                        _, jpeg = cv2.imencode('.jpg', frame)
                        frames[cam_id] = jpeg.tobytes()
        return frames

    # ==== 新增方法：安全释放资源 ====
    def release(self):
        with self.frame_lock:
            for cam in self.cameras.values():
                cam['cap'].release()