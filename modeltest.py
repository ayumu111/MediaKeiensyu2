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

# スコアを保存するテキストファイル名
SCORE_FILE = "scores.txt"

# 3つのモデルのパスを辞書で定義
# ※拡張子が .keras か .h5 か、実際のファイルに合わせてください
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
    
    # Dynamic, Stable, Unique の順で確実に取得したいため、キーを指定してループ
    target_order = ["Dynamic", "Stable", "Unique"]
    
    for name in target_order:
        model = loaded_models.get(name)
        if model:
            # 予測実行 (verbose=0 でログ出力を抑制)
            prediction = model.predict(img, verbose=0)
            
            # スコア計算 (0.0~1.0 -> 0.0~10.0)
            raw_score = prediction[0][0]
            final_score = raw_score * 10.0
            
            # 結果を辞書に保存
            results[name] = final_score
        else:
            results[name] = 0.0 # モデルがない場合は0点とする
    
    return results

# ==========================================
# 3. テキストファイルへの保存関数
# ==========================================
def save_scores_to_txt(new_scores):
    """
    scores.txt の状態を確認し、書き込みまたは追記を行う
    new_scores: [d_score, s_score, u_score] のリスト
    """
    # 新しいスコアをカンマ区切りの文字列にする (例: "4.5,3.2,8.9")
    new_scores_str = ",".join([f"{s:.2f}" for s in new_scores])
    
    existing_content = ""
    value_count = 0

    # ファイルが存在する場合、中身をチェック
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            existing_content = f.read().strip()
        
        if existing_content:
            # カンマで区切って現在いくつの数字が入っているか数える
            value_count = len(existing_content.split(","))

    print(f"現在のファイル内の数値個数: {value_count}")

    # ロジック分岐
    # 6個入っている場合 -> リセットして上書き (新規1P)
    # 0個(空)またはファイルなし -> 上書き (新規1P)
    # それ以外(通常は3個) -> 追記 (2P)
    
    if value_count == 6 or value_count == 0:
        mode = "w" # 上書きモード
        write_content = new_scores_str
        action_msg = "新規書き込み (1P)"
    else:
        mode = "w" # 読み込んだ内容 + 新しい内容 で全体を書き直す（またはaモードでも可）
        # ここでは安全のため全体構築して上書きします
        write_content = existing_content + "," + new_scores_str
        action_msg = "追記 (2P)"

    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        f.write(write_content)
    
    print(f"[{SCORE_FILE}] に保存しました: {action_msg}")
    print(f"保存内容: {write_content}")

# ==========================================
# 4. 実行と結果表示
# ==========================================
print(f"画像ファイル: {TARGET_IMAGE_PATH} の判定を開始します...\n")

scores_dict = predict_all_scores(TARGET_IMAGE_PATH)

if scores_dict is not None:
    print("-" * 40)
    print(f"【 採点結果 】")
    print("-" * 40)
    
    d_score = scores_dict.get("Dynamic", 0.0)
    s_score = scores_dict.get("Stable", 0.0)
    u_score = scores_dict.get("Unique", 0.0)

    print(f"Dynamic (躍動感): {d_score:5.2f} / 10.0")
    print(f"Stable  (安定感): {s_score:5.2f} / 10.0")
    print(f"Unique  (独自性): {u_score:5.2f} / 10.0")
    
    avg_score = (d_score + s_score + u_score) / 3
    print("-" * 40)
    print(f"総合平均スコア  : {avg_score:5.2f} / 10.0")
    print("-" * 40)

    # テキストファイルへ出力
    # Dynamic, Stable, Unique の順でリスト化
    score_list = [d_score, s_score, u_score]
    save_scores_to_txt(score_list)