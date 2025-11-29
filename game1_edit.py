import pygame
import random
import sys
import cv2
import numpy as np
import mediapipe as mp
import os
import re

# --- 設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
FONT_FILE_IOEI = os.path.join(current_dir, "IoEI.ttf")
PAINTBALL_FILE = os.path.join(current_dir, "Paintball_Beta_3.ttf") # ★変数名変更
BOMB_FILE = os.path.join(current_dir, "bakudan.jpg")

# --- 起動時のファイルチェック ---
print("--- ファイル読み込みチェック ---")
if os.path.exists(PAINTBALL_FILE):
    print(f"OK: {PAINTBALL_FILE}")
else:
    print(f"WARNING: {PAINTBALL_FILE} が見つかりません。")

if os.path.exists(FONT_FILE_IOEI):
    print(f"OK: {FONT_FILE_IOEI}")
else:
    print(f"WARNING: {FONT_FILE_IOEI} が見つかりません。")
print("----------------------------")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
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
    # BGR -> RGB, then create pygame surface
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width = image_rgb.shape[:2]
    # .tobytes() を使う（tostring() は非推奨のため修正）
    image_surface = pygame.image.frombuffer(image_rgb.tobytes(), (width, height), 'RGB')
    return image_surface

# ★★★ フォント管理クラス（文字単位合成版） ★★★
class FontManager:
    def __init__(self):
        # フォントキャッシュ（キーは (font_type, size)）
        self.fonts = {}
        # ファイルパス
        self.ioei_path = FONT_FILE_IOEI
        self.paintball_path = PAINTBALL_FILE

    def _load_font_file(self, path, size, fallback_name=None, scale=1.0):
        """指定パスから pygame.font.Font を返す。失敗したら SysFont で代替"""
        key = (path, int(size))
        if key in self.fonts:
            return self.fonts[key]
        
        try:
            font = pygame.font.Font(path, int(size * scale))
        except OSError:
            # 明示的に警告を出す
            print(f"Warning: font file '{path}' not found. Falling back to system font '{fallback_name}'.")
            if fallback_name:
                try:
                    font = pygame.font.SysFont(fallback_name, int(size * scale))
                except Exception:
                    font = pygame.font.Font(None, int(size * scale))
            else:
                font = pygame.font.Font(None, int(size * scale))
        
        self.fonts[key] = font
        return font

    def get_font(self, size, font_type="ioei"):
        """font_type: 'ioei' または 'paintball' を指定"""
        if font_type == "paintball":
            # Paintball は少し大きめに表示したい場合などは scale を調整可能
            return self._load_font_file(self.paintball_path, size, fallback_name="impact", scale=1.0)
        else:
            # iOEI 用（日本語用）
            return self._load_font_file(self.ioei_path, size, fallback_name="meiryo", scale=1.0)

    def is_japanese_char(self, ch):
        """簡易判定：文字がひらがな/カタカナ/漢字の範囲にあるかチェック"""
        code = ord(ch)
        # ひらがな \u3040-\u309f, カタカナ \u30a0-\u30ff, 漢字 \u4e00-\u9fff, 全角記号など
        return (0x3000 <= code <= 0x303f) or (0x3040 <= code <= 0x309f) or (0x30a0 <= code <= 0x30ff) or (0x4e00 <= code <= 0x9fff) or (0xff01 <= code <= 0xff5e)

    def is_ascii_symbol_or_digit(self, ch):
        """半角英数字または記号（基本 ASCII 範囲）なら True"""
        code = ord(ch)
        return 0x20 <= code <= 0x7e  # space(32)～ ~(126) の範囲

    def render(self, text, size, color):
        """
        混在対応レンダリング：
        - 文字ごとに日本語なら IoEI、半角 ASCII なら Paintball を使って順に描画して一枚に合成して返す
        """
        if text == "":
            return pygame.Surface((0,0), pygame.SRCALPHA)

        # まず各フォントオブジェクトを取得
        font_ioei = self.get_font(size, "ioei")
        font_paint = self.get_font(size, "paintball")

        # 文字ごとにサーフェスを作成し、全体のサイズを計算
        total_width = 0
        max_height = 0
        glyphs = []  # (surface, width, height)
        
        for ch in text:
            if self.is_japanese_char(ch):
                font = font_ioei
            elif self.is_ascii_symbol_or_digit(ch):
                font = font_paint
            else:
                # その他（判定漏れなど）は IoEI を優先
                font = font_ioei

            # 1文字描画
            glyph_surf = font.render(ch, True, color)
            w, h = glyph_surf.get_size()
            glyphs.append((glyph_surf, w, h))
            
            total_width += w
            if h > max_height:
                max_height = h

        # 合成用サーフェス（透明背景）を作成
        surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        
        x = 0
        for glyph_surf, w, h in glyphs:
            # 下揃えで描画 (max_height - h)
            # ※フォントによってベースラインがズレる場合、ここを (max_height - h)//2 で中央揃えにする等の調整が可能
            surface.blit(glyph_surf, (x, max_height - h))
            x += w

        return surface

