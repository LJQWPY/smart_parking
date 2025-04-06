import cv2
import torch
from ultralytics import YOLO

class ParkingSpotDetector:
    def __init__(self):
        """
        初始化车位检测模块，根据系统环境选择使用CUDA或CPU，并加载YOLOv8n模型
        """
        try:
            # 检查CUDA是否可用，若可用则使用GPU进行计算，否则使用CPU
            device = 0 if torch.cuda.is_available() else 'cpu'
            # 加载YOLOv8n模型
            self.model = YOLO('yolov8n.pt')
            # 将模型移动到指定设备上
            self.model.to(device)
        except Exception as e:
            import logging
            logging.error(f"模型加载出错: {str(e)}，错误类型: {type(e).__name__}")

    def detect_objects(self, frame):
        """
        使用YOLOv8n模型对输入的视频帧进行目标检测
        :param frame: 输入的视频帧
        :return: 检测到的目标信息列表，包含目标的边界框坐标和类别ID
        """
        try:
            # 使用YOLOv8n模型进行检测
            results = self.model(frame)
            # 存储检测到的目标信息
            detected_objects = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # 获取目标的边界框坐标
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    # 获取目标的类别ID
                    class_id = int(box.cls[0])
                    # 将目标信息添加到列表中
                    detected_objects.append((x1, y1, x2, y2, class_id))
            return detected_objects
        except Exception as e:
            import logging
            logging.error(f"目标检测出错: {str(e)}，错误类型: {type(e).__name__}")
            return []
    