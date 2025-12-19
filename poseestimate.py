from ultralytics import YOLO
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

# モデルのロード
model = YOLO("yolo11n-pose.pt")

# 入力画像フォルダ
image_dir = "images"
save_dir = "pose_black_bg"
os.makedirs(save_dir, exist_ok=True)

for img_file in os.listdir(image_dir):
    if not img_file.lower().endswith((".jpg", ".png")):
        continue

    img_path = os.path.join(image_dir, img_file)
    results = model(img_path)

    if results[0].keypoints is None or len(results[0].keypoints) == 0:
        print(f"スキップ: {img_file}（キーポイントなし）")
        continue

    # 元画像サイズを取得して黒背景を作成
    orig = cv2.imread(img_path)
    h, w, _ = orig.shape
    black_bg = np.zeros((h, w, 3), dtype=np.uint8)

    # YOLOの描画機能を使って骨格＋キーポイントを描画
    # plot() 内部では colors と skeleton 情報を自動参照して描画
    # black_bg に人物を合成せず、推定結果のみを上に描く
    drawn = results[0].plot(img=black_bg.copy(), kpt_radius=5, line_width=2)

    # 保存
    save_path = os.path.join(save_dir, img_file)
    cv2.imwrite(save_path, drawn)
    print(f"保存: {save_path}")

    # 表示（必要なら）
    plt.imshow(cv2.cvtColor(drawn, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.show()
