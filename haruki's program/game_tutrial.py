import os
import re
import sys
from abc import ABC, abstractmethod

import numpy as np
import pygame


# ====================================================
# 1. Config: 設定・定数管理
# ====================================================
class Config:
    # 画面設定
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60
    CAPTION = "Pose Battle Game - Complete Ver."

    # パス設定 (絶対パス)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PATH_FONT_IOEI = os.path.join(BASE_DIR, "IoEI.ttf")
    PATH_FONT_PAINTBALL = os.path.join(BASE_DIR, "Paintball_Beta_3.ttf")
    PATH_IMG_BOMB = os.path.join(BASE_DIR, "bakudan-gray.jpg")
    PATH_CHAR_RED = os.path.join(BASE_DIR, "char_red.jpg")
    PATH_CHAR_BLUE = os.path.join(BASE_DIR, "char_blue.jpg")

    # 色定義
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 50, 50)
    BLUE = (50, 50, 255)
    GRAY = (100, 100, 100)
    ORANGE = (255, 165, 0)
    YELLOW = (255, 255, 0)
    DUMMY_BG = (50, 50, 50)
    LIGHT_BLUE = (120, 180, 255)
    DARK_BLUE = (70, 120, 200)
    CREAM = (255, 250, 220)
    FUSE_BROWN = (80, 60, 40)

    # ゲームパラメータ
    ROULETTE_ITEM_HEIGHT = 110
    FUSE_DURATION = 3.0
    COUNTDOWN_SECONDS = 5.0

    # お題リスト
    THEMES = [
        "グリコ",
        "かんがえるひと",
        "シェー",
        "かめはめは",
        "ジョジョだち",
        "ダブルピース",
        "どげざ",
        "コマネチ",
        "いのち",
        "ごろうまる",
    ]

    # ==========================================
    # ★★★ [ Phase 2: 説明画面のレイアウト設定 ] ★★★
    # ==========================================

    # 1. タイトル ("ゲームの遊び方") の位置
    PHASE2_TITLE_Y = 60  # 中心Y座標
    PHASE2_TITLE_BG_HEIGHT = 70  # 背景帯の高さ

    # 2. Wモニターの位置
    PHASE2_MONITOR_Y = 150  # モニターの上端Y座標
    PHASE2_MONITOR_MARGIN = 40  # 2つのモニターの間隔

    # 3. ラベル ("1.お題を決める" 等) の位置
    PHASE2_LABEL_OFFSET_Y = -20

    # 4. 矢印 (→) の位置
    PHASE2_ARROW_OFFSET_Y = 0

    # 5. フッター（白帯）の高さ
    PHASE2_FOOTER_HEIGHT = 120

    # ==========================================
    # [ 説明画面のミニルーレット(左画面内)設定 ]
    # ==========================================
    MINI_BOMB_Y = 40
    MINI_FUSE_OFFSET_Y = -10
    MINI_FUSE_THICKNESS = 1
    MINI_FUSE_START_X = 40
    MINI_FUSE_END_X = 270
    MINI_BOX_WIDTH = 200
    MINI_BOX_HEIGHT = 50
    MINI_ROULETTE_OFFSET_Y = 15


# ====================================================
# 2. Utils
# ====================================================
class Utils:
    @staticmethod
    def cvimage_to_pygame(image):
        import cv2

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image_rgb.shape[:2]
        return pygame.image.frombuffer(image_rgb.tobytes(), (width, height), "RGB")

    @staticmethod
    def ease_out_cubic(x):
        return 1 - pow(1 - x, 3)


