import pygame
import threading
import os
from core.scene import Scene
from core.score_predictor_service import ScorePredictorService

class ScoreCalculationScene(Scene):
    def __init__(self):
        super().__init__()
        # フォント設定
        current_dir = os.path.dirname(__file__)
        font_path = os.path.join(current_dir, "Paintball_Beta_3.ttf") # 適切なフォントパスを指定
        try:
            self.font = pygame.font.Font(font_path, 60)
        except:
            self.font = pygame.font.SysFont(None, 60)
        
        self.text_surf = self.font.render("けいさんちゅう...", True, pygame.Color("WHITE"))
        self.text_rect = self.text_surf.get_rect(center=(400, 300)) # 画面中央 (800x600想定)

        # 計算サービス
        self.predictor_service = ScorePredictorService()
        
        # 計算状態管理
        self.calculation_done = False
        self.calculation_success = False
        self.thread_started = False

    def _run_calculation(self):
        """別スレッドで実行される計算処理"""
        print("計算スレッド開始")
        # 最新2枚の画像を処理
        success = self.predictor_service.process_latest_images()
        self.calculation_success = success
        self.calculation_done = True
        print("計算スレッド終了")

    def update(self, dt):
        # 最初のフレームで計算スレッドを開始
        if not self.thread_started:
            thread = threading.Thread(target=self._run_calculation)
            thread.daemon = True # メイン終了時に道連れにする
            thread.start()
            self.thread_started = True
        
        # 計算が完了したら次のシーンへ
        if self.calculation_done:
            if self.calculation_success:
                print("計算完了。結果画面へ遷移します。")
                self.request_next("round_result") # 結果表示シーンへ
            else:
                print("計算に失敗しました。タイトルへ戻ります。")
                self.request_next("title") # エラー時はタイトルなどへ

    def draw(self, surface):
        surface.fill(pygame.Color("BLACK")) # 背景黒
        surface.blit(self.text_surf, self.text_rect)