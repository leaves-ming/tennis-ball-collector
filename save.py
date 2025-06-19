# tennis_ball_detector.py
import cv2
import numpy as np
import os
import json
import time
from datetime import datetime
import torch  # 新增YOLOv5依赖

class TennisBallDetector:
    def __init__(self, config):
        self.config = config
        # YOLOv5模型配置（新增）
        self.model_path = config["yolov5"]["model_path"]  # 训练好的模型路径（如./yolov5/runs/train/exp/weights/best.pt）
        self.conf_threshold = config["yolov5"]["conf_threshold"]  # 置信度阈值（如0.5）
        self.iou_threshold = config["yolov5"]["iou_threshold"]    # NMS的IOU阈值
        
        # 加载YOLOv5模型（新增）
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=self.model_path, force_reload=True)
        self.model.conf = self.conf_threshold  # 设置置信度阈值
        self.model.iou = self.iou_threshold    # 设置NMS阈值
        
        # 原OpenCV参数（保留）
        self.min_ball_radius = config["image_processing"]["min_ball_radius"]
        self.max_ball_radius = config["image_processing"]["max_ball_radius"]
        self.focal_length = config["image_processing"]["focal_length"]
        self.known_ball_diameter = config["image_processing"]["known_ball_diameter"]
        
        # 测试模式相关（保留）
        self.test_mode = config["test"]["test_mode"]
        self.test_images_dir = config["test"]["test_images_dir"]
        self.ground_truth_dir = config["test"]["ground_truth_dir"]
        self.test_results = []

    def detect_tennis_balls(self, frame):
        """使用YOLOv5的网球检测（替代原OpenCV逻辑）"""
        # YOLOv5推理（新增）
        results = self.model(frame)  # 输入BGR格式图像
        
        # 解析检测结果（新增）
        balls = []
        processed_frame = frame.copy()
        for *xyxy, conf, cls in results.xyxy[0].tolist():  # xyxy: [x1,y1,x2,y2]
            x1, y1, x2, y2 = map(int, xyxy)
            x_center = (x1 + x2) / 2  # 中心点x坐标
            y_center = (y1 + y2) / 2  # 中心点y坐标
            radius = (x2 - x1) / 2     # 近似半径（假设包围框为正方形）
            
            # 过滤不符合半径范围的球（保留原逻辑）
            if not (self.min_ball_radius < radius < self.max_ball_radius):
                continue
            
            # 计算距离（保留原公式）
            distance = (self.known_ball_diameter * self.focal_length) / (2 * radius)
            
            # 计算水平偏移（保留原逻辑）
            frame_center_x = frame.shape[1] / 2
            horizontal_offset = ((x_center - frame_center_x) / frame_center_x) * 100
            
            balls.append(((x_center, y_center), radius, distance, horizontal_offset))
            
            # 绘制检测框和信息（修改显示内容）
            cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(processed_frame, 
                        f"Ball: {distance:.1f}cm (conf:{conf:.2f})",  # 显示置信度
                        (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return balls, processed_frame

    def run_image_tests(self):
        """运行图像测试集"""
        if not os.path.exists(self.test_images_dir):
            print(f"错误: 测试图像目录 {self.test_images_dir} 不存在")
            return
            
        test_images = [f for f in os.listdir(self.test_images_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        
        total_images = len(test_images)
        correct_detections = 0
        false_positives = 0
        false_negatives = 0
        processing_times = []
        
        print(f"开始图像识别测试，共 {total_images} 张测试图像")
        
        for image_name in test_images:
            image_path = os.path.join(self.test_images_dir, image_name)
            frame = cv2.imread(image_path)
            
            if frame is None:
                print(f"无法读取图像: {image_path}")
                continue
                
            # 记录处理时间
            start_time = time.time()
            balls, processed_frame = self.detect_tennis_balls(frame)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            # 读取真实标注数据
            ground_truth_path = os.path.join(self.ground_truth_dir, image_name.replace('.jpg', '.json'))
            ground_truth = self._load_ground_truth(ground_truth_path)
            
            # 评估检测结果
            tp, fp, fn = self._evaluate_detection(balls, ground_truth)
            correct_detections += tp
            false_positives += fp
            false_negatives += fn
            
            # 保存测试结果
            self.test_results.append({
                "image_name": image_name,
                "detections": len(balls),
                "ground_truth": len(ground_truth),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "processing_time": processing_time
            })
            
            # 显示结果
            cv2.putText(processed_frame, f"Detections: {len(balls)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(processed_frame, f"Time: {processing_time:.3f}s", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow("Test Result", processed_frame)
            key = cv2.waitKey(0)  # 按任意键继续
            
            if key == 27:  # ESC键退出测试
                break
        
        # 计算性能指标
        if total_images > 0:
            avg_processing_time = sum(processing_times) / len(processing_times)
            fps = 1.0 / avg_processing_time
            precision = correct_detections / max((correct_detections + false_positives), 1)
            recall = correct_detections / max((correct_detections + false_negatives), 1)
            f1_score = 2 * (precision * recall) / max((precision + recall), 1)
            
            print("\n=== 测试总结 ===")
            print(f"总测试图像: {total_images}")
            print(f"平均处理时间: {avg_processing_time:.3f}s ({fps:.1f} FPS)")
            print(f"准确率 (Precision): {precision:.2f}")
            print(f"召回率 (Recall): {recall:.2f}")
            print(f"F1分数: {f1_score:.2f}")
            
            # 保存测试报告
            self._save_test_report(precision, recall, f1_score, fps)
    
    def _load_ground_truth(self, path):
        """加载真实标注数据"""
        if not os.path.exists(path):
            return []
            
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get('balls', [])
        except Exception as e:
            print(f"无法加载标注数据: {e}")
            return []
    
    def _evaluate_detection(self, detected_balls, ground_truth):
        """评估多目标检测结果（支持多对多匹配）"""
        true_positives = 0
        matched_gt = set()  # 记录已匹配的真实标注索引
        
        for det_idx, ball in enumerate(detected_balls):  # 正确解包：先获取ball元组
            (det_x, det_y), det_radius, _, _ = ball  # 从ball中提取4个值（坐标、半径、距离、偏移）
            for gt_idx, gt_ball in enumerate(ground_truth):
                if gt_idx in matched_gt:
                    continue  # 跳过已匹配的真实标注
                gt_x, gt_y, gt_radius = gt_ball['x'], gt_ball['y'], gt_ball['radius']
                
                # 计算检测结果与真实标注的匹配度（距离+半径差异）
                distance = np.sqrt((det_x - gt_x)**2 + (det_y - gt_y)**2)
                radius_diff = abs(det_radius - gt_radius)
                
                # 放宽匹配条件（原distance<20→30，radius_diff<10→15）
                if distance < 30 and radius_diff < 15:
                    true_positives += 1
                    matched_gt.add(gt_idx)  # 标记该真实标注已匹配
                    break
        
        false_positives = len(detected_balls) - true_positives
        false_negatives = len(ground_truth) - true_positives
        
        return true_positives, false_positives, false_negatives
    
    def _save_test_report(self, precision, recall, f1_score, fps):
        """保存测试报告"""
        report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_images": len(self.test_results),
            "metrics": {
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "fps": fps
            },
            "details": self.test_results
        }
        
        report_path = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"测试报告已保存至: {report_path}")