# ====================================================
# 3. Managers
# ====================================================
class ResourceManager:
    def __init__(self):
        self.fonts_ioei = {}
        self.fonts_paintball = {}
        self.fonts_system = {}

        self.bomb_img = self._load_image(
            Config.PATH_IMG_BOMB, size=(100, 100), transparent=False
        )
        self.char_red = self._load_image(
            Config.PATH_CHAR_RED, target_height=190, transparent=True
        )
        self.char_blue = self._load_image(
            Config.PATH_CHAR_BLUE, target_height=190, transparent=True
        )

        self._check_files()

    def _check_files(self):
        print("--- Resource Check ---")
        for name, path in [
            ("Paintball", Config.PATH_FONT_PAINTBALL),
            ("IoEI", Config.PATH_FONT_IOEI),
            ("Bomb", Config.PATH_IMG_BOMB),
            ("CharRed", Config.PATH_CHAR_RED),
            ("CharBlue", Config.PATH_CHAR_BLUE),
        ]:
            status = "OK" if os.path.exists(path) else "MISSING"
            print(f"[{status}] {name}: {path}")
        print("----------------------")

    def _load_image(self, path, size=None, target_height=None, transparent=False):
        try:
            if not os.path.exists(path):
                return None
            loaded = pygame.image.load(path)
            # 透過指定: アルファチャンネル付きならそのまま使い、無ければ左上色を抜く
            if transparent and (
                loaded.get_alpha() is not None or loaded.get_masks()[3] != 0
            ):
                img = loaded.convert_alpha()
            else:
                img = loaded.convert()
                if transparent:
                    colorkey = img.get_at((0, 0))
                    img.set_colorkey(colorkey, pygame.RLEACCEL)

            if size:
                img = pygame.transform.scale(img, size)
            elif target_height:
                rect = img.get_rect()
                ratio = target_height / rect.height
                new_width = int(rect.width * ratio)
                img = pygame.transform.scale(img, (new_width, target_height))
            return img
        except:
            return None

    def get_font_object(self, path, size, cache_dict, fallback_sysfont="meiryo"):
        if size in cache_dict:
            return cache_dict[size]
        try:
            font = pygame.font.Font(path, size)
        except:
            if fallback_sysfont == "impact":
                font = pygame.font.Font(None, int(size * 1.5))
            else:
                font = pygame.font.SysFont(fallback_sysfont, size)
        cache_dict[size] = font
        return font

    def get_system_font(self, size, bold=False):
        key = (size, bold)
        if key in self.fonts_system:
            return self.fonts_system[key]
        try:
            font = pygame.font.SysFont("meiryo", size, bold=bold)
        except:
            font = pygame.font.Font(None, size)
            font.set_bold(bold)
        self.fonts_system[key] = font
        return font


class TextRenderer:
    def __init__(self, resource_manager):
        self.rm = resource_manager

    def render(self, text, size, color):
        if text == "":
            return pygame.Surface((0, 0), pygame.SRCALPHA)
        font_ioei = self.rm.get_font_object(
            Config.PATH_FONT_IOEI, size, self.rm.fonts_ioei, "meiryo"
        )
        font_paint = self.rm.get_font_object(
            Config.PATH_FONT_PAINTBALL, size, self.rm.fonts_paintball, "impact"
        )
        glyphs = []
        total_width = 0
        max_height = 0
        for ch in text:
            if re.match(r"^[a-zA-Z0-9\s\.\:\!\-]+$", ch):
                target_font = font_paint
            else:
                target_font = font_ioei
            g_surf = target_font.render(ch, True, color)
            w, h = g_surf.get_size()
            glyphs.append(g_surf)
            total_width += w
            max_height = max(max_height, h)
        surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        x = 0
        for g_surf in glyphs:
            h = g_surf.get_height()
            surface.blit(g_surf, (x, max_height - h))
            x += g_surf.get_width()
        return surface

    def render_system(self, text, size, color, bold=False):
        font = self.rm.get_system_font(size, bold=bold)
        return font.render(text, True, color)


# ====================================================
# 4. Scenes
# ====================================================
class Scene(ABC):
    def __init__(self, app):
        self.app = app
        self.renderer = app.text_renderer
        self.screen = app.screen

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def handle_event(self, event):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def draw(self):
        pass


