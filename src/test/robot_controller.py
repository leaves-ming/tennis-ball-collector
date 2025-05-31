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

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobotController:
    def __init__(self):
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
    
    def move_forward(self, duration=1.0, speed=70):
        """控制机器人前进"""
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
        logger.info(f"后退 {duration} 秒，速度 {speed}%")
        
        GPIO.output(self.LEFT_MOTOR_FORWARD, GPIO.LOW)
        GPIO.output(self.LEFT_MOTOR_BACKWARD, GPIO.HIGH)
        GPIO.output(self.RIGHT_MOTOR_FORWARD, GPIO.LOW)
        GPIO.output(self.RIGHT_MOTOR_BACKWARD, GPIO.HIGH)
        
        time.sleep(duration)
        self.stop()
    
    def turn_left(self, duration=0.5, speed=50):
        """控制机器人左转"""
        logger.info(f"左转 {duration} 秒，速度 {speed}%")
        
        GPIO.output(self.LEFT_MOTOR_FORWARD, GPIO.LOW)
        GPIO.output(self.LEFT_MOTOR_BACKWARD, GPIO.HIGH)
        GPIO.output(self.RIGHT_MOTOR_FORWARD, GPIO.HIGH)
        GPIO.output(self.RIGHT_MOTOR_BACKWARD, GPIO.LOW)
        
        time.sleep(duration)
        self.stop()
    
    def turn_right(self, duration=0.5, speed=50):
        """控制机器人右转"""
        logger.info(f"右转 {duration} 秒，速度 {speed}%")
        
        GPIO.output(self.LEFT_MOTOR_FORWARD, GPIO.HIGH)
        GPIO.output(self.LEFT_MOTOR_BACKWARD, GPIO.LOW)
        GPIO.output(self.RIGHT_MOTOR_FORWARD, GPIO.LOW)
        GPIO.output(self.RIGHT_MOTOR_BACKWARD, GPIO.HIGH)
        
        time.sleep(duration)
        self.stop()
    
    def stop(self):
        """停止所有电机"""
        logger.info("停止所有电机")
        
        for pin in [self.LEFT_MOTOR_FORWARD, self.LEFT_MOTOR_BACKWARD,
                    self.RIGHT_MOTOR_FORWARD, self.RIGHT_MOTOR_BACKWARD]:
            GPIO.output(pin, GPIO.LOW)
    
    def set_servo_angle(self, pwm, angle):
        """设置舵机角度"""
        # 将角度转换为PWM占空比 (2.5%-12.5%)
        duty = 2.5 + (angle / 180) * 10
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.3)  # 等待舵机转动到位
    
    def move_arm_to_position(self, position):
        """移动机械臂到指定位置
        position: (base_angle, shoulder_angle, elbow_angle, gripper_angle)
        """
        base_angle, shoulder_angle, elbow_angle, gripper_angle = position
        
        logger.info(f"移动机械臂到位置: {position}")
        
        self.set_servo_angle(self.base_pwm, base_angle)
        self.set_servo_angle(self.shoulder_pwm, shoulder_angle)
        self.set_servo_angle(self.elbow_pwm, elbow_angle)
        self.set_servo_angle(self.gripper_pwm, gripper_angle)
    
    def collect_ball(self):
        """执行捡球动作"""
        logger.info("开始捡球流程")
        
        # 预定义位置
        READY_POSITION = (90, 45, 90, 90)    # 准备位置
        PICK_POSITION = (90, 70, 120, 0)     # 拾取位置
        HOLD_POSITION = (90, 50, 100, 0)     # 持球位置
        DROP_POSITION = (135, 60, 120, 90)   # 放置位置
        
        # 移动到准备位置
        self.move_arm_to_position(READY_POSITION)
        time.sleep(0.5)
        
        # 移动到拾取位置
        self.move_arm_to_position(PICK_POSITION)
        time.sleep(0.5)
        
        # 闭合抓取器
        self.set_servo_angle(self.gripper_pwm, 0)
        logger.info("抓取网球")
        time.sleep(1)
        
        # 提升网球
        self.move_arm_to_position(HOLD_POSITION)
        time.sleep(0.5)
        
        # 旋转到底座
        self.move_arm_to_position(DROP_POSITION)
        time.sleep(0.5)
        
        # 打开抓取器
        self.set_servo_angle(self.gripper_pwm, 90)
        logger.info("放置网球")
        time.sleep(0.5)
        
        # 返回准备位置
        self.move_arm_to_position(READY_POSITION)
        logger.info("捡球流程完成")
    
    def cleanup(self):
        """释放资源"""
        logger.info("清理资源")
        
        # 停止PWM
        self.base_pwm.stop()
        self.shoulder_pwm.stop()
        self.elbow_pwm.stop()
        self.gripper_pwm.stop()
        
        # 清理GPIO
        GPIO.cleanup()

# 测试代码
if __name__ == "__main__":
    try:
        controller = RobotController()
        
        # 测试底盘运动
        controller.move_forward(1.0)
        controller.turn_left(0.5)
        controller.turn_right(0.5)
        controller.move_backward(1.0)
        
        # 测试机械臂
        controller.collect_ball()
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    finally:
        controller.cleanup()    