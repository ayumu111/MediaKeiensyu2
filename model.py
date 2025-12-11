import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.layers import Dropout
import pandas as pd
import keras_tuner as kt
import cv2
import os
import numpy as np
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt # matplotlibをインポート


# データセットの準備
image_height = 128  # 画像の高さ（リサイズ後）
image_width = 128   # 画像の幅（リサイズ後）

images = []
# 画像ファイル名のリストを取得（フォルダ内のすべてのファイル）
image_files = os.listdir("images_crop\\single_fullbody_pose_black_bg")

# 画像ファイルの数が 998 個であることを確認
if len(image_files) != 998:
    print(f"Warning: Number of image files is {len(image_files)}, not 998.")

# 各画像ファイルを読み込み、リサイズしてリストに追加
for image_file in image_files:
    image_path = os.path.join("images_crop\\single_fullbody_pose_black_bg", image_file)
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error reading image: {image_file}")
        continue
    image = cv2.resize(image, (image_width, image_height))
    images.append(image)

images = np.array(images)  # NumPy配列に変換

# Excelファイルからのラベルデータの読み込み（998行目まで）
labels = pd.read_excel("newcoolness_scores.xlsx", nrows=998)


dynamic_labels = labels["avg_dynamic"] / 10.0
stable_labels = labels["avg_stable"] / 10.0
unique_labels = labels["avg_unique"] / 10.0
# データセットの分割
# データセットの分割
train_images, test_images, train_dynamic, test_dynamic, train_stable, test_stable, train_unique, test_unique = train_test_split(images, dynamic_labels, stable_labels, unique_labels, test_size=0.2, random_state=42)

# モデルの構築関数
def create_model(hp):
    model = Sequential()
    
    # 畳み込み層
    filters_1 = hp.Int('filters_1', min_value=32, max_value=128, step=32) # 探索範囲を変更
    kernel_size_1 = hp.Choice('kernel_size_1', values=[3, 5])
    model.add(Conv2D(filters_1, kernel_size_1, activation='relu', input_shape=(image_height, image_width, 3)))
    model.add(MaxPooling2D((2, 2)))
    
    # ドロップアウト層
    dropout_rate_1 = hp.Float('dropout_rate_1', min_value=0.0, max_value=0.5, step=0.1)
    model.add(Dropout(dropout_rate_1))
    
    # Flatten層を追加
    model.add(Flatten())

    # 全結合層
    units_1 = hp.Int('units_1', min_value=64, max_value=256, step=64)
    model.add(Dense(units_1, activation='relu'))
    
    model.add(Dense(1, activation='sigmoid')) # 出力層

    # 学習率
    learning_rate = hp.Choice('learning_rate', values=[1e-2, 1e-3, 1e-4])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
                  loss='mse',
                  metrics=['mae'])
    return model


tuner = kt.RandomSearch(
    create_model,
    objective='val_mae',
    max_trials=10,  # 試行回数
    executions_per_trial=1, # 各試行での実行回数
    directory='my_dir',
    project_name='intro_to_kt'
)
# チューニングの実行
tuner.search(train_images, train_dynamic, epochs=10, validation_split=0.2)

# 最適なハイパーパラメータの取得
best_hps = tuner.get_best_hyperparameters(num_trials=1)[0]

# 最適なハイパーパラメータでモデルを構築
model = tuner.hypermodel.build(best_hps)

# 最適なハイパーパラメータでモデルを構築
dynamic_model = tuner.hypermodel.build(best_hps) # ここでdynamic_modelを構築

# モデルの訓練
history_dynamic = dynamic_model.fit(train_images, train_dynamic, epochs=50, validation_split=0.2) # エポック数を変更

# モデルの評価
loss, mae = model.evaluate(test_images, test_dynamic)
print(f"Test MAE: {mae}")


# --- ダイナミック性モデルの訓練と学習曲線の描画 ---
dynamic_model = create_model()
history_dynamic = dynamic_model.fit(train_images, train_dynamic, epochs=20, batch_size=32, validation_split=0.2)

