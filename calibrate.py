import cv2
import numpy as np
import json
import os

def calibrate():
    cap = cv2.VideoCapture(0)
    
    # 定義要校準的顏色順序
    color_names = ['White (U)', 'Red (R)', 'Green (F)', 'Yellow (D)', 'Orange (L)', 'Blue (B)']
    color_keys = ['U', 'R', 'F', 'D', 'L', 'B']
    calibration_data = {}

    print("--- 魔術方塊顏色校準工具 ---")
    print("請將方塊的指定顏色對準畫面中央的九宮格，然後按 's' 儲存。")

    cell_size = 40
    start_x, start_y = 240, 160

    idx = 0
    while idx < len(color_names):
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 繪製九宮格輔助線
        temp_hsv_list = []
        for i in range(3):
            for j in range(3):
                x1 = start_x + j * (cell_size + 10)
                y1 = start_y + i * (cell_size + 10)
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 1)
                
                # 取得中心區域的平均 HSV
                roi = hsv_frame[y1:y2, x1:x2]
                avg_hsv = np.mean(roi, axis=(0, 1))
                temp_hsv_list.append(avg_hsv.tolist())

        # 顯示文字說明
        cv2.putText(frame, f"Calibration Step {idx+1}/{len(color_names)}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        cv2.putText(frame, f"Show: {color_names[idx]}", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, "Press 'S' to Capture | 'Q' to Cancel", (20, 450), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Calibration Tool", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            # 儲存該顏色的平均 HSV
            avg_color = np.mean(temp_hsv_list, axis=0)
            calibration_data[color_keys[idx]] = avg_color.tolist()
            print(f"已校準 {color_names[idx]}: HSV = {avg_color}")
            idx += 1
        elif key == ord('q'):
            print("取消校準")
            cap.release()
            cv2.destroyAllWindows()
            return

    # 儲存到 JSON 檔案
    with open('color_config.json', 'w') as f:
        json.dump(calibration_data, f, indent=4)
    
    print("\n校準完成！數據已儲存至 color_config.json")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    calibrate()
