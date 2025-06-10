# tennis-ball-collector
## 项目特色
1.高精度检测：基于 YOLOv5 实现网球识别，结合 NMS 与尺寸过滤，检测成功率超 85%。
2.低成本硬件：采用 Orange Pi AI Pro 开发板，搭配通用 RGB 相机与 3 自由度机械臂，成本更低。
3.模块化设计：视觉、控制、通信模块解耦，支持 YOLO 模型快速替换与多机械臂协同功能扩展。

## 使用说明
1. 环境配置：
   - Python 3.8+
   - PyTorch 1.10+
   - OpenCV 4.5+
2. 安装依赖：
   ```bash
   cd test
   git clone https://github.com/ultralytics/yolov5  # 克隆YOLOv5仓库
   pip install -r requirements.txt  # 安装依赖
   ```
3. 配置文件：
   - config.yaml：模型配置、相机参数、机械臂控制参数等。
   - 在src/test/yolov5/runs/train中放入训练好的，模型（可直接将test文件夹中的exp文件夹复制到runs/train中）
   - 在test_images文件夹中放入测试图片，在ground_truth文件夹中放入对应的标注文件
4. 运行项目：
   ```bash
   python main.py
   ```
