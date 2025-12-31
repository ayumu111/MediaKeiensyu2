import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.vgg16 import preprocess_input
import cv2
import numpy as np
import os
import glob

class ScorePredictorService:
    def __init__(self):
        # --- 設定 ---
        self.IMAGE_HEIGHT = 128
        self.IMAGE_WIDTH = 128
        
        # ベースディレクトリ (game_testフォルダ)
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # ▼▼▼ 修正: 出力ファイルを scores.txt ひとつに戻す ▼▼▼
        self.SCORE_FILE = os.path.join(base_dir, "scores.txt")
        # ▲▲▲▲▲▲

        # 画像フォルダのパス (game_test/outputs_estimated)
        self.IMAGE_DIR = os.path.join(base_dir, "outputs_estimated")

        # モデルパス定義 (game_test/model/...)
        model_dir = os.path.join(base_dir, "model")
        self.MODEL_PATHS = {
            "Dynamic": os.path.join(model_dir, "dynamic_score_model_final.keras"),
            "Stable":  os.path.join(model_dir, "stable_score_model_final.keras"),
            "Unique":  os.path.join(model_dir, "unique_score_model_final.keras")
        }

        self.loaded_models = {}
        self.load_all_models()

    def load_all_models(self):
        """モデルを全て読み込む"""
        print("=== モデル読み込み開始 ===")
        # (中略: 変更なし)
        for model_name, model_path in self.MODEL_PATHS.items():
            if os.path.exists(model_path):
                print(f"[{model_name}] モデルを読み込んでいます...")
                try:
                    # TFの警告を抑制してロード
                    with tf.device('/CPU:0'): 
                         self.loaded_models[model_name] = load_model(model_path, compile=False)
                    print(f" -> {model_name} 読み込み完了")
                except Exception as e:
                    print(f"エラー: {model_name} の読み込みに失敗しました: {e}")
            else:
                print(f"警告: ファイルが見つかりません: {model_path}")
        print("=== 全モデル読み込み完了 ===\n")

    def get_latest_two_images(self):
        """指定フォルダから最新の画像2枚のパスを取得（0番目が最新、1番目が準最新）"""
        if not os.path.exists(self.IMAGE_DIR):
            print(f"フォルダが見つかりません: {self.IMAGE_DIR}")
            return []

        # jpgとpngを検索
        image_files = glob.glob(os.path.join(self.IMAGE_DIR, "*.jpg")) + \
                      glob.glob(os.path.join(self.IMAGE_DIR, "*.png"))
        
        # 更新日時でソート（新しい順: [最新, 準最新, その前...]）
        image_files.sort(key=os.path.getmtime, reverse=True)
        
        # 最新の2枚を返す
        return image_files[:2]

    def predict(self, image_path):
        """画像パスを受け取り、予測を実行してスコアの辞書を返す"""
        if not os.path.exists(image_path): return None
        img = cv2.imread(image_path)
        if img is None: return None

        # 前処理
        img = cv2.resize(img, (self.IMAGE_WIDTH, self.IMAGE_HEIGHT))
        img = np.array([img])
        img = preprocess_input(img)

        # 予測
        results = {}
        target_order = ["Dynamic", "Stable", "Unique"]
        for name in target_order:
            model = self.loaded_models.get(name)
            if model:
                prediction = model.predict(img, verbose=0)
                results[name] = prediction[0][0] * 10.0
            else:
                results[name] = 0.0
        return results

    # ▼▼▼ 大幅修正: 2つのスコア辞書を受け取ってまとめて保存するメソッドに変更 ▼▼▼
    # ▼▼▼ 修正: スコアを整数（四捨五入）で保存するように変更 ▼▼▼
    def save_combined_scores(self, scores_2p, scores_1p):
        """2Pと1Pのスコア辞書を受け取り、整数にして一つのファイルにまとめて保存する"""
        # 2Pのスコア抽出と四捨五入して整数化
        d2 = int(round(scores_2p.get("Dynamic", 0.0)))
        s2 = int(round(scores_2p.get("Stable", 0.0)))
        u2 = int(round(scores_2p.get("Unique", 0.0)))
        
        # 1Pのスコア抽出と四捨五入して整数化
        d1 = int(round(scores_1p.get("Dynamic", 0.0)))
        s1 = int(round(scores_1p.get("Stable", 0.0)))
        u1 = int(round(scores_1p.get("Unique", 0.0)))

        # 文字列作成 (整数でカンマ区切り)
        new_scores_str = f"{d2},{s2},{u2},{d1},{s1},{u1}"

        try:
            # 上書きモード(w)で保存
            with open(self.SCORE_FILE, "w", encoding="utf-8") as f:
                f.write(new_scores_str)
            print(f"[{os.path.basename(self.SCORE_FILE)}] に保存しました: {new_scores_str}")
            return True
        except Exception as e:
            print(f"保存エラー: {e}")
            return False
    # ▲▲▲▲▲▲

    # ▼▼▼ 修正: 予測結果をまとめて保存メソッドに渡すように変更 ▼▼▼
    def process_latest_images(self):
        """最新2枚の画像を処理し、scores.txtにまとめて保存する"""
        target_images = self.get_latest_two_images()
        
        if len(target_images) < 2:
            print(f"エラー: 処理対象の画像が足りません。(現在の枚数: {len(target_images)}枚)")
            return False
        
        img_path_2p = target_images[0] # 一番新しい -> 2P
        img_path_1p = target_images[1] # その次に新しい -> 1P
        
        print("-" * 40)
        print(f"最新画像 (2P用): {os.path.basename(img_path_2p)}")
        print(f"準最新画像 (1P用): {os.path.basename(img_path_1p)}")
        print("-" * 40)

        # 予測実行
        print(">> 2Pのスコア計算中...")
        scores_2p = self.predict(img_path_2p)
        print(">> 1Pのスコア計算中...")
        scores_1p = self.predict(img_path_1p)

        # 両方成功したら保存処理へ
        if scores_2p and scores_1p:
            print(">> 計算完了。ファイルに保存します...")
            return self.save_combined_scores(scores_2p, scores_1p)
        else:
            print("予測に失敗した画像があります。保存を中止します。")
            return False
    # ▲▲▲▲▲▲

# 単体テスト用
if __name__ == "__main__":
    service = ScorePredictorService()
    print("\n--- 単体テスト実行 ---")
    service.process_latest_images()