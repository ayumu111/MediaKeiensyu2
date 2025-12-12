import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.vgg16 import preprocess_input
import cv2
import numpy as np
import os

# ==========================================
# 設定
# ==========================================
# 学習時と同じサイズにする必要があります
IMAGE_HEIGHT = 128
IMAGE_WIDTH = 128

# 保存したモデルのパス
MODEL_PATH = 'model\dynamicscore_model_final.keras'
#MODEL_PATH = 'model\stablescore_model_final.keras'
#MODEL_PATH = 'model\uniquecscore_model_final.keras'


# 予測したい画像のパス (テストしたい画像のパスに変えてください)
TARGET_IMAGE_PATH = "test/2011tokyo_mister_fp-011-320x480.jpg"

# ==========================================
# 1. モデルの読み込み
# ==========================================
if not os.path.exists(MODEL_PATH):
    print(f"エラー: モデルファイルが見つかりません: {MODEL_PATH}")
    exit()

print("モデルを読み込んでいます...")
model = load_model(MODEL_PATH)
print("読み込み完了！")

# ==========================================
# 2. 予測関数の定義
# ==========================================
def predict_coolness(image_path):
    # 画像の読み込み
    if not os.path.exists(image_path):
        print(f"画像が見つかりません: {image_path}")
        return None

    img = cv2.imread(image_path)
    if img is None:
        print("画像の読み込みに失敗しました。")
        return None

    # リサイズ (学習時と同じサイズへ)
    img = cv2.resize(img, (IMAGE_WIDTH, IMAGE_HEIGHT))

    # 次元の拡張 (1, 128, 128, 3)
    # AIは「画像の束(バッチ)」を入力として期待するため、1枚でも配列に入れます
    img = np.array([img])

    # ★重要★ 前処理 (VGG16用)
    # 学習時にもこれを使ったので、予測時にも必須です！
    img = preprocess_input(img)

    # 予測実行
    prediction = model.predict(img, verbose=0)
    
    # 0.0~1.0 で出てくるので 10倍してスコア化
    raw_score = prediction[0][0]
    final_score = raw_score * 10.0
    
    return final_score

# ==========================================
# 3. 実行
# ==========================================
score = predict_coolness(TARGET_IMAGE_PATH)

if score is not None:
    print("-" * 30)
    print(f"画像ファイル: {TARGET_IMAGE_PATH}")
    print(f"AIの判定スコア: {score:.2f} 点 / 10.0点")
    print("-" * 30)