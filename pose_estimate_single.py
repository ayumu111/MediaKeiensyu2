
# -*- coding: utf-8 -*-
"""
1枚の画像に対して、
- YOLO11 Pose で骨格推定
- 黒背景に骨格を描画した画像を保存
- キーポイント座標 (x, y) と信頼度 conf を CSV と JSON で保存

必要: pip install ultralytics opencv-python numpy pandas matplotlib
"""

from ultralytics import YOLO
import cv2
import numpy as np
import pandas as pd
import json
import os

# === 1) 設定 ===
image_path = "pose_example.jpg"    # ← 対象の画像パスを指定
save_dir   = "outputs_single"            # 出力フォルダ
os.makedirs(save_dir, exist_ok=True)

# YOLO11 Pose モデルをロード（軽量版）
model = YOLO("yolo11n-pose.pt")

# === 2) 推論 ===
results = model(image_path)
res = results[0]

# キーポイントが無い場合は終了
if res.keypoints is None or res.keypoints.shape[0] == 0:
    print("キーポイントが検出されませんでした。")
    raise SystemExit

# === 3) 黒背景に骨格描画した画像を保存 ===
orig = cv2.imread(image_path)
h, w = orig.shape[:2]
black_bg = np.zeros((h, w, 3), dtype=np.uint8)

# Ultralytics の描画ユーティリティで骨格＋キーポイントを描画
drawn = res.plot(img=black_bg.copy(), kpt_radius=5, line_width=2)

# 保存ファイル名
base = os.path.splitext(os.path.basename(image_path))[0]
annotated_path = os.path.join(save_dir, f"{base}_pose.png")
cv2.imwrite(annotated_path, drawn)
print(f"骨格描画画像を保存: {annotated_path}")

# === 4) キーポイント座標と信頼度を抽出して保存（CSV/JSON） ===
# res.keypoints.xy: shape = (num_persons, num_kpts, 2)
# res.keypoints.conf: shape = (num_persons, num_kpts)
kpts_xy = res.keypoints.xy  # torch.Tensor または numpy 風
kpts_conf = res.keypoints.conf

# COCO の17キーポイント名（YOLO Pose が一般的に採用）
# モデルのキーポイント数が異なる場合は、下の names を自動で短縮/拡張します
coco_kpt_names_17 = [
    "nose","left_eye","right_eye","left_ear","right_ear",
    "left_shoulder","right_shoulder","left_elbow","right_elbow",
    "left_wrist","right_wrist","left_hip","right_hip",
    "left_knee","right_knee","left_ankle","right_ankle"
]

num_persons, num_kpts = kpts_xy.shape[0], kpts_xy.shape[1]
# キーポイント名をモデル出力に合わせて調整
if len(coco_kpt_names_17) >= num_kpts:
    kpt_names = coco_kpt_names_17[:num_kpts]
else:
    # もしモデルの方が多い場合は不足分をインデックス名に
    kpt_names = coco_kpt_names_17 + [f"kpt_{i}" for i in range(len(coco_kpt_names_17), num_kpts)]

rows = []
for pid in range(num_persons):
    for kid in range(num_kpts):
        x = float(kpts_xy[pid, kid, 0])
        y = float(kpts_xy[pid, kid, 1])
        conf = float(kpts_conf[pid, kid]) if kpts_conf is not None else None
        rows.append({
            "image": os.path.basename(image_path),
            "person_id": pid,
            "keypoint_id": kid,
            "keypoint_name": kpt_names[kid],
            "x": x,
            "y": y,
            "confidence": conf
        })

# CSV 保存
df = pd.DataFrame(rows, columns=["image","person_id","keypoint_id","keypoint_name","x","y","confidence"])
csv_path = os.path.join(save_dir, f"{base}_keypoints.csv")
df.to_csv(csv_path, index=False, encoding="utf-8")
print(f"キーポイントCSVを保存: {csv_path}")

# JSON 保存（人ごとにまとめた構造）
grouped = {}
for r in rows:
    pid = r["person_id"]
    grouped.setdefault(pid, []).append({
        "keypoint_id": r["keypoint_id"],
        "keypoint_name": r["keypoint_name"],
        "x": r["x"],
        "y": r["y"],
        "confidence": r["confidence"]
    })
json_obj = {
    "image": os.path.basename(image_path),
    "width": w, "height": h,
    "num_persons": num_persons,
    "keypoints": grouped
}
json_path = os.path.join(save_dir, f"{base}_keypoints.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_obj, f, ensure_ascii=False, indent=2)
print(f"キーポイントJSONを保存: {json_path}")
