import os
import time

#
# 模块说明：
#   本文件作为图像识别模块，用于被其他程序调用（非主程序运行）。
#   核心功能：处理单张图像，返回识别到的网球数量，并统计单张图像的处理时间。
#   统计逻辑与 test 项目中要求的一致：支持批量图像测试，最终输出每张图像的识别数量、处理时间及所有图像的平均时间。
#
# 参数:
#   img_path: 要识别的图片的路径（绝对或相对路径）
#
# 返回:
#   int: 识别到的网球数量（与 test 项目中“图片对应输出结果.txt”格式一致）
#
def process_img(img_path):
    # 实际实现逻辑（示例）：
    # 1. 读取图像（如使用 OpenCV）
    # 2. 调用 YOLOv5 等模型进行网球检测
    # 3. 统计检测到的网球数量（返回值）
    # 4. 记录处理时间（通过 time 模块计时）
    pass

#
# 以下代码仅作为本地测试时使用（非提交版本），用于验证模块功能：
#   - 遍历指定目录下的所有图像文件
#   - 调用 process_img 处理每张图像
#   - 统计每张图像的识别数量、处理时间及所有图像的平均时间
#   最终提交时需删除或注释此部分，确保仅作为模块被调用。
#
if __name__ == '__main__':
    imgs_folder = './test_imgs/'  # 测试图像目录（与 test 项目路径一致）
    img_paths = [f for f in os.listdir(imgs_folder) if f.endswith(('.jpg', '.png'))]
    
    total_time = 0  # 总处理时间（与 test 项目统计逻辑一致）
    results = []    # 存储每张图像的结果（识别数量、处理时间）

    for img_path in img_paths:
        full_path = os.path.join(imgs_folder, img_path)
        print(f"处理图像: {full_path}")

        # 计时并调用识别函数
        start_time = time.time()
        ball_count = process_img(full_path)  # 调用核心识别功能
        process_time = (time.time() - start_time) * 1000  # 转换为毫秒（与 test 项目单位一致）
        total_time += process_time

        # 记录单张结果（与 test 项目数据格式兼容）
        results.append({
            "image_name": img_path,
            "ball_count": ball_count,
            "process_time_ms": round(process_time, 2)
        })
        print(f"识别到网球数量: {ball_count}, 耗时: {process_time:.2f}ms")

    # 计算平均时间（与 test 项目统计逻辑一致）
    avg_time = total_time / len(img_paths) if img_paths else 0
    print(f"\n测试总结：共 {len(img_paths)} 张图像，平均耗时: {avg_time:.2f}ms")

    # 可选：将结果保存为文件（与 test 项目输出格式兼容）
    # with open('test_results.json', 'w') as f:
    #     json.dump({"avg_time_ms": avg_time, "details": results}, f, indent=2)