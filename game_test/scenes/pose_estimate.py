
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from ultralytics import YOLO


class PoseEstimatorConfig:
    def __init__(
        self,
        model_path: str = "yolo11n-pose.pt",
        device: Optional[str] = None,   # "cpu" or "cuda"
        kpt_radius: int = 5,
        line_width: int = 2,
        draw_on_black_bg: bool = False, # ゲーム画面に重ねる前提なら False
        score_threshold: Optional[float] = None,
    ):
        self.model_path = model_path
        self.device = device
        self.kpt_radius = kpt_radius
        self.line_width = line_width
        self.draw_on_black_bg = draw_on_black_bg
        self.score_threshold = score_threshold


class PoseEstimator:
    COCO_KPT_NAMES_17 = [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ]

    def __init__(self, config: Optional[PoseEstimatorConfig] = None):
        self.cfg = config or PoseEstimatorConfig()
        self.model: YOLO = YOLO(self.cfg.model_path)

    def estimate(self, image_or_path: Any) -> Dict[str, Any]:
        """単一画像に対して骨格推定を行う。"""
        results = self.model.predict(source=image_or_path, device=self.cfg.device, verbose=False)
        res = results[0]

        # 画像サイズの取得
        if isinstance(image_or_path, np.ndarray):
            h, w = image_or_path.shape[:2]
            base_img = image_or_path
        else:
            base_img = cv2.imread(str(image_or_path))
            if base_img is None:
                raise ValueError(f"画像の読み込みに失敗: {image_or_path}")
            h, w = base_img.shape[:2]

        # キーポイントが無い場合
        if res.keypoints is None or res.keypoints.shape[0] == 0:
            return {
                "num_persons": 0, "width": w, "height": h,
                "keypoints": {}, "rows": [], "raw": res, "base": base_img
            }

        # キーポイント抽出
        kpts_xy = res.keypoints.xy
        kpts_conf = res.keypoints.conf
        num_persons, num_kpts = kpts_xy.shape[0], kpts_xy.shape[1]

        # キー名
        if len(self.COCO_KPT_NAMES_17) >= num_kpts:
            kpt_names = self.COCO_KPT_NAMES_17[:num_kpts]
        else:
            kpt_names = self.COCO_KPT_NAMES_17 + [f"kpt_{i}" for i in range(len(self.COCO_KPT_NAMES_17), num_kpts)]

        grouped: Dict[int, List[Dict[str, Any]]] = {}
        all_rows: List[Dict[str, Any]] = []

        for pid in range(num_persons):
            grouped.setdefault(pid, [])
            for kid in range(num_kpts):
                x = float(kpts_xy[pid, kid, 0])
                y = float(kpts_xy[pid, kid, 1])
                conf = float(kpts_conf[pid, kid]) if kpts_conf is not None else None

                if self.cfg.score_threshold is not None and conf is not None and conf < self.cfg.score_threshold:
                    continue

                grouped[pid].append({
                    "keypoint_id": kid, "keypoint_name": kpt_names[kid],
                    "x": x, "y": y, "confidence": conf
                })
                all_rows.append({
                    "person_id": pid, "keypoint_id": kid, "keypoint_name": kpt_names[kid],
                    "x": x, "y": y, "confidence": conf, "width": w, "height": h
                })

        return {
            "num_persons": num_persons, "width": w, "height": h,
            "keypoints": grouped, "rows": all_rows, "raw": res, "base": base_img
        }

    def draw(self, base_image: np.ndarray, raw_result, on_black: Optional[bool] = None) -> np.ndarray:
        """推論結果を base_image 上（または黒背景）に描画して返す。"""
        if raw_result is None:
            return base_image

        h, w = base_image.shape[:2]
        use_black = self.cfg.draw_on_black_bg if on_black is None else on_black
        canvas = np.zeros((h, w, 3), dtype=np.uint8) if use_black else base_image.copy()

        drawn = raw_result.plot(img=canvas, kpt_radius=self.cfg.kpt_radius, line_width=self.cfg.line_width)
        return drawn

    def process_image(self, image_or_path: Any, on_black: Optional[bool] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """画像を渡すだけで推論→描画まで行い、(描画済画像, 推論辞書) を返す。"""
        info = self.estimate(image_or_path)
        base = info["base"]
        drawn = self.draw(base, info["raw"], on_black=on_black)
        return drawn, info
