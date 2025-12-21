import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.vgg16 import preprocess_input
import cv2
import numpy as np
import os

class ScorePredictor:
    def __init__(self):
        # --- 設定 ---
        self.IMAGE_HEIGHT = 128
        self.IMAGE_WIDTH = 128
        self.SCORE_FILE = "scores.txt" # 書き出すファイル名

        # モデルパス定義
        # ※実際のファイル構成に合わせてパスを修正してください
        self.MODEL_PATHS = {
            "Dynamic": "model/dynamic_score_model_final.keras",
            "Stable":  "model/stable_score_model_final.keras",
            "Unique":  "model/unique_score_model_final.keras"
        }

        self.loaded_models = {}
        self.load_all_models()

    def load_all_models(self):
        """モデルを全て読み込む（起動時に1回だけ呼ぶ想定）"""
        print("=== モデル読み込み開始 ===")
        for model_name, model_path in self.MODEL_PATHS.items():
            if os.path.exists(model_path):
                print(f"[{model_name}] モデルを読み込んでいます...")
                try:
                    self.loaded_models[model_name] = load_model(model_path)
                    print(f" -> {model_name} 読み込み完了")
                except Exception as e:
                    print(f"エラー: {model_name} の読み込みに失敗しました: {e}")
            else:
                print(f"警告: ファイルが見つかりません: {model_path}")

        if not self.loaded_models:
            print("エラー: 有効なモデルが一つも読み込めませんでした。")

        print("=== 全モデル読み込み完了 ===\n")

    def predict(self, image_path):
        """
        画像パスを受け取り、予測を実行してスコアの辞書を返す
        """
        # --- 画像の前処理 ---
        if not os.path.exists(image_path):
            print(f"画像が見つかりません: {image_path}")
            return None

        img = cv2.imread(image_path)
        if img is None:
            print("画像の読み込みに失敗しました。")
            return None

        # リサイズ & 前処理
        img = cv2.resize(img, (self.IMAGE_WIDTH, self.IMAGE_HEIGHT))
        img = np.array([img])
        img = preprocess_input(img)

        # --- 予測実行 ---
        results = {}
        target_order = ["Dynamic", "Stable", "Unique"]
        
        for name in target_order:
            model = self.loaded_models.get(name)
            if model:
                prediction = model.predict(img, verbose=0)
                raw_score = prediction[0][0]
                final_score = raw_score * 10.0
                results[name] = final_score
            else:
                results[name] = 0.0
        
        return results

    def save_scores(self, scores_dict):
        """
        スコア辞書を受け取り、テキストファイルに保存する
        """
        # 辞書からリストへ変換 (Dynamic, Stable, Unique順)
        d_score = scores_dict.get("Dynamic", 0.0)
        s_score = scores_dict.get("Stable", 0.0)
        u_score = scores_dict.get("Unique", 0.0)
        new_scores = [d_score, s_score, u_score]

        # 文字列作成
        new_scores_str = ",".join([f"{s:.2f}" for s in new_scores])
        
        existing_content = ""
        value_count = 0

        # ファイル読み込みチェック
        if os.path.exists(self.SCORE_FILE):
            with open(self.SCORE_FILE, "r", encoding="utf-8") as f:
                existing_content = f.read().strip()
            
            if existing_content:
                # カンマ区切りで要素数を数える
                # 空白や改行が含まれる場合を除去してカウント
                parts = [p for p in existing_content.split(",") if p.strip()]
                value_count = len(parts)

        print(f"現在のファイル内の数値個数: {value_count}")

        # ロジック分岐
        if value_count >= 6 or value_count == 0:
            # 6個埋まっている、または空なら -> 新規書き込み (1P)
            write_content = new_scores_str
            action_msg = "新規書き込み (1P)"
        else:
            # それ以外(3個など) -> 追記 (2P)
            write_content = existing_content + "," + new_scores_str
            action_msg = "追記 (2P)"

        with open(self.SCORE_FILE, "w", encoding="utf-8") as f:
            f.write(write_content)
        
        print(f"[{self.SCORE_FILE}] に保存しました: {action_msg}")
        return new_scores # 処理したスコアリストを返す

    def run_prediction_flow(self, target_image_path):
        """
        予測から保存までを一括で行う便利メソッド
        """
        print(f"画像ファイル: {target_image_path} の判定を開始します...")
        
        scores = self.predict(target_image_path)
        
        if scores is not None:
            # 結果表示
            d = scores.get("Dynamic", 0.0)
            s = scores.get("Stable", 0.0)
            u = scores.get("Unique", 0.0)
            avg = (d + s + u) / 3

            print("-" * 40)
            print(f"Dynamic: {d:5.2f}, Stable: {s:5.2f}, Unique: {u:5.2f}")
            print(f"Average: {avg:5.2f}")
            print("-" * 40)

            # 保存
            self.save_scores(scores)
            return True
        else:
            print("予測に失敗しました。")
            return False

# 単体テスト用
if __name__ == "__main__":
    predictor = ScorePredictor()
    # テスト画像を判定
    test_image = "test/2011tokyo_mister_fp-011-320x480.jpg"
    predictor.run_prediction_flow(test_image)