import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.vgg16 import preprocess_input
import cv2
import numpy as np
import os

# ==========================================
# 設定
# ==========================================
IMAGE_HEIGHT = 128
IMAGE_WIDTH = 128

# 3つのモデルのパスを辞書で定義
# ※ファイル名が実際の保存名と合っているか確認してください
MODEL_PATHS = {
    "Dynamic": "model/dynamic_score_model_final.keras",
    "Stable":  "model/stable_score_model_final.keras",
    "Unique":  "model/unique_score_model_final.keras"
}

# 予測したい画像のパス
TARGET_IMAGE_PATH = "test/2011tokyo_mister_fp-011-320x480.jpg"

# ==========================================
# 1. モデルの読み込み (3つ全て読み込む)
# ==========================================
loaded_models = {}

print("=== モデル読み込み開始 ===")
for model_name, model_path in MODEL_PATHS.items():
    if os.path.exists(model_path):
        print(f"[{model_name}] モデルを読み込んでいます...")
        try:
            # モデルをロードして辞書に格納
            loaded_models[model_name] = load_model(model_path)
            print(f" -> {model_name} 読み込み完了")
        except Exception as e:
            print(f"エラー: {model_name} の読み込みに失敗しました: {e}")
    else:
        print(f"警告: ファイルが見つかりません: {model_path}")

if not loaded_models:
    print("エラー: 有効なモデルが一つも読み込めませんでした。終了します。")
    exit()

print("=== 全モデル読み込み完了 ===\n")

# ==========================================
# 2. 予測関数の定義
# ==========================================
def predict_all_scores(image_path):
    # --- 画像の前処理 (共通) ---
    if not os.path.exists(image_path):
        print(f"画像が見つかりません: {image_path}")
        return None

    img = cv2.imread(image_path)
    if img is None:
        print("画像の読み込みに失敗しました。")
        return None

    # リサイズ (128x128)
    img = cv2.resize(img, (IMAGE_WIDTH, IMAGE_HEIGHT))

    # 次元の拡張 (1, 128, 128, 3)
    img = np.array([img])

    # VGG16用の前処理
    img = preprocess_input(img)

    # --- 各モデルで予測を実行 ---
    results = {}
    
    # 読み込んだモデルを順番に回して予測
    for name, model in loaded_models.items():
        # 予測実行 (verbose=0 でログ出力を抑制)
        prediction = model.predict(img, verbose=0)
        
        # スコア計算 (0.0~1.0 -> 0.0~10.0)
        raw_score = prediction[0][0]
        final_score = raw_score * 10.0
        
        # 結果を辞書に保存
        results[name] = final_score
    
    return results

# ==========================================
# 3. 実行と結果表示
# ==========================================
print(f"画像ファイル: {TARGET_IMAGE_PATH} の判定を開始します...\n")

scores = predict_all_scores(TARGET_IMAGE_PATH)

if scores is not None:
    print("-" * 40)
    print(f"【 採点結果 】")
    print("-" * 40)
    
    # 各スコアを表示
    # 辞書から取り出して表示
    d_score = scores.get("Dynamic", 0.0)
    s_score = scores.get("Stable", 0.0)
    u_score = scores.get("Unique", 0.0)

    print(f"Dynamic (躍動感): {d_score:5.2f} / 10.0")
    print(f"Stable  (安定感): {s_score:5.2f} / 10.0")
    print(f"Unique  (独自性): {u_score:5.2f} / 10.0")
    
    # 合計や平均を出したい場合
    avg_score = (d_score + s_score + u_score) / 3
    print("-" * 40)
    print(f"総合平均スコア  : {avg_score:5.2f} / 10.0")
    print("-" * 40)