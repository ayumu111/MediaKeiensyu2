import pygame
import threading
import os
from core.scene import Scene
from core.score_predictor_service import ScorePredictorService

class ScoreCalculationScene(Scene):
    def __init__(self):
        super().__init__()
        # フォント設定
        base_dir = os.path.dirname(os.path.dirname(__file__))
        font_path = os.path.join(base_dir, "font", "ikamodoki1_0.ttf")
        try:
            self.font = pygame.font.Font(font_path, 60)
        except:
            self.font = pygame.font.SysFont(None, 60)
        
        self.text_surf = self.font.render("けいさんちゅう...", True, pygame.Color("WHITE"))
        self.text_rect = self.text_surf.get_rect(center=(400, 300))

        self.predictor_service = ScorePredictorService()
        
        self.calculation_done = False
        self.calculation_success = False
        self.is_game_over = False
        self.thread_started = False

    def _run_calculation(self):
        print("計算スレッド開始")
        # サービス実行（詳細保存 & 合計追記 & 終了判定）
        success, is_over = self.predictor_service.process_latest_images()
        self.calculation_success = success
        self.is_game_over = is_over
        self.calculation_done = True
        print("計算スレッド終了")

    def update(self, dt):
        if not self.thread_started:
            thread = threading.Thread(target=self._run_calculation)
            thread.daemon = True
            thread.start()
            self.thread_started = True
        
        if self.calculation_done:
            if self.calculation_success:
                print("計算成功。")
                print("ラウンド終了 -> 結果表示へ")
                self.request_next("round_result")
            else:
                print("計算失敗 -> タイトルへ")
                self.request_next("title")

    def draw(self, surface):
        surface.fill(pygame.Color("BLACK"))
        surface.blit(self.text_surf, self.text_rect)