# ★★★ Phase 2: 説明画面 (火花削除版) ★★★
class Phase2Scene(Scene):
    def __init__(self, app):
        super().__init__(app)

        self.dialogues = [
            {"sp": 0, "text": "ようこそ！ ポーズ対戦ゲームへ！"},
            {"sp": 1, "text": "ここではカメラを使って全身で遊びます。"},
            {"sp": 0, "text": "左の画面を見てくれ。まずはルーレットでお題が決まる！"},
            {"sp": 1, "text": "そして右の画面。そのお題のポーズを真似してください。"},
            {"sp": 0, "text": "カウントダウンがゼロになったら、シャッターだ！"},
            {"sp": 1, "text": "うまくポーズを取れた方が勝ちですよ。"},
            {"sp": 0, "text": "準備はいいか？ スペースキーで開始だ！"},
        ]

        self.index = 0
        self.char_y_offset = 0
        self.jump_speed = 0.0

        # ミニ画面
        self.mini_w, self.mini_h = 320, 240
        self.surf_roulette = pygame.Surface((self.mini_w, self.mini_h))
        self.surf_camera = pygame.Surface((self.mini_w, self.mini_h))

        self.sim_time = 0.0
        self.sim_scroll_y = 0.0
        self.sim_countdown_val = 3.0

        # 状態管理
        self.sim_roulette_state = 0
        self.sim_roulette_timer = 0.0
        self.sim_roulette_speed = 400.0

        self.sim_cam_state = 0
        self.sim_cam_timer = 0.0
        self.sim_shutter_y = 0
        self.sim_arm_angle = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.index += 1
                self.char_y_offset = -15
                if self.index >= len(self.dialogues):
                    self.index = 0

    def update(self, dt):
        if self.char_y_offset < 0:
            self.char_y_offset += 150 * dt
            if self.char_y_offset > 0:
                self.char_y_offset = 0

        self.sim_time += dt

        # 1. ルーレット
        box_h = Config.MINI_BOX_HEIGHT
        if self.sim_roulette_state == 0:
            self.sim_scroll_y += self.sim_roulette_speed * dt
            self.sim_roulette_timer += dt
            if self.sim_roulette_timer > 2.0:
                self.sim_roulette_state = 1

        elif self.sim_roulette_state == 1:
            self.sim_roulette_speed *= 0.92
            self.sim_scroll_y += self.sim_roulette_speed * dt

            if self.sim_roulette_speed < 10.0:
                target = round(self.sim_scroll_y / box_h) * box_h
                diff = target - self.sim_scroll_y
                self.sim_scroll_y += diff * 10 * dt
                if abs(diff) < 1.0:
                    self.sim_scroll_y = target
                    self.sim_roulette_state = 2
                    self.sim_roulette_timer = 0.0

        elif self.sim_roulette_state == 2:
            self.sim_roulette_timer += dt
            if self.sim_roulette_timer > 2.0:
                self.sim_roulette_state = 0
                self.sim_roulette_timer = 0.0
                self.sim_roulette_speed = 400.0

        # 2. カメラ
        if self.sim_cam_state == 0:
            self.sim_countdown_val -= dt
            self.sim_arm_angle = np.sin(self.sim_time * 5) * 30

            if self.sim_countdown_val <= 0:
                self.sim_cam_state = 1
                self.sim_cam_timer = 0.0

        elif self.sim_cam_state == 1:
            self.sim_cam_timer += dt
            progress = min(1.0, self.sim_cam_timer / 0.1)
            self.sim_shutter_y = int((self.mini_h / 2) * progress)
            if progress >= 1.0:
                self.sim_cam_state = 2
                self.sim_cam_timer = 0.0

        elif self.sim_cam_state == 2:
            self.sim_cam_timer += dt
            progress = min(1.0, self.sim_cam_timer / 0.1)
            self.sim_shutter_y = int((self.mini_h / 2) * (1.0 - progress))
            if progress >= 1.0:
                self.sim_cam_state = 3
                self.sim_cam_timer = 0.0

        elif self.sim_cam_state == 3:
            self.sim_cam_timer += dt
            if self.sim_cam_timer > 2.0:
                self.sim_cam_state = 0
                self.sim_countdown_val = 3.0
                self.sim_shutter_y = 0

    def draw(self):
        self.screen.fill(Config.CREAM)

        footer_h = Config.PHASE2_FOOTER_HEIGHT
        footer_y = Config.SCREEN_HEIGHT - footer_h

        # 黄色い背景
        pygame.draw.rect(
            self.screen, (255, 230, 0), (0, 0, Config.SCREEN_WIDTH, footer_y)
        )

        # --- タイトル ---
        title_y = Config.PHASE2_TITLE_Y
        title_bg_h = Config.PHASE2_TITLE_BG_HEIGHT

        pygame.draw.rect(
            self.screen,
            (200, 150, 50),
            (0, title_y - title_bg_h // 2, Config.SCREEN_WIDTH, title_bg_h),
        )
        title = self.renderer.render_system(
            "ゲームの遊び方", 40, Config.WHITE, bold=True
        )
        self.screen.blit(
            title, title.get_rect(center=(Config.SCREEN_WIDTH // 2, title_y))
        )

        # --- Wモニター ---
        monitor_y = Config.PHASE2_MONITOR_Y
        margin_center = Config.PHASE2_MONITOR_MARGIN

        left_x = Config.SCREEN_WIDTH // 2 - self.mini_w - margin_center // 2
        self._draw_simulation_roulette(self.surf_roulette)
        self.screen.blit(self.surf_roulette, (left_x, monitor_y))
        pygame.draw.rect(
            self.screen, (100, 80, 0), (left_x, monitor_y, self.mini_w, self.mini_h), 4
        )

        right_x = Config.SCREEN_WIDTH // 2 + margin_center // 2
        self._draw_simulation_camera(self.surf_camera)
        self.screen.blit(self.surf_camera, (right_x, monitor_y))
        pygame.draw.rect(
            self.screen, (100, 80, 0), (right_x, monitor_y, self.mini_w, self.mini_h), 4
        )

        # --- 矢印 & ラベル ---
        arrow_y = monitor_y + self.mini_h // 2 + Config.PHASE2_ARROW_OFFSET_Y
        arrow = self.renderer.render_system("→", 60, (200, 100, 0), bold=True)
        self.screen.blit(
            arrow, arrow.get_rect(center=(Config.SCREEN_WIDTH // 2, arrow_y))
        )

        label_y = monitor_y + Config.PHASE2_LABEL_OFFSET_Y

        lbl_1 = self.renderer.render_system(
            "1. お題を決める", 24, (100, 80, 0), bold=True
        )
        self.screen.blit(
            lbl_1, lbl_1.get_rect(center=(left_x + self.mini_w // 2, label_y))
        )

        lbl_2 = self.renderer.render_system(
            "2. ポーズをとる", 24, (100, 80, 0), bold=True
        )
        self.screen.blit(
            lbl_2, lbl_2.get_rect(center=(right_x + self.mini_w // 2, label_y))
        )

        # --- フッター & 会話 ---
        pygame.draw.rect(
            self.screen, Config.WHITE, (0, footer_y, Config.SCREEN_WIDTH, footer_h)
        )
        pygame.draw.line(
            self.screen,
            (220, 180, 100),
            (0, footer_y),
            (Config.SCREEN_WIDTH, footer_y),
            3,
        )

        if self.index < len(self.dialogues):
            current_data = self.dialogues[self.index]
            is_red_turn = current_data["sp"] == 0
            name = "アカ" if is_red_turn else "アオ"
            name_color = Config.RED if is_red_turn else Config.BLUE
            name_x = 180 if is_red_turn else Config.SCREEN_WIDTH - 250
            name_surf = self.renderer.render_system(name, 20, name_color, bold=True)
            self.screen.blit(name_surf, (name_x, footer_y + 15))
            text = current_data["text"]
            text_surf = self.renderer.render_system(text, 18, Config.BLACK)
            text_rect = text_surf.get_rect(
                center=(Config.SCREEN_WIDTH // 2, footer_y + 60)
            )
            self.screen.blit(text_surf, text_rect)
            next_guide = self.renderer.render_system("SPACE で 次へ", 16, Config.GRAY)
            self.screen.blit(
                next_guide, (Config.SCREEN_WIDTH - 150, Config.SCREEN_HEIGHT - 25)
            )

            red_img = self.app.resource_manager.char_red
            if red_img:
                r_w, r_h = red_img.get_size()
                char_x = 20
                char_y = Config.SCREEN_HEIGHT - r_h - 10
                if is_red_turn:
                    char_y += int(self.char_y_offset)
                self.screen.blit(red_img, (char_x, char_y))
            blue_img = self.app.resource_manager.char_blue
            if blue_img:
                b_w, b_h = blue_img.get_size()
                char_x = Config.SCREEN_WIDTH - b_w - 20
                char_y = Config.SCREEN_HEIGHT - b_h - 10
                if not is_red_turn:
                    char_y += int(self.char_y_offset)
                self.screen.blit(blue_img, (char_x, char_y))

    def _draw_simulation_roulette(self, surface):
        surface.fill(Config.GRAY)
        w, h = surface.get_size()

        box_h = Config.MINI_BOX_HEIGHT
        box_w = Config.MINI_BOX_WIDTH
        cx = w // 2
        cy = h // 2 + Config.MINI_ROULETTE_OFFSET_Y

        clip_h = box_h * 3
        clip_rect = pygame.Rect(0, cy - clip_h // 2, w, clip_h)
        surface.set_clip(clip_rect)

        offset_y = self.sim_scroll_y % box_h
        base_idx = int(self.sim_scroll_y / box_h)

        for i in range(-2, 3):
            theme_idx = (base_idx + i) % len(Config.THEMES)
            theme_text = Config.THEMES[theme_idx]

            draw_y = cy + (i * box_h) - offset_y
            dist_from_center = abs(draw_y - cy)
            is_center = dist_from_center < 10

            if is_center:
                bg_col = (255, 100, 100)
            else:
                bg_col = Config.LIGHT_BLUE if is_center else Config.DARK_BLUE

            rect = pygame.Rect(cx - box_w // 2, draw_y - box_h // 2, box_w, box_h - 4)
            pygame.draw.rect(surface, bg_col, rect, border_radius=5)

            txt = self.renderer.render(theme_text, 30, Config.WHITE)
            surface.blit(txt, txt.get_rect(center=rect.center))

        surface.set_clip(None)
        hl_rect = pygame.Rect(
            cx - box_w // 2 - 2, cy - box_h // 2 - 2, box_w + 4, box_h + 4
        )
        pygame.draw.rect(surface, Config.YELLOW, hl_rect, 3, border_radius=8)

        # 導火線と爆弾
        bomb_y = Config.MINI_BOMB_Y
        fuse_y = bomb_y + Config.MINI_FUSE_OFFSET_Y

        bomb = self.app.resource_manager.bomb_img
        if bomb:
            bomb_mini = pygame.transform.scale(bomb, (40, 40))
            surface.blit(bomb_mini, (w - 50, bomb_y - 20))
        else:
            pygame.draw.rect(surface, Config.RED, (w - 30, bomb_y - 20, 20, 40))

        start_x = Config.MINI_FUSE_START_X
        end_x = Config.MINI_FUSE_END_X
        pygame.draw.line(
            surface,
            Config.FUSE_BROWN,
            (start_x, fuse_y),
            (end_x, fuse_y),
            Config.MINI_FUSE_THICKNESS,
        )

        # ★削除: 火花アニメーションのコードを削除しました

    def _draw_simulation_camera(self, surface):
        if self.sim_countdown_val <= 0:
            pass

        surface.fill(Config.DUMMY_BG)
        w, h = surface.get_size()
        cx, cy = w // 2, h // 2 + 20

        arm_move = self.sim_arm_angle

        pygame.draw.circle(surface, Config.WHITE, (cx, cy - 60), 15, 2)
        pygame.draw.line(surface, Config.WHITE, (cx, cy - 45), (cx, cy + 20), 2)
        pygame.draw.line(
            surface, Config.WHITE, (cx, cy - 30), (cx - 40, cy - 60 + arm_move), 2
        )
        pygame.draw.line(
            surface, Config.WHITE, (cx, cy - 30), (cx + 40, cy - 60 - arm_move), 2
        )
        pygame.draw.line(surface, Config.WHITE, (cx, cy + 20), (cx - 20, cy + 80), 2)
        pygame.draw.line(surface, Config.WHITE, (cx, cy + 20), (cx + 20, cy + 80), 2)

        theme = self.renderer.render("おだい: グリコ", 16, Config.WHITE)
        surface.blit(theme, (10, 10))

        if self.sim_cam_state == 0:
            disp_num = int(self.sim_countdown_val) + 1
            timer = self.renderer.render(str(disp_num), 100, Config.RED)
            timer.set_alpha(150)
            surface.blit(timer, timer.get_rect(center=(w // 2, h // 2)))

        pygame.draw.rect(surface, Config.RED, (10, 40, 40, 20))
        t_turn = self.renderer.render_system("先行", 12, Config.WHITE)
        surface.blit(t_turn, (15, 42))

        if self.sim_shutter_y > 0:
            pygame.draw.rect(surface, Config.BLACK, (0, 0, w, self.sim_shutter_y))
            pygame.draw.rect(
                surface,
                Config.BLACK,
                (0, h - self.sim_shutter_y, w, self.sim_shutter_y),
            )


# ====================================================
# 4. GameApp: アプリケーション本体
# ====================================================
class GameApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(Config.CAPTION)
        self.clock = pygame.time.Clock()
        self.resource_manager = ResourceManager()
        self.text_renderer = TextRenderer(self.resource_manager)

        self.current_scene = None
        self.change_scene(Phase2Scene(self))
        self.running = True

    def change_scene(self, new_scene):
        if self.current_scene:
            self.current_scene.on_exit()
        self.current_scene = new_scene
        if self.current_scene:
            self.current_scene.on_enter()

    def run(self):
        while self.running:
            dt = self.clock.tick(Config.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.current_scene:
                    self.current_scene.handle_event(event)
            if self.current_scene:
                self.current_scene.update(dt)
                self.current_scene.draw()
            pygame.display.flip()
        if self.current_scene:
            self.current_scene.on_exit()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = GameApp()
    app.run()
