import json
import os
from glob import glob  # 新增：用于查找所有JSON文件

def convert_json_to_txt(json_path, output_txt_path):
    # 读取JSON报告（原有逻辑不变）
    with open(json_path, 'r') as f:
        report = json.load(f)
    
    result_dict = {}
    for detail in report['details']:
        img_name = detail['image_name']
        re = detail['detections']
        t_ms = detail['processing_time'] * 1000  # 秒转毫秒
        result_dict[img_name] = {'re': re, 't': round(t_ms, 2)}
    
    # 计算统计指标（原有逻辑不变）
    times = [d['processing_time'] * 1000 for d in report['details']]
    avg_time = sum(times) / len(times) if times else 0
    max_time = max(times) if times else 0
    min_time = min(times) if times else 0
    result_dict['avg_time'] = f"{avg_time:.2f}"
    result_dict['max_time'] = f"{max_time:.2f}"
    result_dict['min_time'] = f"{min_time:.2f}"
    
    # 写入TXT文件（原有逻辑不变）
    with open(output_txt_path, 'w') as f:
        f.write(str(result_dict))
    print(f"转换完成：{json_path} -> {output_txt_path}")

if __name__ == '__main__':
    # 配置参数：指定要扫描的目录（当前目录）
    target_dir = "./"  # 可修改为其他目录路径（如绝对路径）
    
    # 查找目录下所有JSON文件（新增逻辑）
    json_files = glob(os.path.join(target_dir, "*.json"))  # 获取所有.json文件路径
    
    if not json_files:
        print("未找到任何JSON文件！")
        exit()
    
    # 遍历每个JSON文件并转换（新增逻辑）
    for json_file in json_files:
        # 生成输出TXT路径（与JSON同名，替换扩展名）
        txt_file = os.path.splitext(json_file)[0] + ".txt"
        convert_json_to_txt(json_file, txt_file)