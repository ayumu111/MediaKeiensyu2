import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D, BatchNormalization
from tensorflow.keras.applications import VGG16
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.applications.vgg16 import preprocess_input
import pandas as pd
import cv2
import os
import numpy as np
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# ==========================================
# 1. データセットの準備
# ==========================================
image_height = 128
image_width = 128
img_dir = "single_fullbody_pose_black_bg" 
excel_path = "newcoolness_scores.xlsx"

# 画像読み込み
print("画像読み込み中...")
images = []
valid_indices = [] # 読み込めた画像のインデックスを記録
image_files = os.listdir(img_dir)

# 先頭から順番にチェック
for i, image_file in enumerate(image_files):
    if i >= 998: break # 998枚まで
    
    image_path = os.path.join(img_dir, image_file)
    image = cv2.imread(image_path)
    if image is None:
        continue
        
    image = cv2.resize(image, (image_width, image_height))
    images.append(image)
    valid_indices.append(i) # Excelの対応する行を取得するために必要

images = np.array(images)
print(f"画像読み込み完了: {images.shape}")

# Excel読み込み
df = pd.read_excel(excel_path)

# ★重要★: 読み込めた画像に対応する行だけを抽出
# 画像とExcelの行がズレている可能性を減らします
labels_df = df.iloc[valid_indices]

# 学習させるラベルを選択 (ここでは 'unique' に設定しています)
# Excelの列名が正しいか確認してください ('avg_unique' か 'unique' か)
target_column = "avg_stable"

print(f"使用するラベル列: {target_column}")
if target_column not in labels_df.columns:
    print(f"Error: Excelに '{target_column}' という列がありません。")
    print(f"存在する列名: {labels_df.columns.tolist()}")
    exit()

# ラベルデータの統計を確認 (ここが重要！)
raw_labels = labels_df[target_column].values
print(f"ラベルデータの最大値: {raw_labels.max()}")
print(f"ラベルデータの最小値: {raw_labels.min()}")
print(f"ラベルデータの平均値: {raw_labels.mean()}")

# もし最大値が0なら、データがおかしいです
if raw_labels.max() == 0:
    print("Error: 正解データがすべて0です。Excelの中身か列名を確認してください。")
    exit()

# 正規化 (0-10 -> 0.0-1.0)
normalized_labels = raw_labels / 10.0

# 分割
train_images, test_images, train_labels, test_labels = train_test_split(
    images, normalized_labels, test_size=0.2, random_state=42
)

# 前処理 (VGG16用)
train_images = preprocess_input(train_images.copy())
test_images = preprocess_input(test_images.copy())

# ==========================================
# 2. モデル構築 (VGG16 - 微調整版)
# ==========================================
def create_model():
    base_model = VGG16(weights='imagenet', include_top=False, input_shape=(image_height, image_width, 3))
    
    # ★VGG16の最後の数層だけ学習させる (Unfreezing)
    # これにより「Unique」のような抽象的な特徴を捉えやすくなります
    base_model.trainable = True
    for layer in base_model.layers[:-4]: # 後ろの4層以外は固定
        layer.trainable = False

    model = Sequential([
        base_model,
        GlobalAveragePooling2D(),
        
        Dense(256, activation='relu'), # reluに戻します(安定性のため)
        BatchNormalization(),
        Dropout(0.5),
        
        # ★出力層を Linear に変更 (Sigmoidだと0に張り付くことがあるため)
        # これでマイナスの値が出たら「学習不足」とわかります
        Dense(1, activation='sigmoid') 
    ])

    model.compile(optimizer=Adam(learning_rate=1e-5), # 微調整なので学習率はさらに小さく
                  loss='mse',
                  metrics=['mae'])
    return model

# ==========================================
# 3. 学習と評価
# ==========================================
model = create_model()
print("学習開始...")
history = model.fit(train_images, train_labels, epochs=15, batch_size=32, validation_split=0.2)

# 予測テスト
predict_image_path = "test/2011tokyo_mister_fp-011-320x480.jpg"
if os.path.exists(predict_image_path):
    img = cv2.imread(predict_image_path)
    if img is not None:
        img = cv2.resize(img, (image_width, image_height))
        img = np.array([img])
        img = preprocess_input(img) # 前処理

        # 予測
        pred = model.predict(img)[0][0]
        
        # Linearなので値がそのまま出ます。10倍してスコアに戻します。
        # もしマイナスが出たら 0 とみなします。
        final_score = pred * 10.0
        
        print(f"Raw Prediction (0.0-1.0): {pred}")
        print(f"Dynamic Score (0-10): {final_score:.2f}")
    else:
        print("画像読み込みエラー")
else:
    print("予測用画像なし")



# モデル保存
model.save('dynamicscore_model_final.keras')
print("モデルを保存しました: dynamicscore_model_final.keras")