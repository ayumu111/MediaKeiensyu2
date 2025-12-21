
# -*- coding: utf-8 -*-
"""
フォルダ内の画像を一括処理して、
- 黒背景に骨格を描画した画像
- キーポイント座標をCSV（まとめ）/JSON（各画像）保存
"""

from ultralytics import YOLO
import cv2
import numpy as np
import pandas as pd
import json
import os

image_dir = "pose_examples"        # 入力画像フォルダ
save_dir  = "outputs_multi"  # 出力フォルダ
os.makedirs(save_dir, exist_ok=True)

model = YOLO("yolo11n-pose.pt")

all_rows = []  # 全画像分のキー座標をここにまとめる

# COCO 17キー名
coco_kpt_names_17 = [
    "nose","left_eye","right_eye","left_ear","right_ear",
    "left_shoulder","right_shoulder","left_elbow","right_elbow",
    "left_wrist","right_wrist","left_hip","right_hip",
    "left_knee","right_knee","left_ankle","right_ankle"
]

for img_file in os.listdir(image_dir):
    if not img_file.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    img_path = os.path.join(image_dir, img_file)
    results = model(img_path)
    res = results[0]

    # キーポイントが無い場合はスキップ
    if res.keypoints is None or res.keypoints.shape[0] == 0:
        print(f"スキップ: {img_file}（キーポイントなし）")
        continue

    # 黒背景に描画して保存
    orig = cv2.imread(img_path)
    h, w = orig.shape[:2]
    black_bg = np.zeros((h, w, 3), dtype=np.uint8)
    drawn = res.plot(img=black_bg.copy(), kpt_radius=5, line_width=2)

    base = os.path.splitext(img_file)[0]
    save_img = os.path.join(save_dir, f"{base}_pose.png")
    cv2.imwrite(save_img, drawn)
    print(f"保存: {save_img}")

    # キーポイント抽出
    kpts_xy = res.keypoints.xy
    kpts_conf = res.keypoints.conf
    num_persons, num_kpts = kpts_xy.shape[0], kpts_xy.shape[1]

    # キー名をモデルに合わせて調整
    if len(coco_kpt_names_17) >= num_kpts:
        kpt_names = coco_kpt_names_17[:num_kpts]
    else:
        kpt_names = coco_kpt_names_17 + [f"kpt_{i}" for i in range(len(coco_kpt_names_17), num_kpts)]

    # 1画像ぶんのJSON構造も保存
    grouped = {}
    for pid in range(num_persons):
        grouped.setdefault(pid, [])
        for kid in range(num_kpts):
            x = float(kpts_xy[pid, kid, 0])
            y = float(kpts_xy[pid, kid, 1])
            conf = float(kpts_conf[pid, kid]) if kpts_conf is not None else None

            grouped[pid].append({
                "keypoint_id": kid,
                "keypoint_name": kpt_names[kid],
                "x": x,
                "y": y,
                "confidence": conf
            })

            # CSV用（まとめ）
            all_rows.append({
                "image": img_file,
                "person_id": pid,
                "keypoint_id": kid,
                "keypoint_name": kpt_names[kid],
                "x": x,
                "y": y,
                "confidence": conf,
                "width": w,
                "height": h
            })

    json_path = os.path.join(save_dir, f"{base}_keypoints.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "image": img_file,
            "width": w, "height": h,
            "num_persons": num_persons,
            "keypoints": grouped
        }, f, ensure_ascii=False, indent=2)
    print(f"保存: {json_path}")

# すべての画像のキーポイントを1つのCSVにまとめて保存
if all_rows:
    df = pd.DataFrame(all_rows, columns=[
        "image","person_id","keypoint_id","keypoint_name","x","y","confidence","width","height"
    ])
    csv_path = os.path.join(save_dir, "all_keypoints.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"まとめCSVを保存: {csv_path}")
else:
    print("有効なキーポイント検出がありませんでした。")
