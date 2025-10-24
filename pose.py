import os
from glob import glob
import argparse
from tqdm import tqdm
import numpy as np
from ultralytics import YOLO
import cv2

def safe_to_numpy(kp):
    if kp is None:
        return None
    try:
        return np.array(kp)
    except Exception:
        try:
            return np.array(kp.cpu())
        except Exception:
            return kp

def infer_folder(model_path, images_dir, out_dir, imgsz=640, conf=0.25, device='0'):
    os.makedirs(out_dir, exist_ok=True)
    ann_dir = os.path.join(out_dir, "annotated")
    kp_dir = os.path.join(out_dir, "keypoints")
    os.makedirs(ann_dir, exist_ok=True)
    os.makedirs(kp_dir, exist_ok=True)

    model = YOLO(model_path, device=device)
    paths = sorted(glob(os.path.join(images_dir, "*.*")))
    for p in tqdm(paths, desc="Images"):
        try:
            results = model.predict(source=p, imgsz=imgsz, conf=conf, verbose=False)
        except Exception as e:
            print("Model predict error:", p, e)
            continue

        for r in results:
            # annotated image
            try:
                annotated = r.plot()  # RGB numpy
                out_img = os.path.join(ann_dir, os.path.splitext(os.path.basename(p))[0] + ".jpg")
                cv2.imwrite(out_img, cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
            except Exception as e:
                print("Could not save annotated image for", p, e)

            # keypoints
            kp_arr = None
            try:
                if hasattr(r, "keypoints") and r.keypoints is not None:
                    kp_arr = safe_to_numpy(r.keypoints)
                out_npz = os.path.join(kp_dir, os.path.splitext(os.path.basename(p))[0] + ".npz")
                np.savez_compressed(out_npz, keypoints=kp_arr, image_path=p)
            except Exception as e:
                print("Could not save keypoints for", p, e)

            break  # 1画像につき1結果で良ければ break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="yolo11n-pose.pt")
    parser.add_argument("--images", required=True, help="画像フォルダのパス（例: datasets/lsp/images）")
    parser.add_argument("--out", default="runs/lsp_infer")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--device", default="0", help="'cpu' or GPU id like '0' or 'cuda:0'")
    args = parser.parse_args()
    infer_folder(args.model, args.images, args.out, imgsz=args.imgsz, conf=args.conf, device=args.device)