# 学習曲線の描画（損失とMAE）
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(history_dynamic.history['loss'], label='Training Loss')
plt.plot(history_dynamic.history['val_loss'], label='Validation Loss')
plt.title('Dynamic Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss (MSE)')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history_dynamic.history['mae'], label='Training MAE')
plt.plot(history_dynamic.history['val_mae'], label='Validation MAE')
plt.title('Dynamic Model MAE')
plt.xlabel('Epoch')
plt.ylabel('MAE')
plt.legend()

# 画像ファイルとして保存
plt.savefig('dynamic_learning_curve.png')
plt.show() # 画面に表示（任意）

# # --- 安定感モデルの訓練と学習曲線の描画 ---
# stable_model = create_model()
# history_stable = stable_model.fit(train_images, train_stable, epochs=20, batch_size=32, validation_split=0.2)

# # 学習曲線の描画（損失）
# plt.figure(figsize=(12, 4))
# plt.subplot(1, 2, 1)
# plt.plot(history_stable.history['loss'], label='Training Loss')
# plt.plot(history_stable.history['val_loss'], label='Validation Loss')
# plt.title('Stable Model Loss')
# plt.xlabel('Epoch')
# plt.ylabel('Loss (MSE)')
# plt.legend()

# # 学習曲線の描画（MAE）
# plt.subplot(1, 2, 2)
# plt.plot(history_stable.history['mae'], label='Training MAE')
# plt.plot(history_stable.history['val_mae'], label='Validation MAE')
# plt.title('Stable Model MAE')
# plt.xlabel('Epoch')
# plt.ylabel('MAE')
# plt.legend()
# plt.show()


# # --- 独自性モデルの訓練と学習曲線の描画 ---
# unique_model = create_model()
# history_unique = unique_model.fit(train_images, train_unique, epochs=20, batch_size=32, validation_split=0.2)

# # 学習曲線の描画（損失）
# plt.figure(figsize=(12, 4))
# plt.subplot(1, 2, 1)
# plt.plot(history_unique.history['loss'], label='Training Loss')
# plt.plot(history_unique.history['val_loss'], label='Validation Loss')
# plt.title('Unique Model Loss')
# plt.xlabel('Epoch')
# plt.ylabel('Loss (MSE)')
# plt.legend()

# # 学習曲線の描画（MAE）
# plt.subplot(1, 2, 2)
# plt.plot(history_unique.history['mae'], label='Training MAE')
# plt.plot(history_unique.history['val_mae'], label='Validation MAE')
# plt.title('Unique Model MAE')
# plt.xlabel('Epoch')
# plt.ylabel('MAE')
# plt.legend()
# plt.show()

# ... (モデルの評価と予測のコードは省略)
# モデルの評価
dynamic_mse, dynamic_mae = dynamic_model.evaluate(test_images, test_dynamic)
#stable_mse, stable_mae = stable_model.evaluate(test_images, test_stable)
#unique_mse, unique_mae = unique_model.evaluate(test_images, test_unique)
print("Dynamic MSE:", dynamic_mse)
#print("Stable MSE:", stable_mse)
#print("Unique MSE:", unique_mse)

# 予測の実行
# 予測したい画像ファイルのパス
image_path = "test/2011tokyo_mister_fp-011-320x480.jpg"

# 画像の読み込みとリサイズ
image = cv2.imread(image_path)
image = cv2.resize(image, (image_width, image_height))

# NumPy配列に変換し、次元を拡張
image = np.array([image]) # (1, 128, 128, 3) の形状になる

# 予測の実行
dynamic_score = dynamic_model.predict(image)
#stable_score = stable_model.predict(image)
#unique_score = unique_model.predict(image)

print("Dynamic Score:", dynamic_score[0][0])
#print("Stable Score:", stable_score[0][0])
#print("Unique Score:", unique_score[0][0])