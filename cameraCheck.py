import cv2

def check_cameras():
    print("接続されているカメラを探しています...")
    for i in range(5): # 0番から4番までチェック
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"✅ カメラ ID {i}: 使用可能")
            cap.release()
        else:
            print(f"❌ カメラ ID {i}: なし")

if __name__ == "__main__":
    check_cameras()