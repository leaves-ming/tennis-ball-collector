{
    "hardware": {
        "board_type": "Orange Pi AIpro(20T)",
        "gpio_mode": "BOARD",
        "camera_type": "csi",  # 或 "usb"，根据实际连接选择
        "motor_pins": {
            "left_forward": 12,
            "left_backward": 16,
            "right_forward": 18,
            "right_backward": 22
        },
        "servo_pins": {
            "arm_base": 32,
            "arm_shoulder": 33,
            "arm_elbow": 35,
            "gripper": 36
        },
        "pwm_frequency": 50  # PWM频率(Hz)
    },
    "image_processing": {
        "lower_yellow": [20, 100, 100],
        "upper_yellow": [40, 255, 255],
        "min_ball_radius": 10,
        "max_ball_radius": 100,
        "focal_length": 800,
        "known_ball_diameter": 6.7,
        "use_npu": false  # 是否使用NPU加速(需安装相关驱动)
    },
    "robot_control": {
        "move_speed": 70,       # 移动速度百分比
        "turn_speed": 50,       # 转向速度百分比
        "collect_distance": 30, # 收集距离(cm)
        "search_turn_time": 0.3 # 搜索时每次旋转时间(s)
    },
    "debug": {
        "show_video": true,
        "log_level": "INFO"
    }
}    