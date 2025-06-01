try:
    # 尝试导入真实硬件库
    import orangepi.gpio as GPIO
except ImportError:
    # 导入失败，使用模拟类
    class MockGPIO:
        BOARD = 1
        OUT = 2
        HIGH = 1
        LOW = 0

        @staticmethod
        def setmode(mode):
            print(f"[模拟GPIO] 设置模式: {mode}")

        @staticmethod
        def setup(pin, direction, initial=None):
            print(f"[模拟GPIO] 设置引脚 {pin} 方向: {direction}, 初始值: {initial}")

        @staticmethod
        def output(pin, value):
            print(f"[模拟GPIO] 引脚 {pin} 输出: {value}")

        @staticmethod
        def cleanup():
            print("[模拟GPIO] 清理资源")

    class MockPWM:
        def __init__(self, pin, frequency):
            self.pin = pin
            self.frequency = frequency
            print(f"[模拟PWM] 引脚 {pin}, 频率 {frequency}Hz")

        def start(self, duty_cycle):
            print(f"[模拟PWM] 开始输出，占空比 {duty_cycle}%")

        def ChangeDutyCycle(self, duty_cycle):
            print(f"[模拟PWM] 修改占空比为 {duty_cycle}%")

        def stop(self):
            print(f"[模拟PWM] 停止输出")

    GPIO = MockGPIO

    def PWM(pin, frequency):
        return MockPWM(pin, frequency)

