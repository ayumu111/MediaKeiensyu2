import pygame
import random
import sys
import cv2
import numpy as np

# --- 設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 50, 255) # 後攻用の青
GRAY = (100, 100, 100)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
DUMMY_BG = (50, 50, 50)
DARK_BLUE = (50, 50, 150)
LIGHT_BLUE = (100, 100, 255)

# 状態定義
STATE_SPINNING = 0
STATE_STOPPING = 1
STATE_FUSE     = 2
STATE_EXPLOSION = 3

# --- Helper Function ---
def cvimage_to_pygame(image):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width = image_rgb.shape[:2]
    image_surface = pygame.image.frombuffer(image_rgb.tostring(), (width, height), 'RGB')
    return image_surface

# --- Phase 3: ルーレット画面 (変更なし) ---
class Phase3Scene:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        try:
            self.font_large = pygame.font.SysFont("meiryo", 60)
            self.font_small = pygame.font.SysFont("meiryo", 30)
            self.font_bold  = pygame.font.SysFont("meiryo", 24, bold=True)
        except:
            self.font_large = pygame.font.Font(None, 60)
            self.font_small = pygame.font.Font(None, 30)
            self.font_bold  = pygame.font.Font(None, 24)

        self.themes = ["グリコ", "考える人", "シェー", "かめはめ波", "ジョジョ立ち", 
                       "ダブルピース", "土下座", "コマネチ", "命", "五郎丸"]
        self.fuse_duration = 3.0
        self.box_width = 400
        self.box_height = 100
        self.box_margin = 10
        self.visible_items = 3
        self.state = STATE_SPINNING
        self.start_ticks = pygame.time.get_ticks()
        self.fuse_start_ticks = 0
        self.explosion_start_ticks = 0
        self.scroll_pos = 0.0
        self.current_speed = 25.0
        self.item_height = self.box_height + self.box_margin
        self.center_y = SCREEN_HEIGHT // 2 + 50 
        self.final_theme = ""
        self.spin_duration_target = random.uniform(1.5, 3.0)
        self.friction = random.uniform(0.94, 0.97)

    def draw_dynamite_fuse(self, progress):
        start_x = 100
        end_x = 700
        y_pos = 80 
        dynamite_rect = pygame.Rect(end_x, y_pos - 15, 30, 60)
        pygame.draw.rect(self.screen, RED, dynamite_rect)
        pygame.draw.rect(self.screen, BLACK, dynamite_rect, 2)
        text_label = self.font_bold.render("撮影開始！", True, RED)
        label_rect = text_label.get_rect(center=(end_x + 15, y_pos + 60)) 
        self.screen.blit(text_label, label_rect)
        current_fuse_x = start_x + (end_x - start_x) * progress
        if current_fuse_x < end_x:
            pygame.draw.line(self.screen, GRAY, (current_fuse_x, y_pos), (end_x, y_pos), 5)
            if 0.0 < progress < 1.0:
                spark_size = random.randint(8, 16)
                pygame.draw.circle(self.screen, ORANGE, (int(current_fuse_x), y_pos), spark_size)
                pygame.draw.circle(self.screen, YELLOW, (int(current_fuse_x), y_pos), spark_size // 2)
    
    def draw_roulette(self):
        roulette_bg_rect = pygame.Rect(
            (SCREEN_WIDTH - self.box_width) // 2 - 20,
            self.center_y - (self.item_height * self.visible_items // 2) - 20,
            self.box_width + 40,
            self.item_height * self.visible_items + 40
        )
        pygame.draw.rect(self.screen, GRAY, roulette_bg_rect)
        clip_rect = pygame.Rect(0, roulette_bg_rect.top, SCREEN_WIDTH, roulette_bg_rect.height)
        self.screen.set_clip(clip_rect)
        base_index = int(self.scroll_pos / self.item_height)
        offset_y = self.scroll_pos % self.item_height
        start_i = base_index - self.visible_items // 2 - 1
        end_i = base_index + self.visible_items // 2 + 2
        for i in range(start_i, end_i):
            theme_index = i % len(self.themes)
            text = self.themes[theme_index]
            pos_y = self.center_y + (i - base_index) * self.item_height - offset_y - self.box_height // 2
            is_center = abs(pos_y + self.box_height // 2 - self.center_y) < self.item_height // 2
            if self.state >= STATE_FUSE and is_center:
                box_color = (255, 100, 100)
            else:
                box_color = LIGHT_BLUE if is_center else DARK_BLUE
            box_rect = pygame.Rect((SCREEN_WIDTH - self.box_width) // 2, pos_y, self.box_width, self.box_height)
            pygame.draw.rect(self.screen, box_color, box_rect, border_radius=10)
            text_surface = self.font_large.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=box_rect.center)
            self.screen.blit(text_surface, text_rect)
        self.screen.set_clip(None)
        highlight_rect = pygame.Rect(
            (SCREEN_WIDTH - self.box_width) // 2 - 5,
            self.center_y - self.box_height // 2 - 5,
            self.box_width + 10,
            self.box_height + 10
        )
        border_color = YELLOW
        if self.state >= STATE_FUSE:
             if (pygame.time.get_ticks() // 100) % 2 == 0:
                 border_color = RED
        pygame.draw.rect(self.screen, border_color, highlight_rect, 5, border_radius=15)

    def run(self):
        running = True
        fuse_progress = 0.0
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            current_ticks = pygame.time.get_ticks()
            elapsed_total = (current_ticks - self.start_ticks) / 1000.0
            if self.state == STATE_SPINNING:
                self.scroll_pos += self.current_speed
                if elapsed_total > self.spin_duration_target:
                    self.state = STATE_STOPPING
            elif self.state == STATE_STOPPING:
                self.current_speed *= self.friction
                self.scroll_pos += self.current_speed
                if self.current_speed < 1.0:
                    target_pos = round(self.scroll_pos / self.item_height) * self.item_height
                    self.scroll_pos += (target_pos - self.scroll_pos) * 0.2
                    if abs(self.scroll_pos - target_pos) < 0.5:
                        self.scroll_pos = target_pos
                        self.state = STATE_FUSE
                        self.fuse_start_ticks = current_ticks
                        final_index = int(self.scroll_pos / self.item_height) % len(self.themes)
                        self.final_theme = self.themes[final_index]
            elif self.state == STATE_FUSE:
                fuse_elapsed = (current_ticks - self.fuse_start_ticks) / 1000.0
                fuse_progress = fuse_elapsed / self.fuse_duration
                if fuse_progress >= 1.0:
                    fuse_progress = 1.0
                    self.state = STATE_EXPLOSION
                    self.explosion_start_ticks = current_ticks
            self.screen.fill(WHITE)
            msg = "お題を抽選中..."
            if self.state == STATE_FUSE:
                remaining = max(0, 3.0 - (current_ticks - self.fuse_start_ticks)/1000.0)
                msg = f"撮影まであと {remaining:.2f} 秒"
            elif self.state == STATE_EXPLOSION:
                msg = "撮影開始！"
            text_guide = self.font_small.render(msg, True, BLACK)
            self.screen.blit(text_guide, (50, 30))
            self.draw_roulette()
            self.draw_dynamite_fuse(fuse_progress)
            if self.state == STATE_EXPLOSION:
                explosion_elapsed = (current_ticks - self.explosion_start_ticks) / 1000.0
                radius = int(explosion_elapsed * 1000)
                if radius < SCREEN_WIDTH * 1.5:
                    pygame.draw.circle(self.screen, YELLOW, (700 + 15, 80 + 30), radius)
                fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                fade_surface.fill(RED)
                alpha = min(255, int(explosion_elapsed * 2 * 255))
                fade_surface.set_alpha(alpha)
                self.screen.blit(fade_surface, (0, 0))
                if alpha >= 255:
                    running = False
                    return self.final_theme
            pygame.display.flip()
            self.clock.tick(FPS)

# --- ★★★ Phase 4: 対戦画面２ ★★★ ---
class Phase4Scene:
    # player_turn引数を追加 (1: 先攻, 2: 後攻)
    def __init__(self, screen, theme, player_turn=1):
        self.screen = screen
        self.theme = theme
        self.player_turn = player_turn # 現在のプレイヤーを保持
        self.clock = pygame.time.Clock()
        
        try:
            self.font = pygame.font.SysFont("meiryo", 40)
            self.font_small = pygame.font.SysFont("meiryo", 24)
            self.font_turn = pygame.font.SysFont("meiryo", 20, bold=True) # ボックス用フォント
        except:
            self.font = pygame.font.Font(None, 40)
            self.font_small = pygame.font.Font(None, 24)
            self.font_turn = pygame.font.Font(None, 20)

        # カメラ設定 (DirectShow指定で高速化)
        print("カメラを起動しています...")
        self.cap = cv2.VideoCapture(2, cv2.CAP_DSHOW) # 0番内蔵、1番外付けなど環境に合わせて変更
        if not self.cap.isOpened():
            print("エラー: カメラが見つかりません")
            sys.exit()
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, SCREEN_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_HEIGHT)

        # ダミー画面作成
        self.dummy_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.dummy_surface.fill(DUMMY_BG)
        text_theme = self.font.render(f"お題: {self.theme}", True, WHITE)
        text_rect_theme = text_theme.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        self.dummy_surface.blit(text_theme, text_rect_theme)
        text_info = self.font_small.render("ここにカメラ映像が出ます", True, GRAY)
        text_rect_info = text_info.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
        self.dummy_surface.blit(text_info, text_rect_info)
        
        self.wait_duration = 1.0
        self.anim_duration = 2.0
        self.start_ticks = pygame.time.get_ticks()

    def draw_turn_indicators(self):
        """先攻・後攻ボックスを描画する関数"""
        box_width = 80
        box_height = 35
        margin = 10
        start_x = 20
        start_y = 65 # お題の下あたり
        
        # 1. 先攻ボックス (赤)
        p1_surface = pygame.Surface((box_width, box_height))
        p1_surface.fill(RED)
        
        # 文字描画
        p1_text = self.font_turn.render("先攻", True, WHITE)
        p1_rect = p1_text.get_rect(center=(box_width//2, box_height//2))
        p1_surface.blit(p1_text, p1_rect)
        
        # 2. 後攻ボックス (青)
        p2_surface = pygame.Surface((box_width, box_height))
        p2_surface.fill(BLUE)
        
        p2_text = self.font_turn.render("後攻", True, WHITE)
        p2_rect = p2_text.get_rect(center=(box_width//2, box_height//2))
        p2_surface.blit(p2_text, p2_rect)
        
        # 3. 透明度設定 (現在のターンのみ濃く、他は半透明)
        if self.player_turn == 1:
            p1_surface.set_alpha(255) # くっきり
            p2_surface.set_alpha(80)  # 薄く
            # ハイライト枠などをつけても良い
            pygame.draw.rect(p1_surface, WHITE, (0,0,box_width,box_height), 2)
        else:
            p1_surface.set_alpha(80)
            p2_surface.set_alpha(255)
            pygame.draw.rect(p2_surface, WHITE, (0,0,box_width,box_height), 2)
            
        # 4. 画面に貼り付け
        self.screen.blit(p1_surface, (start_x, start_y))
        self.screen.blit(p2_surface, (start_x + box_width + margin, start_y))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # A. カメラ映像
            ret, frame = self.cap.read()
            if ret:
                camera_surface = cvimage_to_pygame(frame)
                camera_surface = pygame.transform.scale(camera_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
                camera_surface = pygame.transform.flip(camera_surface, True, False)
                self.screen.blit(camera_surface, (0, 0))
            
            # B. ダミー画面（フェード）
            current_ticks = pygame.time.get_ticks()
            total_elapsed = (current_ticks - self.start_ticks) / 1000.0

            if total_elapsed < self.wait_duration:
                self.dummy_surface.set_alpha(255)
                self.screen.blit(self.dummy_surface, (0, 0))
            elif total_elapsed < (self.wait_duration + self.anim_duration):
                anim_elapsed = total_elapsed - self.wait_duration
                progress = anim_elapsed / self.anim_duration
                alpha = int(255 * (1.0 - progress))
                self.dummy_surface.set_alpha(alpha)
                scale = 1.0 - (progress * 0.8)
                new_width = int(SCREEN_WIDTH * scale)
                new_height = int(SCREEN_HEIGHT * scale)
                scaled_surface = pygame.transform.scale(self.dummy_surface, (new_width, new_height))
                target_x = -new_width * 0.5 
                target_y = -new_height * 0.5
                current_x = 0 + (target_x - 0) * progress
                current_y = 0 + (target_y - 0) * progress
                self.screen.blit(scaled_surface, (int(current_x), int(current_y)))

            # C. UI描画（お題・ターン表示・タイマー）
            # お題
            theme_display = self.font_small.render(f"お題: {self.theme}", True, WHITE)
            theme_shadow = self.font_small.render(f"お題: {self.theme}", True, BLACK)
            self.screen.blit(theme_shadow, (22, 22))
            self.screen.blit(theme_display, (20, 20))

            # ★ターン表示ボックスの描画
            self.draw_turn_indicators()

            # タイマー
            timer_text = self.font.render("5.00", True, RED)
            self.screen.blit(timer_text, (SCREEN_WIDTH//2 - 50, 50))

            pygame.display.flip()
            self.clock.tick(FPS)
        
        self.cap.release()
        pygame.quit()
        sys.exit()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ポーズ対戦ゲーム - Turn Indicator")

    # Phase 3
    phase3 = Phase3Scene(screen)
    selected_theme = phase3.run()

    # Phase 4 (例として Player 1 のターンとして開始)
    if selected_theme:
        # player_turn=1 で先攻のボックスが光ります
        phase4 = Phase4Scene(screen, selected_theme, player_turn=1)
        phase4.run()

if __name__ == "__main__":
    main()