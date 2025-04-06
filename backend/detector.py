import cv2
import numpy as np
import torch
from ultralytics import YOLO
import time
import threading


class ParkingSpotDetector:
    def __init__(self, model_path='yolov8n.pt', use_half_precision=False):
        # 自动检测硬件环境
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = YOLO(model_path).to(self.device)

        # 半精度模式仅在GPU可用时启用
        if use_half_precision and self.device == 'cuda':
            self.model = self.model.half()

        # 停车位配置
        self.parking_spots = []
        self.last_redetect_time = 0
        self.redetect_interval = 30  # 重检测间隔（秒）

        # 图像处理参数
        self.min_area = 2000
        self.max_area = 10000
        self.dilation_kernel = np.ones((3, 3), np.uint8)
        self.lock = threading.Lock()

    def auto_detect_spots(self, frame):
        """自动检测停车位区域"""
        with self.lock:
            # 图像预处理
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 50, 150)

            # 形态学操作
            dilated = cv2.dilate(edges, self.dilation_kernel, iterations=2)

            # 查找并筛选轮廓
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            self.parking_spots = []

            for idx, cnt in enumerate(contours):
                area = cv2.contourArea(cnt)
                if self.min_area < area < self.max_area:
                    x, y, w, h = cv2.boundingRect(cnt)
                    self.parking_spots.append({
                        "id": f"{id(self)}_{idx}",
                        "coords": [x, y, x + w, y + h],
                        "occupied": False,
                        "confidence": 0.0
                    })
            return self.parking_spots

    def check_occupancy(self, frame):
        """检测车位占用状态"""
        with self.lock:
            # 动态重检测机制
            current_time = time.time()
            if current_time - self.last_redetect_time > self.redetect_interval:
                self.auto_detect_spots(frame)
                self.last_redetect_time = current_time

            # 执行推理
            results = self.model(frame, verbose=False, device=self.device)

            # 状态衰减
            for spot in self.parking_spots:
                spot["confidence"] *= 0.5

            # 处理检测结果
            for result in results:
                for box in result.boxes:
                    if int(box.cls) not in [2, 3, 5, 7]:  # 车辆类别过滤
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    # 多条件碰撞检测
                    for spot in self.parking_spots:
                        sx1, sy1, sx2, sy2 = spot["coords"]
                        point_inside = (sx1 < cx < sx2) and (sy1 < cy < sy2)

                        # 计算IoU
                        inter_w = min(x2, sx2) - max(x1, sx1)
                        inter_h = min(y2, sy2) - max(y1, sy1)
                        intersection = max(0, inter_w) * max(0, inter_h)
                        vehicle_area = (x2 - x1) * (y2 - y1)
                        iou = intersection / vehicle_area if vehicle_area > 0 else 0

                        if point_inside or iou > 0.3:
                            spot["confidence"] = min(1.0, spot["confidence"] + 0.3)

                        spot["occupied"] = spot["confidence"] > 0.7
            return self.parking_spots

    def draw_parking_spots(self, frame):
        """可视化绘制"""
        with self.lock:
            for spot in self.parking_spots:
                color = (0, 0, 255) if spot["occupied"] else (0, 255, 0)
                x1, y1, x2, y2 = spot["coords"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, str(spot["id"]), (x1 + 5, y1 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            return frame


class MultiCameraManager:
    """多摄像头管理类"""

    def __init__(self, video_sources):
        self.cameras = {}
        self.lock = threading.Lock()

        # 初始化每个摄像头
        for idx, source in enumerate(video_sources):
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                raise RuntimeError(f"无法打开摄像头 {source}")

            self.cameras[idx] = {
                "cap": cap,
                "detector": ParkingSpotDetector(),
                "last_frame": None,
                "active": True
            }

    def get_all_frames(self):
        """获取所有摄像头帧"""
        frames = {}
        with self.lock:
            for cam_id, cam in self.cameras.items():
                if cam["active"]:
                    ret, frame = cam["cap"].read()
                    if ret:
                        cam["detector"].check_occupancy(frame)
                        cam["last_frame"] = cam["detector"].draw_parking_spots(frame)
                        frames[cam_id] = cam["last_frame"]
        return frames

    def release(self):
        """释放资源"""
        with self.lock:
            for cam in self.cameras.values():
                cam["cap"].release()


if __name__ == "__main__":
    # 测试代码
    manager = MultiCameraManager([0])
    try:
        while True:
            frames = manager.get_all_frames()
            for cam_id, frame in frames.items():
                cv2.imshow(f"Camera {cam_id}", frame)
            if cv2.waitKey(1) == 27:
                break
    finally:
        manager.release()
        cv2.destroyAllWindows()