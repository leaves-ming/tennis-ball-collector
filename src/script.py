import json
import os
from PIL import Image

def convert_to_yolov5(json_path, images_dir, output_dir):
    """
    将JSON格式的标注转换为YOLOv5格式
    
    参数:
    json_path: JSON文件路径
    images_dir: 图像文件所在目录
    output_dir: 输出标注文件的目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取JSON文件
    with open(json_path, 'r') as f:
        annotations = json.load(f)
    
    # 处理每个图像的标注
    for image_name, bboxes in annotations.items():
        # 获取图像尺寸
        try:
            img_path = os.path.join(images_dir, image_name)
            img = Image.open(img_path)
            width, height = img.size
        except Exception as e:
            print(f"无法处理图像 {image_name}: {e}")
            continue
        
        # 创建对应的txt文件
        txt_name = os.path.splitext(image_name)[0] + '.txt'
        txt_path = os.path.join(output_dir, txt_name)
        
        with open(txt_path, 'w') as f:
            # 处理每个边界框
            for bbox in bboxes:
                x = bbox['x']
                y = bbox['y']
                w = bbox['w']
                h = bbox['h']
                
                # 计算中心点坐标
                x_center = x + w / 2
                y_center = y + h / 2
                
                # 归一化处理
                x_center_norm = x_center / width
                y_center_norm = y_center / height
                w_norm = w / width
                h_norm = h / height
                
                # 写入YOLOv5格式 (class x_center y_center width height)
                # 假设类别ID为0 (网球)
                f.write(f"0 {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}\n")
        
        print(f"已转换: {image_name} -> {txt_name}")

# 使用示例
if __name__ == "__main__":
    json_path = "annotations.json"  # 替换为你的JSON文件路径
    images_dir = "image"  # 替换为你的图像文件夹路径
    output_dir = "labels"  # 替换为输出标注文件夹路径
    
    convert_to_yolov5(json_path, images_dir, output_dir)