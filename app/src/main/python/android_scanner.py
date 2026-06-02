import cv2
import numpy as np
from scanner import get_grid_centers, get_display_char, load_config, DISPLAY_TO_CODE

def detect_cube_corners(frame):
    """
    自動偵測畫面中魔術方塊的四個頂點
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 使用自適應二值化
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                 cv2.THRESH_BINARY_INV, 11, 2)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best_cnt = None
    max_area = 0
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 5000: continue # 過濾太小的
        
        # 逼近多邊形
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        
        # 魔方通常是四邊形
        if len(approx) == 4:
            if area > max_area:
                max_area = area
                best_cnt = approx
                
    if best_cnt is not None:
        # 整理點的順序：TL, TR, BR, BL
        pts = best_cnt.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")
        
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] # TL
        rect[2] = pts[np.argmax(s)] # BR
        
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # TR
        rect[3] = pts[np.argmax(diff)] # BL
        
        return rect.tolist()
    
    return None

def process_frame(frame_bytes, width, height, config_json=None):
    """
    供 Android 呼叫的主要接口
    """
    # 將 bytes 轉換回 OpenCV 影像格式
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"status": "error", "message": "Decode failed"}

    # 1. 偵測頂點
    corners = detect_cube_corners(frame)
    if not corners:
        return {"status": "no_cube"}

    # 2. 如果有頂點，嘗試擷取顏色
    config = load_config() # 這裡可以改成從 Android 傳入或是讀取檔案
    centers = get_grid_centers(corners)
    
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    face_colors = []
    
    for pt in centers:
        roi_r = 7
        roi = hsv_frame[max(0, pt[1]-roi_r):pt[1]+roi_r+1, max(0, pt[0]-roi_r):pt[0]+roi_r+1]
        if roi.size > 0:
            avg_hsv = np.median(roi, axis=(0, 1))
            display_char = get_display_char(avg_hsv, config)
            face_colors.append(DISPLAY_TO_CODE.get(display_char, '?'))
        else:
            face_colors.append('?')

    return {
        "status": "success",
        "corners": corners,
        "colors": "".join(face_colors)
    }
