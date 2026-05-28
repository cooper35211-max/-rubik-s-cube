import cv2
import numpy as np
import json
import os

# 全域變數
clicked_points = []
# 顏色對應表：顯示字母 -> 演算法代號
DISPLAY_TO_CODE = {
    'w': 'U', # White -> Up
    'r': 'R', # Red -> Right
    'g': 'F', # Green -> Front
    'y': 'D', # Yellow -> Down
    'o': 'L', # Orange -> Left
    'b': 'B'  # Blue -> Back
}
# 反向對應：演算法代號 -> 顯示字母 (用於校準讀取)
CODE_TO_DISPLAY = {v: k for k, v in DISPLAY_TO_CODE.items()}

def mouse_callback(event, x, y, flags, param):
    global clicked_points
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicked_points) < 4:
            clicked_points.append((x, y))
        else:
            clicked_points = [(x, y)]

def load_config():
    if os.path.exists('color_config.json'):
        with open('color_config.json', 'r') as f:
            return json.load(f)
    return None

def get_display_char(hsv, config):
    """
    獲取直觀的顏色首字母 (w, r, g, y, o, b)
    """
    if config is None:
        return '?'
    
    min_dist = float('inf')
    closest_code = '?'
    
    h, s, v = hsv
    for code, target_hsv in config.items():
        th, ts, tv = target_hsv
        dh = min(abs(h - th), 180 - abs(h - th))
        ds = (s - ts)
        dv = (v - tv)
        dist = np.sqrt((dh * 2.0)**2 + (ds * 1.0)**2 + (dv * 1.0)**2)
        
        if dist < min_dist:
            min_dist = dist
            closest_code = code
            
    return CODE_TO_DISPLAY.get(closest_code, '?')

def get_grid_centers(pts):
    """
    根據四個角 (TL, TR, BR, BL) 插值計算出 3x3 網格的中心點
    修正鏡像問題：
    因為畫面是 flip(1) 鏡像過的，畫面上的左(TL)其實是現實的右(TR)。
    為了讓字串順序正確(左到右)，我們在插值時要把水平方向反過來。
    """
    pts = np.array(pts, dtype="float32")
    def lerp(p1, p2, t):
        return p1 + t * (p2 - p1)

    centers = []
    # 網格位置 t = 1/6, 3/6, 5/6
    rows = [1/6, 3/6, 5/6]
    cols = [5/6, 3/6, 1/6] # 反轉水平插值順序：5/6(右) -> 3/6(中) -> 1/6(左)
    
    for r in rows:
        for c in cols:
            # 在鏡像畫面上，從右向左掃描，對應到現實世界就是從左向右掃描
            left_edge = lerp(pts[0], pts[3], r)  # TL to BL
            right_edge = lerp(pts[1], pts[2], r) # TR to BR
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

def scan_cube():
    global clicked_points
    config = load_config()
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Cube Scanner")
    cv2.setMouseCallback("Cube Scanner", mouse_callback)
    
    faces_data = {}
    face_order = ['U', 'R', 'F', 'D', 'L', 'B']
    current_face_idx = 0

    print("--- 影像辨識模式 (顏色縮寫版) ---")
    print("w:白, y:黃, r:紅, o:橘, g:綠, b:藍")

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        hsv_frame, bgr_enhanced = enhance_image(frame)
        display_frame = bgr_enhanced.copy()
        
        current_face_codes = []
        
        # 繪製已點選的點與連線 (提供即時視覺回饋)
        for p in clicked_points:
            cv2.circle(display_frame, p, 5, (0, 0, 255), -1) # 紅色小圓點
            
        if len(clicked_points) > 1:
            for i in range(len(clicked_points) - 1):
                cv2.line(display_frame, clicked_points[i], clicked_points[i+1], (0, 255, 0), 2)
        
        if len(clicked_points) == 4:
            cv2.line(display_frame, clicked_points[3], clicked_points[0], (0, 255, 0), 2)
            
            centers = get_grid_centers(clicked_points)
            for pt in centers:
                roi_r = 7
                roi = hsv_frame[max(0, pt[1]-roi_r):pt[1]+roi_r+1, max(0, pt[0]-roi_r):pt[0]+roi_r+1]
                
                if roi.size > 0:
                    avg_hsv = np.median(roi, axis=(0, 1))
                    display_char = get_display_char(avg_hsv, config)
                    # 轉換回演算法代號儲存
                    current_face_codes.append(DISPLAY_TO_CODE.get(display_char, '?'))
                else:
                    display_char = '?'
                    current_face_codes.append('?')
                
                cv2.circle(display_frame, tuple(pt), 3, (255, 0, 0), -1)
                cv2.putText(display_frame, display_char, (pt[0]+5, pt[1]-5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        status_text = f"Face: {face_order[current_face_idx] if current_face_idx < 6 else 'Done'}"
        cv2.putText(display_frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        
        cv2.imshow("Cube Scanner", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') and current_face_idx < 6 and len(clicked_points) == 4:
            if '?' not in current_face_codes:
                faces_data[face_order[current_face_idx]] = "".join(current_face_codes)
                print(f"已儲存 {face_order[current_face_idx]} 面")
                current_face_idx += 1
                if current_face_idx == 6:
                    full_string = "".join([faces_data[f] for f in face_order])
                    print(f"\n掃描完成！全字串：{full_string}")
                    # 自動將結果寫入一個臨時文件，方便貼上
                    with open('cube_string.txt', 'w') as f:
                        f.write(full_string)
                    break
            else:
                print("偵測到未知顏色，請重新對準")
        elif key == ord('c'):
            clicked_points = []
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    scan_cube()
