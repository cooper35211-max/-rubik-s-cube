import cv2
import numpy as np
import json
import os

def load_config():
    if os.path.exists('color_config.json'):
        with open('color_config.json', 'r') as f:
            return json.load(f)
    return None

def get_color_name(hsv, config):
    """
    使用歐幾里得距離在 HSV 空間中尋找最接近的校準顏色
    """
    if config is None:
        # 如果沒有校準檔，使用備用的簡單邏輯
        h, s, v = hsv
        if s < 50 and v > 150: return 'U'
        if h < 10 or h > 160: return 'R'
        if 10 <= h < 25: return 'L'
        if 25 <= h < 45: return 'D'
        if 45 <= h < 85: return 'F'
        if 85 <= h < 130: return 'B'
        return '?'
    
    # 計算距離
    min_dist = float('inf')
    closest_color = '?'
    
    for color_key, target_hsv in config.items():
        # 在 HSV 空間計算歐幾里得距離
        dist = np.linalg.norm(np.array(hsv) - np.array(target_hsv))
        if dist < min_dist:
            min_dist = dist
            closest_color = color_key
            
    return closest_color

def scan_cube():
    config = load_config()
    if config is None:
        print("警告：找不到 color_config.json，建議先執行 calibrate.py 進行校準以獲得最佳效果。")
    
    cap = cv2.VideoCapture(0)
    
    # 定義九宮格的參數
    cell_size = 40
    start_x, start_y = 240, 160
    
    faces_data = {}
    face_order = ['U', 'R', 'F', 'D', 'L', 'B']
    current_face_idx = 0

    print("開始掃描！請按 's' 擷取當前面，按 'q' 退出。")

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        current_face_colors = []
        
        for i in range(3):
            for j in range(3):
                x1 = start_x + j * (cell_size + 10)
                y1 = start_y + i * (cell_size + 10)
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
                
                roi = hsv_frame[y1:y2, x1:x2]
                avg_hsv = np.mean(roi, axis=(0, 1))
                
                color_code = get_color_name(avg_hsv, config)
                current_face_colors.append(color_code)
                
                cv2.putText(frame, color_code, (x1, y1 - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        target_face = face_order[current_face_idx] if current_face_idx < 6 else "Done"
        cv2.putText(frame, f"Scanning Face: {target_face}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        
        if config is None:
            cv2.putText(frame, "NO CALIBRATION DATA!", (20, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.putText(frame, "Press 'S' to Save Face | 'Q' to Quit", (20, 450), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Cube Scanner (Spike)", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') and current_face_idx < 6:
            faces_data[face_order[current_face_idx]] = "".join(current_face_colors)
            current_face_idx += 1
            if current_face_idx == 6:
                full_string = "".join([faces_data[f] for f in face_order])
                print("\n掃描完成！")
                print(f"字串：{full_string}")
                break
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_cube()
