import cv2
import numpy as np
import time
import logging
from robot_controller import RobotController

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TennisBallCollector:
    def __init__(self):
        # 初始化机器人控制器
        self.controller = RobotController()
        
        # 初始化摄像头（优先使用CSI接口，根据实际情况调整）
        try:
            # 尝试使用CSI摄像头（需安装libcamera和相关驱动）
            from picamera2 import Picamera2
            self.cap = Picamera2()
            self.cap.configure(self.cap.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
            self.cap.start()
            self.camera_type = "csi"
            logger.info("成功使用CSI摄像头")
        except:
            # 回退到USB摄像头
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                logger.error("无法打开摄像头")
                raise Exception("无法初始化摄像头")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera_type = "usb"
            logger.info("使用USB摄像头")
        
        # 图像处理参数
        self.lower_yellow = np.array([20, 100, 100])  # HSV黄色下界
        self.upper_yellow = np.array([40, 255, 255])  # HSV黄色上界
        self.min_ball_radius = 10  # 最小网球半径(像素)
        self.max_ball_radius = 100  # 最大网球半径(像素)
        self.focal_length = 800  # 相机焦距(像素)
        self.known_ball_diameter = 6.7  # 网球实际直径(cm)
        
        # 机器人状态
        self.STATE_SEARCHING = "SEARCHING"  # 搜索网球
        self.STATE_MOVING = "MOVING"        # 向网球移动
        self.STATE_COLLECTING = "COLLECTING"  # 收集网球
        self.STATE_RETURNING = "RETURNING"  # 返回起点
        
        self.current_state = self.STATE_SEARCHING
        self.balls_collected = 0
        
        logger.info("网球收集器初始化完成")
    
    def capture_frame(self):
        """捕获一帧图像"""
        if self.camera_type == "csi":
            return self.cap.capture_array()
        else:
            ret, frame = self.cap.read()
            if not ret:
                logger.error("无法捕获图像")
                return None
            return frame
    
    def preprocess_image(self, frame):
        """预处理图像，准备网球检测"""
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 高斯模糊，减少噪声
        blurred = cv2.GaussianBlur(hsv, (5, 5), 0)
        
        # 创建黄色掩码
        mask = cv2.inRange(blurred, self.lower_yellow, self.upper_yellow)
        
        # 形态学操作，消除小噪声点，填充小孔
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # 开运算：先腐蚀后膨胀
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # 闭运算：先膨胀后腐蚀
        
        return mask, frame
    
    def detect_tennis_balls(self, frame):
        """检测图像中的网球"""
        mask, original = self.preprocess_image(frame)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_balls = []
        
        for contour in contours:
            # 计算轮廓面积
            area = cv2.contourArea(contour)
            
            # 过滤小面积轮廓
            if area < 100:
                continue
            
            # 计算轮廓的最小包围圆
            ((x, y), radius) = cv2.minEnclosingCircle(contour)
            
            # 计算轮廓的矩
            M = cv2.moments(contour)
            
            # 计算轮廓的中心点
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX, cY = 0, 0
            
            # 过滤不符合大小的圆
            if self.min_ball_radius <= radius <= self.max_ball_radius:
                detected_balls.append(((cX, cY), radius))
                
                # 在原图上绘制圆和中心点
                cv2.circle(original, (int(x), int(y)), int(radius), (0, 255, 0), 2)
                cv2.circle(original, (cX, cY), 5, (0, 0, 255), -1)
                cv2.putText(original, f"Ball {len(detected_balls)}", (int(x) - 20, int(y) - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return detected_balls, original
    
    def calculate_distance(self, radius):
        """根据网球半径计算距离(cm)"""
        return (self.known_ball_diameter * self.focal_length) / (2 * radius)
    
    def calculate_offset(self, center):
        """计算网球中心与图像中心的水平偏移(cm)"""
        image_center_x = 320  # 640x480图像的中心x坐标
        pixel_offset = center[0] - image_center_x
        
        # 将像素偏移转换为实际距离偏移
        # 假设图像中心对应实际距离0cm
        distance_per_pixel = self.known_ball_diameter / (2 * self.focal_length)
        return pixel_offset * distance_per_pixel
    
    def search_for_balls(self):
        """搜索网球（旋转底盘）"""
        logger.info("搜索网球中...")
        self.controller.turn_left(0.3)  # 每次旋转一小段角度
    
    def move_towards_ball(self, offset, distance):
        """向网球移动"""
        logger.info(f"向网球移动: 偏移={offset:.2f}cm, 距离={distance:.2f}cm")
        
        # 补偿水平偏移
        if offset < -5:  # 网球在左侧
            self.controller.turn_left(0.1)
        elif offset > 5:  # 网球在右侧
            self.controller.turn_right(0.1)
        
        # 向前移动（根据距离调整移动时间）
        move_time = min(distance / 50, 2.0)  # 限制最大移动时间
        self.controller.move_forward(move_time)
    
    def run(self):
        """运行网球收集器"""
        logger.info("开始运行网球收集器")
        
        try:
            while True:
                # 捕获图像
                frame = self.capture_frame()
                if frame is None:
                    continue
                
                # 检测网球
                balls, processed_frame = self.detect_tennis_balls(frame)
                
                # 显示状态信息
                cv2.putText(processed_frame, f"State: {self.current_state}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(processed_frame, f"Balls collected: {self.balls_collected}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # 显示处理后的图像
                cv2.imshow("Tennis Ball Collector", processed_frame)
                
                # 状态机逻辑
                if self.current_state == self.STATE_SEARCHING:
                    if balls:
                        # 找到网球，选择最大的一个
                        largest_ball = max(balls, key=lambda x: x[1])
                        ball_center, ball_radius = largest_ball
                        
                        # 计算距离和偏移
                        distance = self.calculate_distance(ball_radius)
                        offset = self.calculate_offset(ball_center)
                        
                        logger.info(f"找到网球: 半径={ball_radius:.2f}px, 距离={distance:.2f}cm, 偏移={offset:.2f}cm")
                        
                        if distance > 30:  # 如果距离大于30cm，向网球移动
                            self.current_state = self.STATE_MOVING
                        else:  # 距离足够近，开始收集
                            self.current_state = self.STATE_COLLECTING
                    else:
                        # 没找到网球，继续搜索
                        self.search_for_balls()
                
                elif self.current_state == self.STATE_MOVING:
                    if balls:
                        largest_ball = max(balls, key=lambda x: x[1])
                        ball_center, ball_radius = largest_ball
                        distance = self.calculate_distance(ball_radius)
                        offset = self.calculate_offset(ball_center)
                        
                        self.move_towards_ball(offset, distance)
                        
                        # 移动后重新评估距离
                        if distance <= 30:
                            self.current_state = self.STATE_COLLECTING
                    else:
                        # 移动过程中丢失目标，返回搜索状态
                        self.current_state = self.STATE_SEARCHING
                
                elif self.current_state == self.STATE_COLLECTING:
                    # 执行捡球操作
                    self.controller.collect_ball()
                    self.balls_collected += 1
                    logger.info(f"成功收集第{self.balls_collected}个网球")
                    
                    # 捡球后返回搜索状态
                    self.current_state = self.STATE_SEARCHING
                
                # 按'q'键退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                # 短暂延时，降低CPU使用率
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"发生异常: {str(e)}")
        finally:
            # 释放资源
            logger.info("释放资源并退出")
            self.controller.cleanup()
            if self.camera_type == "csi":
                self.cap.stop()
            else:
                self.cap.release()
            cv2.destroyAllWindows()

# 主程序入口
if __name__ == "__main__":
    collector = TennisBallCollector()
    collector.run()    