# --- Phase 3: ルーレット画面 ---
class Phase3Scene:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        self.font_mgr = FontManager()

        # 爆弾画像
        try:
            self.bomb_img = pygame.image.load(BOMB_FILE)
            self.bomb_img = pygame.transform.scale(self.bomb_img, (100, 100))
        except OSError:
            print(f"Warning: {BOMB_FILE} not found. Drawing rectangle instead.")
            self.bomb_img = None

        # お題
        self.themes = [
            "グリコ", "かんがえるひと", "シェー", "かめはめは", "ジョジョだち", 
            "ダブルピース", "どげざ", "コマネチ", "いのち", "ごろうまる"
        ]
        
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
        end_x = 680 
        y_pos = 80
        
        if self.bomb_img:
            bomb_x = end_x - 10 
            bomb_y = y_pos - 20 
            self.screen.blit(self.bomb_img, (bomb_x, bomb_y))
        else:
            dynamite_rect = pygame.Rect(end_x, y_pos - 15, 30, 60)
            pygame.draw.rect(self.screen, RED, dynamite_rect)
            pygame.draw.rect(self.screen, BLACK, dynamite_rect, 2)

        # ★ここは「かな」を含むので IoEI で表示されます
        text_label = self.font_mgr.render("さつえい かいし！", 24, RED)
        label_rect = text_label.get_rect(center=(end_x + 50, y_pos + 90)) 
        self.screen.blit(text_label, label_rect)

        # 導線
        current_fuse_x = start_x + (end_x - start_x) * progress
        if current_fuse_x < end_x:
            pygame.draw.line(self.screen, GRAY, (current_fuse_x, y_pos + 3), (end_x + 1, y_pos + 3), 2)
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
            
            # お題テキスト
            text_surface = self.font_mgr.render(text, 60, WHITE)
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
            
            # ★文字合成のテストケース
            msg = "おだいを きめています..."
            if self.state == STATE_FUSE:
                remaining = max(0, 3.0 - (current_ticks - self.fuse_start_ticks)/1000.0)
                # 「さつえい まで」はIoEI、「3.00」はPaintball、「びょう」はIoEIで描画されます！
                msg = f"さつえい まで {remaining:.2f} びょう"
            elif self.state == STATE_EXPLOSION:
                msg = "さつえい かいし！"
            
            text_guide = self.font_mgr.render(msg, 30, BLACK)
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

# --- Phase 4: 対戦画面２ ---
class Phase4Scene:
    def __init__(self, screen, theme, player_turn=1):
        self.screen = screen
        self.theme = theme
        self.player_turn = player_turn
        self.clock = pygame.time.Clock()
        
        self.font_mgr = FontManager()

        print("カメラを起動しています...")
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW) ###############################カメラ番号###################################
        if not self.cap.isOpened():
            print("エラー: カメラが見つかりません")
            sys.exit()
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, SCREEN_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_HEIGHT)

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec_point = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=5, circle_radius=5)
        self.drawing_spec_line = self.mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=3)

        self.dummy_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.dummy_surface.fill(DUMMY_BG)
        
        text_theme = self.font_mgr.render(f"おだい: {self.theme}", 40, WHITE)
        text_rect_theme = text_theme.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        self.dummy_surface.blit(text_theme, text_rect_theme)
        
        text_info = self.font_mgr.render("ここに カメラが うつります", 24, GRAY)
        text_rect_info = text_info.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
        self.dummy_surface.blit(text_info, text_rect_info)
        
        self.wait_duration = 1.0
        self.anim_duration = 2.0
        self.start_ticks = pygame.time.get_ticks()

    def draw_turn_indicators(self):
        box_width = 80
        box_height = 35
        margin = 10
        start_x = 20
        start_y = 65
        
        p1_surf = pygame.Surface((box_width, box_height))
        p1_surf.fill(RED)
        p1_text = self.font_mgr.render("せんこう", 20, WHITE)
        p1_rect = p1_text.get_rect(center=(box_width//2, box_height//2))
        p1_surf.blit(p1_text, p1_rect)
        
        p2_surf = pygame.Surface((box_width, box_height))
        p2_surf.fill(BLUE)
        p2_text = self.font_mgr.render("こうこう", 20, WHITE)
        p2_rect = p2_text.get_rect(center=(box_width//2, box_height//2))
        p2_surf.blit(p2_text, p2_rect)
        
        if self.player_turn == 1:
            p1_surf.set_alpha(255)
            p2_surf.set_alpha(80)
            pygame.draw.rect(p1_surf, WHITE, (0,0,box_width,box_height), 2)
        else:
            p1_surf.set_alpha(80)
            p2_surf.set_alpha(255)
            pygame.draw.rect(p2_surf, WHITE, (0,0,box_width,box_height), 2)
            
        self.screen.blit(p1_surf, (start_x, start_y))
        self.screen.blit(p2_surf, (start_x + box_width + margin, start_y))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            ret, frame = self.cap.read()
            if ret:
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(image_rgb)
                
                if results.pose_landmarks:
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=results.pose_landmarks,
                        connections=self.mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=self.drawing_spec_point,
                        connection_drawing_spec=self.drawing_spec_line
                    )

                camera_surface = cvimage_to_pygame(frame)
                camera_surface = pygame.transform.scale(camera_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
                camera_surface = pygame.transform.flip(camera_surface, True, False)
                self.screen.blit(camera_surface, (0, 0))
            
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

            theme_display = self.font_mgr.render(f"おだい: {self.theme}", 24, WHITE)
            theme_shadow = self.font_mgr.render(f"おだい: {self.theme}", 24, BLACK)
            self.screen.blit(theme_shadow, (22, 22))
            self.screen.blit(theme_display, (20, 20))

            self.draw_turn_indicators()

            # ★タイマー (Paintballで描画されます)
            timer_text = self.font_mgr.render("5.00", 60, RED)
            self.screen.blit(timer_text, (SCREEN_WIDTH//2 - 50, 50))

            pygame.display.flip()
            self.clock.tick(FPS)
        
        self.cap.release()
        pygame.quit()
        sys.exit()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ポーズ対戦ゲーム - Final Version")

    # Phase 3
    phase3 = Phase3Scene(screen)
    selected_theme = phase3.run()

    # Phase 4
    if selected_theme:
        phase4 = Phase4Scene(screen, selected_theme, player_turn=1)
        phase4.run()

if __name__ == "__main__":
    main()