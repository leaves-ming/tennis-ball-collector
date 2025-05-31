# tennis_ball_detector.py
import cv2
import numpy as np
import os
import json
import time
from datetime import datetime

class TennisBallDetector:
    def __init__(self, config):
        self.config = config
        self.lower_yellow = np.array(config["image_processing"]["lower_yellow"])
        self.upper_yellow = np.array(config["image_processing"]["upper_yellow"])
        self.min_ball_radius = config["image_processing"]["min_ball_radius"]
        self.max_ball_radius = config["image_processing"]["max_ball_radius"]
        self.focal_length = config["image_processing"]["focal_length"]
        self.known_ball_diameter = config["image_processing"]["known_ball_diameter"]
        
        # 测试模式相关
        self.test_mode = config["test"]["test_mode"]
        self.test_images_dir = config["test"]["test_images_dir"]
        self.ground_truth_dir = config["test"]["ground_truth_dir"]
        self.test_results = []
        
    def detect_tennis_balls(self, frame):
        """检测图像中的网球"""
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 创建黄色掩码
        mask = cv2.inRange(hsv, self.lower_yellow, self.upper_yellow)
        
        # 形态学操作
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 寻找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        balls = []
        processed_frame = frame.copy()
        
        for contour in contours:
            # 计算轮廓面积
            area = cv2.contourArea(contour)
            
            # 过滤小面积区域
            if area < 100:
                continue
                
            # 拟合圆形
            ((x, y), radius) = cv2.minEnclosingCircle(contour)
            
            # 过滤不符合半径范围的圆形
            if radius < self.min_ball_radius or radius > self.max_ball_radius:
                continue
                
            # 计算圆形度（圆形度 = 4π×面积/周长²，圆形为1）
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            
            # 过滤非圆形物体
            if circularity < 0.7:
                continue
                
            # 计算距离
            distance = (self.known_ball_diameter * self.focal_length) / (2 * radius)
            
            # 计算水平偏移（百分比）
            frame_center_x = frame.shape[1] / 2
            horizontal_offset = ((x - frame_center_x) / frame_center_x) * 100
            
            # 记录检测结果
            balls.append(((x, y), radius, distance, horizontal_offset))
            
            # 在图像上绘制检测结果
            cv2.circle(processed_frame, (int(x), int(y)), int(radius), (0, 255, 0), 2)
            cv2.putText(processed_frame, f"{distance:.1f}cm", (int(x) - 20, int(y) - 20),
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
        """评估检测结果"""
        # 计算真正例、假正例、假反例
        true_positives = 0
        false_positives = len(detected_balls)
        false_negatives = len(ground_truth)
        
        for (x, y), radius, _, _ in detected_balls:
            for gt_ball in ground_truth:
                gt_x, gt_y, gt_radius = gt_ball['x'], gt_ball['y'], gt_ball['radius']
                
                # 计算距离和半径差异
                distance = np.sqrt((x - gt_x)**2 + (y - gt_y)**2)
                radius_diff = abs(radius - gt_radius)
                
                # 如果检测结果与真实标注足够接近，则认为是真正例
                if distance < 20 and radius_diff < 10:
                    true_positives += 1
                    false_positives -= 1
                    false_negatives -= 1
                    break
        
        false_negatives = max(false_negatives, 0)
        false_positives = max(false_positives, 0)
        
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