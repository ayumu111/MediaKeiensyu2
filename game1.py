import pygame
import random
import sys

# --- 設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
ORANGE = (255, 165, 0)
GRAY = (100, 100, 100)
DARK_BLUE = (50, 50, 150)
LIGHT_BLUE = (100, 100, 255)
YELLOW = (255, 255, 0)

# 状態定義
STATE_SPINNING = 0
STATE_STOPPING = 1
STATE_FUSE     = 2
STATE_EXPLOSION = 3
STATE_FINISHED = 4

# --- Phase 3: ルーレット画面クラス ---
class Phase3Scene:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        # フォント設定
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

        # ★★★ ランダム要素の追加 ★★★
        # 1. 減速を開始するまでの時間をランダムに決定 (1.5秒 〜 3.0秒)
        self.spin_duration_target = random.uniform(1.5, 3.0)
        
        # 2. 減速時の摩擦係数（ブレーキの強さ）をランダムに決定
        # 0.94(急) 〜 0.97(滑る) くらいの範囲にすると停止位置が大きくばらける
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

            # --- ロジック ---
            if self.state == STATE_SPINNING:
                self.scroll_pos += self.current_speed
                
                # ★ 以前は固定2秒だった判定を、ランダム生成した spin_duration_target に変更
                if elapsed_total > self.spin_duration_target:
                    self.state = STATE_STOPPING
                    print(f"減速開始: 摩擦係数 {self.friction:.4f}")

            elif self.state == STATE_STOPPING:
                # ★ 固定の0.95ではなく、ランダム生成した self.friction を使用
                self.current_speed *= self.friction
                self.scroll_pos += self.current_speed
                
                # 十分遅くなったら吸着処理
                if self.current_speed < 1.0:
                    target_pos = round(self.scroll_pos / self.item_height) * self.item_height
                    self.scroll_pos += (target_pos - self.scroll_pos) * 0.2
                    if abs(self.scroll_pos - target_pos) < 0.5:
                        self.scroll_pos = target_pos
                        self.state = STATE_FUSE
                        self.fuse_start_ticks = current_ticks
                        final_index = int(self.scroll_pos / self.item_height) % len(self.themes)
                        self.final_theme = self.themes[final_index]
                        print(f"決定お題: {self.final_theme}")

            elif self.state == STATE_FUSE:
                fuse_elapsed = (current_ticks - self.fuse_start_ticks) / 1000.0
                fuse_progress = fuse_elapsed / self.fuse_duration
                if fuse_progress >= 1.0:
                    fuse_progress = 1.0
                    self.state = STATE_EXPLOSION
                    self.explosion_start_ticks = current_ticks

            # --- 描画 ---
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

            # --- 爆発＆フェードアウト ---
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

# --- Phase 4: 対戦画面２（ダミー） ---
class Phase4Scene:
    def __init__(self, screen, theme):
        self.screen = screen
        self.theme = theme
        self.font = pygame.font.SysFont("meiryo", 40)
        self.clock = pygame.time.Clock()

    def run(self):
        running = True
        start_ticks = pygame.time.get_ticks()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    running = False
            
            self.screen.fill((50, 50, 50))
            text_theme = self.font.render(f"お題: {self.theme}", True, WHITE)
            self.screen.blit(text_theme, (50, 50))
            text_info = self.font.render("ここにカメラ映像が出ます", True, WHITE)
            self.screen.blit(text_info, (50, 150))
            
            elapsed = (pygame.time.get_ticks() - start_ticks) / 1000.0
            if elapsed < 1.0:
                fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                fade_surface.fill(RED)
                alpha = max(0, 255 - int(elapsed * 255))
                fade_surface.set_alpha(alpha)
                self.screen.blit(fade_surface, (0, 0))

            pygame.display.flip()
            self.clock.tick(FPS)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ポーズ対戦ゲーム - Random Roulette")

    phase3 = Phase3Scene(screen)
    selected_theme = phase3.run()

    if selected_theme:
        phase4 = Phase4Scene(screen, selected_theme)
        phase4.run()

    pygame.quit()

if __name__ == "__main__":
    main()