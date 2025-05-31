# main.py
import json
import cv2
import time
from tennis_ball_detector import TennisBallDetector
from robot_controller import RobotController

class TennisBallCollector:
    def __init__(self, config_path="config.json"):
        # 加载配置
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # 初始化检测器
        self.detector = TennisBallDetector(self.config)
        
        # 初始化控制器（在测试模式下不使用）
        if not self.config["test"]["test_mode"]:
            self.controller = RobotController(self.config)
        
        # 初始化摄像头
        if not self.config["test"]["test_mode"]:
            camera_type = self.config["hardware"]["camera_type"]
            if camera_type == "csi":
                # CSI摄像头配置
                self.cap = cv2.VideoCapture(
                    "nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1280, height=720, format=(string)NV12, framerate=(fraction)30/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! appsink",
                    cv2.CAP_GSTREAMER
                )
            else:
                # USB摄像头配置
                self.cap = cv2.VideoCapture(0)
                
            if not self.cap.isOpened():
                raise Exception("无法打开摄像头")
        
        # 状态机
        self.STATE_SEARCHING = "SEARCHING"
        self.STATE_MOVING = "MOVING"
        self.STATE_COLLECTING = "COLLECTING"
        self.current_state = self.STATE_SEARCHING
        
        # 性能统计
        self.frame_count = 0
        self.start_time = time.time()
    
    def run(self):
        """运行主循环"""
        if self.config["test"]["test_mode"]:
            print("运行测试模式...")
            self.detector.run_image_tests()
            return
            
        print("启动自动捡网球机器人...")
        
        try:
            while True:
                # 读取一帧图像
                ret, frame = self.cap.read()
                if not ret:
                    print("无法获取图像，退出...")
                    break
                
                # 检测网球
                balls, processed_frame = self.detector.detect_tennis_balls(frame)
                
                # 根据检测结果执行相应动作
                self._process_detection_results(balls)
                
                # 显示处理后的图像
                cv2.imshow("Tennis Ball Collector", processed_frame)
                
                # 按ESC键退出
                key = cv2.waitKey(1)
                if key == 27:
                    break
                
                # 更新性能统计
                self.frame_count += 1
                if self.frame_count % 100 == 0:
                    fps = self.frame_count / (time.time() - self.start_time)
                    print(f"处理速度: {fps:.1f} FPS")
                    
        except KeyboardInterrupt:
            print("用户中断，退出...")
        finally:
            # 释放资源
            if not self.config["test"]["test_mode"]:
                self.cap.release()
            cv2.destroyAllWindows()
            if not self.config["test"]["test_mode"]:
                self.controller.cleanup()
    
    def _process_detection_results(self, balls):
        """根据检测结果执行相应动作"""
        if not balls:
            # 没有检测到网球，进入搜索状态
            self.current_state = self.STATE_SEARCHING
            if not self.config["test"]["test_mode"]:
                self.controller.search_for_balls()
            return
            
        # 获取最大的网球（最可能是最近的）
        largest_ball = max(balls, key=lambda b: b[1])
        (x, y), radius, distance, horizontal_offset = largest_ball
        
        if distance > self.config["robot_control"]["collect_distance"]:
            # 距离大于收集距离，向网球移动
            self.current_state = self.STATE_MOVING
            if not self.config["test"]["test_mode"]:
                self.controller.move_towards_ball(horizontal_offset, distance)
        else:
            # 距离足够近，收集网球
            self.current_state = self.STATE_COLLECTING
            if not self.config["test"]["test_mode"]:
                self.controller.collect_ball()
        
        print(f"状态: {self.current_state}, 距离: {distance:.1f}cm, 偏移: {horizontal_offset:.1f}%")

if __name__ == "__main__":
    collector = TennisBallCollector()
    collector.run()

    #194，185，40