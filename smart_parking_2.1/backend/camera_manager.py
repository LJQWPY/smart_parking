import cv2
import threading
import logging

# 配置日志记录，将错误信息记录下来方便后续排查问题
logging.basicConfig(level=logging.ERROR)


class CameraManager:
    def __init__(self):
        """
        初始化摄像头管理器，检测可用摄像头并初始化相关信息
        """
        self.cameras = {}
        # 用于线程安全的锁，确保在多线程环境下对摄像头信息的操作安全
        self.frame_lock = threading.Lock()
        # 检测可用的摄像头
        self.detect_available_cameras()

    def detect_available_cameras(self):
        """
        检测系统中可用的摄像头，并将其信息存储在cameras字典中
        """
        index = 0
        while True:
            # 尝试打开指定索引的摄像头
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap.read()[0]:
                # 若无法读取视频帧，说明该摄像头不可用，退出循环
                break
            else:
                # 设置摄像头的分辨率
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                # 将可用摄像头的信息存储在cameras字典中
                self.cameras[index] = {
                    'cap': cap,
                    'detector': None,
                    'active': True
                }
            # 释放摄像头资源
            cap.release()
            index += 1

    def get_frame(self, cam_id):
        """
        获取指定摄像头的视频帧
        :param cam_id: 摄像头的ID
        :return: 视频帧数据
        """
        with self.frame_lock:
            if cam_id in self.cameras and self.cameras[cam_id]['active']:
                ret, frame = self.cameras[cam_id]['cap'].read()
                if ret:
                    _, buffer = cv2.imencode('.jpg', frame)
                    return buffer.tobytes()
        return None

    def get_frames(self):
        """
        获取所有可用摄像头的视频帧
        :return: 包含摄像头ID和对应视频帧数据的字典
        """
        frames = {}
        with self.frame_lock:
            for cam_id, cam_info in self.cameras.items():
                if cam_info['active']:
                    ret, frame = cam_info['cap'].read()
                    if ret:
                        _, buffer = cv2.imencode('.jpg', frame)
                        frames[cam_id] = buffer.tobytes()
        return frames

    def release(self):
        """
        释放所有可用摄像头的资源
        """
        with self.frame_lock:
            for cam_info in self.cameras.values():
                if cam_info['active']:
                    cam_info['cap'].release()

    def toggle_camera(self, cam_id):
        """
        切换指定摄像头的开关状态
        :param cam_id: 摄像头的ID
        """
        with self.frame_lock:
            if cam_id in self.cameras:
                self.cameras[cam_id]['active'] = not self.cameras[cam_id]['active']
                if self.cameras[cam_id]['active']:
                    self.cameras[cam_id]['cap'] = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
                    self.cameras[cam_id]['cap'].set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cameras[cam_id]['cap'].set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                else:
                    self.cameras[cam_id]['cap'].release()
    