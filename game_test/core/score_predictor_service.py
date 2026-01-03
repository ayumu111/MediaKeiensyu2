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
        
        # 1. ラウンド詳細結果用 (ここは詳細な数値を保存します: 画面表示用)
        self.SCORE_FILE_DETAIL = os.path.join(base_dir, "scores.txt")

        # 2. 累積スコア用 (★ここは「合計点のみ」を保存します)
        self.SCORE_FILE_1P = os.path.join(base_dir, "1Pscores.txt")
        self.SCORE_FILE_2P = os.path.join(base_dir, "2Pscores.txt")

        # 画像フォルダ
        self.IMAGE_DIR = os.path.join(base_dir, "outputs_estimated")

        # モデルパス定義
        model_dir = os.path.join(base_dir, "model")
        self.MODEL_PATHS = {
            "Dynamic": os.path.join(model_dir, "dynamic_score_model_final.keras"),
            "Stable":  os.path.join(model_dir, "stable_score_model_final.keras"),
            "Unique":  os.path.join(model_dir, "unique_score_model_final.keras")
        }

        self.loaded_models = {}
        self.load_all_models()

    def load_all_models(self):
        print("=== モデル読み込み開始 ===")
        for model_name, model_path in self.MODEL_PATHS.items():
            if os.path.exists(model_path):
                print(f"[{model_name}] モデルを読み込んでいます...")
                try:
                    with tf.device('/CPU:0'): 
                         self.loaded_models[model_name] = load_model(model_path, compile=False)
                    print(f" -> {model_name} 読み込み完了")
                except Exception as e:
                    print(f"エラー: {model_name} の読み込みに失敗しました: {e}")
            else:
                print(f"警告: ファイルが見つかりません: {model_path}")
        print("=== 全モデル読み込み完了 ===\n")

    def get_latest_two_images(self):
        if not os.path.exists(self.IMAGE_DIR): return []
        image_files = glob.glob(os.path.join(self.IMAGE_DIR, "*.jpg")) + \
                      glob.glob(os.path.join(self.IMAGE_DIR, "*.png"))
        image_files.sort(key=os.path.getmtime, reverse=True)
        return image_files[:2]

    def predict(self, image_path):
        if not os.path.exists(image_path): return None
        img = cv2.imread(image_path)
        if img is None: return None
        img = cv2.resize(img, (self.IMAGE_WIDTH, self.IMAGE_HEIGHT))
        img = np.array([img])
        img = preprocess_input(img)

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

    # --- ヘルパーメソッド ---

    def calculate_total_score(self, scores_dict):
        """
        生スコア辞書を受け取り、重み付け計算を行って
        「1つの整数（合計点）」だけを返す
        """
        # 1. 各要素を四捨五入して整数にする
        d = int(round(scores_dict.get("Dynamic", 0.0)))
        s = int(round(scores_dict.get("Stable", 0.0)))
        u = int(round(scores_dict.get("Unique", 0.0)))
        
        # 2. 重み付け計算 (Dynamic*3 + Stable*3 + Unique*4)
        total = (d * 3) + (s * 3) + (u * 4)
        
        return total # 整数のみを返す

    def save_detail_scores(self, scores_2p, scores_1p):
        """scores.txt には詳細な内訳を保存する（ラウンド結果画面のメーター表示用）"""
        d2 = int(round(scores_2p.get("Dynamic", 0.0)))
        s2 = int(round(scores_2p.get("Stable", 0.0)))
        u2 = int(round(scores_2p.get("Unique", 0.0)))
        d1 = int(round(scores_1p.get("Dynamic", 0.0)))
        s1 = int(round(scores_1p.get("Stable", 0.0)))
        u1 = int(round(scores_1p.get("Unique", 0.0)))
        
        content = f"{d2},{s2},{u2},{d1},{s1},{u1}"
        
        try:
            with open(self.SCORE_FILE_DETAIL, "w", encoding="utf-8") as f:
                f.write(content)
            # print(f"[scores.txt] 詳細保存: {content}")
            return True
        except Exception as e:
            print(f"詳細保存エラー: {e}")
            return False

    def append_total_score(self, filepath, score_val, reset=False):
        """
        ★重要★
        この関数は受け取った「score_val（合計点）」のみをファイルに保存します。
        他の数値は保存しません。
        """
        current_scores = []
        if not reset and os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        current_scores = content.split(",")
            except: pass
        
        # 合計点のみを追加
        current_scores.append(str(score_val))
        new_content = ",".join(current_scores)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            action = "新規(リセット)" if reset else "追記"
            print(f"[{os.path.basename(filepath)}] に{action}: {new_content}")
            return True
        except Exception as e:
            print(f"累積保存エラー: {e}")
            return False

    def get_round_count(self):
        if not os.path.exists(self.SCORE_FILE_1P): return 0
        try:
            with open(self.SCORE_FILE_1P, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content: return 0
                return len(content.split(","))
        except: return 0

    def display_round_history(self):
        """履歴表示（デバッグ用）"""
        scores_1p = []
        scores_2p = []
        if os.path.exists(self.SCORE_FILE_1P):
            with open(self.SCORE_FILE_1P, "r", encoding="utf-8") as f:
                c = f.read().strip()
                if c: scores_1p = c.split(",")
        if os.path.exists(self.SCORE_FILE_2P):
            with open(self.SCORE_FILE_2P, "r", encoding="utf-8") as f:
                c = f.read().strip()
                if c: scores_2p = c.split(",")

        print("\n--- 現在の戦績 (合計点のみ) ---")
        rounds = max(len(scores_1p), len(scores_2p))
        for i in range(rounds):
            s1 = scores_1p[i] if i < len(scores_1p) else "--"
            s2 = scores_2p[i] if i < len(scores_2p) else "--"
            print(f"Round {i+1} | 1P: {s1}点, 2P: {s2}点")
        print("------------------------------\n")

    # --- メイン処理 ---
    
    def process_latest_images(self):
        target_images = self.get_latest_two_images()
        if len(target_images) < 2:
            print("エラー: 画像不足")
            return False, False
        
        img_path_2p = target_images[0]
        img_path_1p = target_images[1]
        
        print(">> スコア計算中...")
        scores_2p_raw = self.predict(img_path_2p)
        scores_1p_raw = self.predict(img_path_1p)

        if not (scores_2p_raw and scores_1p_raw):
            return False, False

        # 1. scores.txt には詳細を保存（変更なし）
        if not self.save_detail_scores(scores_2p_raw, scores_1p_raw):
            return False, False

        # 2. ここで重み付け合計点を計算！
        # これが「合計点のみ」になります
        total_2p = self.calculate_total_score(scores_2p_raw)
        total_1p = self.calculate_total_score(scores_1p_raw)
        
        print(f"今回の算出合計点 -> 1P: {total_1p}, 2P: {total_2p}")

        # リセット判定
        current_rounds = self.get_round_count()
        should_reset = False
        if current_rounds >= 3:
            print(f"警告: 既に{current_rounds}ラウンド分あるためリセットします。")
            should_reset = True

        # 3. 1Pscores.txt / 2Pscores.txt には「合計点のみ」を保存
        s1 = self.append_total_score(self.SCORE_FILE_1P, total_1p, reset=should_reset)
        s2 = self.append_total_score(self.SCORE_FILE_2P, total_2p, reset=should_reset)
        
        if not (s1 and s2):
            return False, False

        # 履歴表示
        self.display_round_history()

        # 4. 終了判定
        rounds = self.get_round_count()
        is_game_over = (rounds >= 3)
        print(f"現在の完了ラウンド: {rounds}/3")

        return True, is_game_over