import cv2
import numpy as np
import json
import os


clicked_points = []

def mouse_callback(event, x, y, flags, param):
    global clicked_points
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicked_points) < 4:
            clicked_points.append((x, y))
        else:
            clicked_points = [(x, y)]

def get_grid_centers(pts):
    pts = np.array(pts, dtype="float32")
    def lerp(p1, p2, t):
        return p1 + t * (p2 - p1)
    centers = []
    steps = [1/6, 3/6, 5/6]
    for r in steps:
        for c in steps:
            left_edge = lerp(pts[0], pts[3], r)
            right_edge = lerp(pts[1], pts[2], r)
            point = lerp(left_edge, right_edge, c)
            centers.append(point.astype(int))
    return centers

def enhance_image(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    v = clahe.apply(v)
    s = cv2.convertScaleAbs(s, alpha=1.3, beta=0)
    enhanced_hsv = cv2.merge([h, s, v])
    return enhanced_hsv, cv2.cvtColor(enhanced_hsv, cv2.COLOR_HSV2BGR)

def calibrate():
    global clicked_points
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Calibration Tool")
    cv2.setMouseCallback("Calibration Tool", mouse_callback)
    
    color_names = ['White (U)', 'Red (R)', 'Green (F)', 'Yellow (D)', 'Orange (L)', 'Blue (B)']
    color_keys = ['U', 'R', 'F', 'D', 'L', 'B']
    calibration_data = {}

    idx = 0
    print("--- 顏色校準工具 (增強版) ---")

    while idx < len(color_names):
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        hsv_frame, bgr_enhanced = enhance_image(frame)
        display_frame = bgr_enhanced.copy()
        
        for p in clicked_points:
            cv2.circle(display_frame, p, 5, (0, 0, 255), -1)
        if len(clicked_points) == 4:
            cv2.line(display_frame, clicked_points[0], clicked_points[1], (0, 255, 0), 2)
            cv2.line(display_frame, clicked_points[1], clicked_points[2], (0, 255, 0), 2)
            cv2.line(display_frame, clicked_points[2], clicked_points[3], (0, 255, 0), 2)
            cv2.line(display_frame, clicked_points[3], clicked_points[0], (0, 255, 0), 2)
            
            centers = get_grid_centers(clicked_points)
            for pt in centers:
                cv2.circle(display_frame, tuple(pt), 3, (255, 255, 0), -1)

        cv2.putText(display_frame, f"Calibration: {color_names[idx]}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.imshow("Calibration Tool", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') and len(clicked_points) == 4:
            centers = get_grid_centers(clicked_points)
            hsv_values = []
            for pt in centers:
                roi = hsv_frame[max(0, pt[1]-5):pt[1]+5, max(0, pt[0]-5):pt[0]+5]
                hsv_values.append(np.median(roi, axis=(0, 1)))
            
            avg_color = np.mean(hsv_values, axis=0)
            calibration_data[color_keys[idx]] = avg_color.tolist()
            print(f"已儲存 {color_names[idx]}")
            idx += 1
            clicked_points = []
        elif key == ord('c'):
            clicked_points = []
        elif key == ord('q'):
            break

    if len(calibration_data) == 6:
        with open('color_config.json', 'w') as f:
            json.dump(calibration_data, f, indent=4)
        print("\n校準完成！")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    calibrate()