import time
import logging
import threading

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobotController:
    def __init__(self, config):
        self.config = config
        self.test_mode = config["test"]["test_mode"]

        if not self.test_mode:
            # 真实硬件初始化
            import orangepi.gpio as GPIO
            # Orange Pi AIpro(20T) GPIO配置（物理引脚编号）
            GPIO.setmode(GPIO.BOARD)

            # 底盘电机控制引脚（根据实际硬件连接调整）
            self.LEFT_MOTOR_FORWARD = 12   # 物理引脚12 (GPIO18)
            self.LEFT_MOTOR_BACKWARD = 16  # 物理引脚16 (GPIO23)
            self.RIGHT_MOTOR_FORWARD = 18  # 物理引脚18 (GPIO24)
            self.RIGHT_MOTOR_BACKWARD = 22 # 物理引脚22 (GPIO25)

            # 机械臂舵机控制引脚（使用支持PWM的引脚）
            self.ARM_BASE_SERVO = 32       # 物理引脚32 (GPIO12, PWM0)
            self.ARM_SHOULDER_SERVO = 33   # 物理引脚33 (GPIO13, PWM1)
            self.ARM_ELBOW_SERVO = 35      # 物理引脚35 (GPIO19, PWM0)
            self.GRIPPER_SERVO = 36        # 物理引脚36 (GPIO16, PWM1)

            # 初始化电机控制引脚
            for pin in [self.LEFT_MOTOR_FORWARD, self.LEFT_MOTOR_BACKWARD,
                        self.RIGHT_MOTOR_FORWARD, self.RIGHT_MOTOR_BACKWARD]:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)

            # 初始化舵机PWM控制
            self.base_pwm = GPIO.PWM(self.ARM_BASE_SERVO, 50)    # 50Hz频率
            self.shoulder_pwm = GPIO.PWM(self.ARM_SHOULDER_SERVO, 50)
            self.elbow_pwm = GPIO.PWM(self.ARM_ELBOW_SERVO, 50)
            self.gripper_pwm = GPIO.PWM(self.GRIPPER_SERVO, 50)

            # 启动PWM，初始占空比为0
            self.base_pwm.start(0)
            self.shoulder_pwm.start(0)
            self.elbow_pwm.start(0)
            self.gripper_pwm.start(0)

            logger.info("机器人控制器初始化完成")
        else:
            # 模拟模式
            print("[模拟] 机器人控制器初始化完成")
            # 创建可视化器
            from arm_visualizer import ArmVisualizer
            self.visualizer = ArmVisualizer()
            # 创建用于显示可视化的线程
            self.visualization_thread = threading.Thread(target=self._run_visualization)
            self.visualization_thread.daemon = True
            self.visualization_thread.start()

    def _run_visualization(self):
        """运行可视化窗口的独立线程"""
        # 初始化可视化窗口
        self.visualizer.show()

    def move_forward(self, duration=1.0, speed=70):
        """控制机器人前进"""
        if self.test_mode:
            logger.info(f"[模拟] 前进 {duration} 秒，速度 {speed}%")
        else:
            logger.info(f"前进 {duration} 秒，速度 {speed}%")

            # 设置电机占空比（需L298N或类似驱动支持PWM调速）
            GPIO.output(self.LEFT_MOTOR_FORWARD, GPIO.HIGH)
            GPIO.output(self.LEFT_MOTOR_BACKWARD, GPIO.LOW)
            GPIO.output(self.RIGHT_MOTOR_FORWARD, GPIO.HIGH)
            GPIO.output(self.RIGHT_MOTOR_BACKWARD, GPIO.LOW)

            time.sleep(duration)
            self.stop()

    def move_backward(self, duration=1.0, speed=70):
        """控制机器人后退"""
        if self.test_mode:
            logger.info(f"[模拟] 后退 {duration} 秒，速度 {speed}%")
        else:
            logger.info(f"后退 {duration} 秒，速度 {speed}%")

            GPIO.output(self.LEFT_MOTOR_FORWARD, GPIO.LOW)
            GPIO.output(self.LEFT_MOTOR_BACKWARD, GPIO.HIGH)
            GPIO.output(self.RIGHT_MOTOR_FORWARD, GPIO.LOW)
            GPIO.output(self.RIGHT_MOTOR_BACKWARD, GPIO.HIGH)

            time.sleep(duration)
            self.stop()

    def turn_left(self, duration=0.5, speed=50):
        """控制机器人左转"""
        if self.test_mode:
            logger.info(f"[模拟] 左转 {duration} 秒，速度 {speed}%")
        else:
            logger.info(f"左转 {duration} 秒，速度 {speed}%")

            GPIO.output(self.LEFT_MOTOR_FORWARD, GPIO.LOW)
            GPIO.output(self.LEFT_MOTOR_BACKWARD, GPIO.HIGH)
            GPIO.output(self.RIGHT_MOTOR_FORWARD, GPIO.HIGH)
            GPIO.output(self.RIGHT_MOTOR_BACKWARD, GPIO.LOW)

            time.sleep(duration)
            self.stop()

    def turn_right(self, duration=0.5, speed=50):
        """控制机器人右转"""
        if self.test_mode:
            logger.info(f"[模拟] 右转 {duration} 秒，速度 {speed}%")
        else:
            logger.info(f"右转 {duration} 秒，速度 {speed}%")

            GPIO.output(self.LEFT_MOTOR_FORWARD, GPIO.HIGH)
            GPIO.output(self.LEFT_MOTOR_BACKWARD, GPIO.LOW)
            GPIO.output(self.RIGHT_MOTOR_FORWARD, GPIO.LOW)
            GPIO.output(self.RIGHT_MOTOR_BACKWARD, GPIO.HIGH)

            time.sleep(duration)
            self.stop()

    def stop(self):
        """停止所有电机"""
        if self.test_mode:
            logger.info("[模拟] 停止所有电机")
        else:
            logger.info("停止所有电机")

            for pin in [self.LEFT_MOTOR_FORWARD, self.LEFT_MOTOR_BACKWARD,
                        self.RIGHT_MOTOR_FORWARD, self.RIGHT_MOTOR_BACKWARD]:
                GPIO.output(pin, GPIO.LOW)

    def set_servo_angle(self, pwm, angle):
        """设置舵机角度"""
        if self.test_mode:
            # 将角度转换为PWM占空比 (2.5%-12.5%)
            duty = 2.5 + (angle / 180) * 10
            print(f"[模拟] 设置舵机角度 {angle} 度，占空比 {duty:.2f}%")
        else:
            # 将角度转换为PWM占空比 (2.5%-12.5%)
            duty = 2.5 + (angle / 180) * 10
            pwm.ChangeDutyCycle(duty)
            time.sleep(0.3)  # 等待舵机转动到位

    def move_arm_to_position(self, position):
        """移动机械臂到指定位置
        position: (base_angle, shoulder_angle, elbow_angle, gripper_angle)
        """
        base_angle, shoulder_angle, elbow_angle, gripper_angle = position

        if self.test_mode:
            logger.info(f"[模拟] 移动机械臂到位置: {position}")
            self.set_servo_angle(None, base_angle)
            self.set_servo_angle(None, shoulder_angle)
            self.set_servo_angle(None, elbow_angle)
            self.set_servo_angle(None, gripper_angle)
        else:
            logger.info(f"移动机械臂到位置: {position}")

            self.set_servo_angle(self.base_pwm, base_angle)
            self.set_servo_angle(self.shoulder_pwm, shoulder_angle)
            self.set_servo_angle(self.elbow_pwm, elbow_angle)
            self.set_servo_angle(self.gripper_pwm, gripper_angle)

    def move_towards_ball(self, horizontal_offset, distance):
        if self.test_mode:
            print(f"[模拟] 移动向网球 - 水平偏移: {horizontal_offset:.1f}%, 距离: {distance:.1f}cm")

            # 计算移动参数
            left_speed = 70 + horizontal_offset/5
            right_speed = 70 - horizontal_offset/5
            move_time = distance/20

            print(f"[模拟] 左电机: {left_speed:.1f}%, 右电机: {right_speed:.1f}%, 时间: {move_time:.2f}秒")

            # 模拟移动过程中的机械臂姿态变化
            for i in range(10):
                progress = i / 10
                # 计算网球位置（简化模型）
                ball_x = horizontal_offset * 0.3 * (1 - progress)
                ball_y = 50 - distance * (1 - progress)

                # 更新机械臂姿态（简化模型）
                shoulder_angle = 90 - horizontal_offset * 0.3 * (1 - progress)
                elbow_angle = distance * 0.5 * (1 - progress)

                self.visualizer.update_arm(shoulder_angle, elbow_angle, True, (ball_x, ball_y))
                time.sleep(0.1)  # 使用 time.sleep 代替 plt.pause
        else:
            # 真实硬件控制
            # 这里需要根据实际情况补充真实硬件控制代码
            pass

    def collect_ball(self):
        if self.test_mode:
            print("[模拟] 执行捡球动作")

            # 模拟捡球过程
            # 1. 下降到收集位置
            for i in range(10):
                shoulder_angle = 90 - i * 3
                elbow_angle = i * 6
                self.visualizer.update_arm(shoulder_angle, elbow_angle, True, (0, 10))
                time.sleep(0.1)

            # 2. 闭合夹爪
            self.visualizer.update_arm(shoulder_angle, elbow_angle, False, (0, 10))
            time.sleep(0.5)

            # 3. 上升
            for i in range(10):
                shoulder_angle = 60 + i * 3
                elbow_angle = 60 - i * 2
                self.visualizer.update_arm(shoulder_angle, elbow_angle, False, (0, 10))
                time.sleep(0.1)