import matplotlib.pyplot as plt
import numpy as np

class ArmVisualizer:
    def __init__(self):
        # 尝试使用系统中可能存在的中文字体
        plt.rcParams["font.family"] = ["SimHei"]  # 可根据系统情况修改字体名称

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.ax.set_xlim(-50, 50)
        self.ax.set_ylim(0, 60)
        self.ax.set_aspect('equal')
        self.ax.set_title("机械臂动作模拟")

        # 机械臂参数（单位：cm）
        self.base_height = 5
        self.shoulder_length = 20
        self.elbow_length = 20
        self.gripper_length = 10

        # 初始化关节角度
        self.shoulder_angle = 90  # 肩部角度（垂直）
        self.elbow_angle = 0      # 肘部角度
        self.gripper_open = True  # 夹爪状态

        # 绘制元素
        self.base = plt.Circle((0, 0), 3, color='blue')
        self.shoulder = plt.Circle((0, self.base_height), 2, color='red')
        self.elbow = plt.Circle((0, 0), 2, color='red')
        self.gripper = plt.Circle((0, 0), 2, color='green')

        # 机械臂连杆
        self.arm1, = self.ax.plot([], [], 'b-', lw=5)
        self.arm2, = self.ax.plot([], [], 'b-', lw=5)
        self.gripper_arms, = self.ax.plot([], [], 'g-', lw=3)

        self.ax.add_patch(self.base)
        self.ax.add_patch(self.shoulder)
        self.ax.add_patch(self.elbow)
        self.ax.add_patch(self.gripper)

        # 网球位置（初始为None）
        self.tennis_ball = None
        self.ball_pos = None

        # 设置非阻塞显示
        plt.ion()
        self.fig.show()

    def update_arm(self, shoulder_angle, elbow_angle, gripper_open, ball_pos=None):
        """更新机械臂姿态"""
        self.shoulder_angle = shoulder_angle
        self.elbow_angle = elbow_angle
        self.gripper_open = gripper_open
        self.ball_pos = ball_pos

        # 计算关节位置
        shoulder_x = 0
        shoulder_y = self.base_height

        elbow_x = shoulder_x + self.shoulder_length * np.cos(np.radians(shoulder_angle - 90))
        elbow_y = shoulder_y + self.shoulder_length * np.sin(np.radians(shoulder_angle - 90))

        gripper_x = elbow_x + self.elbow_length * np.cos(np.radians(shoulder_angle + elbow_angle - 90))
        gripper_y = elbow_y + self.elbow_length * np.sin(np.radians(shoulder_angle + elbow_angle - 90))

        # 更新关节位置
        self.shoulder.center = (shoulder_x, shoulder_y)
        self.elbow.center = (elbow_x, elbow_y)
        self.gripper.center = (gripper_x, gripper_y)

        # 更新连杆
        self.arm1.set_data([shoulder_x, elbow_x], [shoulder_y, elbow_y])
        self.arm2.set_data([elbow_x, gripper_x], [elbow_y, gripper_y])

        # 更新夹爪
        if self.gripper_open:
            # 张开状态
            gripper_arm1_x = [gripper_x - 5, gripper_x]
            gripper_arm1_y = [gripper_y - 3, gripper_y]
            gripper_arm2_x = [gripper_x + 5, gripper_x]
            gripper_arm2_y = [gripper_y - 3, gripper_y]
        else:
            # 闭合状态
            gripper_arm1_x = [gripper_x - 2, gripper_x]
            gripper_arm1_y = [gripper_y - 1, gripper_y]
            gripper_arm2_x = [gripper_x + 2, gripper_x]
            gripper_arm2_y = [gripper_y - 1, gripper_y]

        self.gripper_arms.set_data(gripper_arm1_x + [None] + gripper_arm2_x,
                                   gripper_arm1_y + [None] + gripper_arm2_y)

        # 更新网球位置
        if self.tennis_ball and self.ball_pos:
            self.tennis_ball.center = self.ball_pos
        elif self.ball_pos:
            self.tennis_ball = plt.Circle(self.ball_pos, 3, color='yellow')
            self.ax.add_patch(self.tennis_ball)

        # 更新标题
        if self.ball_pos:
            ball_dist = np.sqrt(self.ball_pos[0]**2 + (self.ball_pos[1] - self.base_height)**2)
            self.ax.set_title(f"机械臂动作模拟 - 网球距离: {ball_dist:.1f}cm")
        else:
            self.ax.set_title("机械臂动作模拟")

        # 更新图形
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

        return [self.base, self.shoulder, self.elbow, self.gripper,
                self.arm1, self.arm2, self.gripper_arms] + ([self.tennis_ball] if self.tennis_ball else [])

    def show(self):
        """保持窗口打开"""
        plt.ioff()  # 关闭交互模式
        plt.show()