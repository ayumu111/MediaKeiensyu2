import pygame
import sys
import cv2
import numpy as np
import mediapipe as mp
import os
import re
import random
import time
from abc import ABC, abstractmethod


# ====================================================
# 1. Config: 設定・定数管理 (Magic Numberの排除)
# ====================================================
class Config:
    # 画面設定
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60
    CAPTION = "Pose Battle Game - Refactored"

    # パス設定 (絶対パス)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PATH_FONT_IOEI = os.path.join(BASE_DIR, "IoEI.ttf")
    PATH_FONT_PAINTBALL = os.path.join(BASE_DIR, "Paintball_Beta_3.ttf")
    PATH_IMG_BOMB = os.path.join(BASE_DIR, "bakudan.jpg")

    # 色定義
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 50, 50)
    BLUE = (50, 50, 255)
    GRAY = (100, 100, 100)
    ORANGE = (255, 165, 0)
    YELLOW = (255, 255, 0)
    DUMMY_BG = (50, 50, 50)

    # ★追加: 未定義だった色
    LIGHT_BLUE = (120, 180, 255)
    DARK_BLUE = (70, 120, 200)

    # ゲームパラメータ
    ROULETTE_ITEM_HEIGHT = 110
    ROULETTE_SPIN_MIN = 1.5
    ROULETTE_SPIN_MAX = 3.0
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


# ====================================================
# 2. Utils: 便利関数群 (Easingなど)
# ====================================================
class Utils:
    @staticmethod
    def cvimage_to_pygame(image):
        """OpenCV(BGR)画像をPygame(RGB)画像に変換"""
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image_rgb.shape[:2]
        return pygame.image.frombuffer(image_rgb.tobytes(), (width, height), "RGB")

    @staticmethod
    def ease_out_cubic(x):
        """イージング関数: 急速に始まり、ゆっくり終わる"""
        return 1 - pow(1 - x, 3)


# ====================================================
# 3. Managers: リソース・テキスト・ハードウェア
# ====================================================
class ResourceManager:
    """リソース管理とフォールバック処理"""

    def __init__(self):
        self.fonts_ioei = {}
        self.fonts_paintball = {}
        self.bomb_img = self._load_image(Config.PATH_IMG_BOMB, (100, 100))
        self._check_files()

    def _check_files(self):
        """起動チェック"""
        print("--- Resource Check ---")
        for name, path in [
            ("Paintball", Config.PATH_FONT_PAINTBALL),
            ("IoEI", Config.PATH_FONT_IOEI),
            ("Bomb", Config.PATH_IMG_BOMB),
        ]:
            status = "OK" if os.path.exists(path) else "MISSING"
            print(f"[{status}] {name}: {path}")
        print("----------------------")

    def _load_image(self, path, size=None):
        try:
            img = pygame.image.load(path)
            if size:
                img = pygame.transform.scale(img, size)
            return img
        except OSError:
            print(f"Warning: Failed to load image {path}")
            return None

    def get_font_object(self, path, size, cache_dict, fallback_sysfont="meiryo"):
        """フォント取得（キャッシュ＆フォールバック付き）"""
        if size in cache_dict:
            return cache_dict[size]

        try:
            font = pygame.font.Font(path, size)
        except OSError:
            # フォールバック処理
            print(
                f"Warning: Font {path} not found. Using fallback '{fallback_sysfont}'."
            )
            try:
                font = pygame.font.SysFont(fallback_sysfont, size)
            except:
                font = pygame.font.Font(None, int(size * 1.5))  # 最終手段

        cache_dict[size] = font
        return font


class TextRenderer:
    """文字単位でフォントを切り替えて合成描画するクラス"""

    def __init__(self, resource_manager):
        self.rm = resource_manager

    def is_ascii_symbol_or_digit(self, ch):
        """半角英数字・記号のみか判定"""
        return re.match(r"^[a-zA-Z0-9\s\.\:\!\-]+$", ch) is not None

    def render(self, text, size, color):
        """
        1文字ずつ判定して描画し、1枚のSurfaceに合成して返す
        - 数字・記号 -> Paintball (Impact)
        - その他（日本語） -> IoEI (Meiryo)
        """
        if text == "":
            return pygame.Surface((0, 0), pygame.SRCALPHA)

        # キャッシュからフォント取得
        font_ioei = self.rm.get_font_object(
            Config.PATH_FONT_IOEI, size, self.rm.fonts_ioei, "meiryo"
        )
        # Paintballがない場合は impact を代用
        font_paint = self.rm.get_font_object(
            Config.PATH_FONT_PAINTBALL, size, self.rm.fonts_paintball, "impact"
        )

        glyphs = []
        total_width = 0
        max_height = 0

        # 文字ごとにレンダリング
        for ch in text:
            if self.is_ascii_symbol_or_digit(ch):
                target_font = font_paint
            else:
                target_font = font_ioei

            g_surf = target_font.render(ch, True, color)
            w, h = g_surf.get_size()
            glyphs.append(g_surf)
            total_width += w
            max_height = max(max_height, h)

        # 合成
        surface = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
        x = 0
        for g_surf in glyphs:
            # 下揃えで描画
            h = g_surf.get_height()
            surface.blit(g_surf, (x, max_height - h))
            x += g_surf.get_width()

        return surface


class HardwareManager:
    """カメラとMediaPipeの管理（自動検出＆エラーハンドリング）"""

    def __init__(self):
        self.cap = None
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,  # 0:Lite, 1:Full, 2:Heavy
            enable_segmentation=False,
            min_detection_confidence=0.5,
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.draw_spec = self.mp_drawing.DrawingSpec(
            color=(0, 255, 0), thickness=2, circle_radius=2
        )

    def start_camera(self):
        """使用可能なカメラを0番から順に探す"""
        if self.cap is not None and self.cap.isOpened():
            return True

        print("Searching for camera...")
        # 0番から3番までトライ
        for cam_id in range(4):
            # WindowsならDSHOW推奨
            cap = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
            if cap.isOpened():
                print(f"Camera found at index {cam_id}")
                self.cap = cap
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.SCREEN_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.SCREEN_HEIGHT)
                return True
            cap.release()

        print("Error: No working camera found.")
        return False

    def read_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            return ret, frame
        return False, None

    def process_pose(self, frame):
        """骨格推定（負荷軽減のため毎フレーム呼び出し注意）"""
        if frame is None:
            return None

        # 書き込み不可にして高速化
        frame.flags.writeable = False
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)
        frame.flags.writeable = True

        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=results.pose_landmarks,
                connections=self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.draw_spec,
                connection_drawing_spec=self.draw_spec,
            )
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None


# ====================================================
# 4. Scenes: シーン基底クラスと各フェーズ
# ====================================================
class Scene(ABC):
    def __init__(self, app):
        self.app = app
        self.renderer = app.text_renderer
        self.screen = app.screen

    # ライフサイクルメソッド
    def on_enter(self):
        pass

    def on_exit(self):
        pass

    # イベント処理委譲
    def handle_event(self, event):
        pass

    @abstractmethod
    def update(self, dt):
        pass  # dt: 経過時間(秒)

    @abstractmethod
    def draw(self):
        pass


class Phase3Scene(Scene):
    """お題決定ルーレット"""

    def __init__(self, app):
        super().__init__(app)
        self.state = 0  # 0:Spin, 1:Stop, 2:Fuse, 3:Explosion
        self.scroll_pos = 0.0
        self.current_speed = 2500.0  # px/sec (dt対応のため値を大きく)
        self.elapsed_spin = 0.0

        self.final_theme = ""
        self.spin_duration = random.uniform(
            Config.ROULETTE_SPIN_MIN, Config.ROULETTE_SPIN_MAX
        )

        # 導火線
        self.fuse_timer = 0.0
        self.expl_timer = 0.0

    def update(self, dt):
        if self.state == 0:  # Spinning
            self.scroll_pos += self.current_speed * dt
            self.elapsed_spin += dt
            if self.elapsed_spin > self.spin_duration:
                self.state = 1

        elif self.state == 1:  # Stopping
            # 減速処理
            self.current_speed *= 0.95
            self.scroll_pos += self.current_speed * dt

            if self.current_speed < 50.0:
                # 吸着計算 (中央に来るように)
                h = Config.ROULETTE_ITEM_HEIGHT
                # 現在位置から一番近い「アイテム中央」の位置を計算
                target_pos = round(self.scroll_pos / h) * h

                # 線形補間で近づける
                diff = target_pos - self.scroll_pos
                self.scroll_pos += diff * 10 * dt  # 10は吸着スピード

                if abs(diff) < 1.0:
                    self.scroll_pos = target_pos
                    self.state = 2
                    # お題確定
                    center_idx = int(self.scroll_pos / h)
                    self.final_theme = Config.THEMES[center_idx % len(Config.THEMES)]

        elif self.state == 2:  # Fuse
            self.fuse_timer += dt
            if self.fuse_timer >= Config.FUSE_DURATION:
                self.state = 3

        elif self.state == 3:  # Explosion
            self.expl_timer += dt
            if self.expl_timer > 0.5:
                self.app.change_scene(Phase4Scene(self.app, self.final_theme))

    def draw(self):
        self.screen.fill(Config.WHITE)

        # ガイドテキスト
        msg = "おだいを きめています..."
        if self.state == 2:
            rem = max(0, Config.FUSE_DURATION - self.fuse_timer)
            msg = f"さつえい まで {rem:.2f} びょう"
        elif self.state == 3:
            msg = "さつえい かいし！"

        t_surf = self.renderer.render(msg, 30, Config.BLACK)
        self.screen.blit(t_surf, (50, 30))

        self._draw_roulette()
        self._draw_fuse()

        if self.state == 3:
            self._draw_explosion()

    def _draw_roulette(self):
        h = Config.ROULETTE_ITEM_HEIGHT
        box_w, box_h = 400, 100
        center_y = Config.SCREEN_HEIGHT // 2 + 50

        # 基準インデックス計算
        base_idx = int(self.scroll_pos / h)
        offset_y = self.scroll_pos % h

        # 背景クリップ設定
        bg_rect = pygame.Rect(
            (Config.SCREEN_WIDTH - box_w) // 2 - 20,
            center_y - (h * 1.5) - 20,
            box_w + 40,
            h * 3 + 40,
        )
        pygame.draw.rect(self.screen, Config.GRAY, bg_rect)
        self.screen.set_clip(bg_rect)

        # ループ描画
        for i in range(base_idx - 2, base_idx + 3):
            text = Config.THEMES[i % len(Config.THEMES)]
            # 描画位置Y
            pos_y = center_y + (i - base_idx) * h - offset_y - box_h // 2

            # 中央判定
            is_center = abs(pos_y + box_h // 2 - center_y) < h // 2

            # 色決定
            if self.state >= 2 and is_center:
                color = (255, 100, 100)
            else:
                color = Config.LIGHT_BLUE if is_center else Config.DARK_BLUE

            # 描画
            r = pygame.Rect((Config.SCREEN_WIDTH - box_w) // 2, pos_y, box_w, box_h)
            pygame.draw.rect(self.screen, color, r, border_radius=10)

            ts = self.renderer.render(text, 60, Config.WHITE)
            tr = ts.get_rect(center=r.center)
            self.screen.blit(ts, tr)

        self.screen.set_clip(None)

        # ハイライト枠
        hl_rect = pygame.Rect(
            (Config.SCREEN_WIDTH - box_w) // 2 - 5,
            center_y - box_h // 2 - 5,
            box_w + 10,
            box_h + 10,
        )
        border_col = (
            Config.RED
            if (self.state >= 2 and int(pygame.time.get_ticks() / 100) % 2 == 0)
            else Config.YELLOW
        )
        pygame.draw.rect(self.screen, border_col, hl_rect, 5, border_radius=15)

    def _draw_fuse(self):
        progress = (
            min(1.0, self.fuse_timer / Config.FUSE_DURATION)
            if self.state == 2
            else (1.0 if self.state == 3 else 0.0)
        )

        sx, ex, y = 100, 680, 80

        # 爆弾描画 (固定)
        bomb = self.app.resource_manager.bomb_img
        if bomb:
            self.screen.blit(bomb, (ex - 10, y - 20))
        else:
            pygame.draw.rect(self.screen, Config.RED, (ex, y - 15, 30, 60))

        # ラベル
        lbl = self.renderer.render("さつえい かいし！", 24, Config.RED)
        self.screen.blit(lbl, lbl.get_rect(center=(ex + 50, y + 90)))

        # 導線アニメーション
        curr_x = sx + (ex - sx) * progress
        if curr_x < ex:
            pygame.draw.line(
                self.screen, Config.GRAY, (curr_x, y + 3), (ex + 1, y + 3), 2
            )
            if 0.0 < progress < 1.0:
                size = random.randint(8, 16)
                pygame.draw.circle(self.screen, Config.ORANGE, (int(curr_x), y), size)
                pygame.draw.circle(
                    self.screen, Config.YELLOW, (int(curr_x), y), size // 2
                )

    def _draw_explosion(self):
        radius = int(self.expl_timer * 1500)  # 速度調整
        if radius < Config.SCREEN_WIDTH * 1.5:
            pygame.draw.circle(self.screen, Config.YELLOW, (700, 80), radius)

        fade = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        fade.fill(Config.RED)
        fade.set_alpha(min(255, int(self.expl_timer * 2 * 255)))
        self.screen.blit(fade, (0, 0))


class Phase4Scene(Scene):
    """カメラ・骨格推定・撮影画面（超巨大カウントダウン版）"""
    def __init__(self, app, theme, player_turn=1):
        super().__init__(app)
        self.theme = theme
        self.player_turn = player_turn
        
        # カメラ起動要求
        self.app.hardware.start_camera()
        
        # アニメーション制御
        self.anim_timer = 0.0
        self.wait_duration = 1.0
        self.anim_duration = 2.0
        
        # カウントダウン設定
        self.is_counting = False
        self.countdown_timer = Config.COUNTDOWN_SECONDS
        
        # ★時間の進むスピード係数 (0.7倍速 = 1カウント約1.4秒)
        # 1.0より小さくするとゆっくりになり、溜めが生まれます
        self.time_speed = 0.7 
        
        # ダミー画面の作成
        self.dummy_surf = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        self.dummy_surf.fill(Config.DUMMY_BG)
        
        t_theme = self.renderer.render(f"おだい: {self.theme}", 40, Config.WHITE)
        self.dummy_surf.blit(t_theme, t_theme.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2 - 30)))
        
        t_info = self.renderer.render("ここに カメラが うつります", 24, Config.GRAY)
        self.dummy_surf.blit(t_info, t_info.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2 + 30)))

    def on_enter(self):
        if not self.app.hardware.start_camera():
            print("Failed to start camera.")

    def on_exit(self):
        pass

    def update(self, dt):
        # 1. 蓋アニメーション
        if self.anim_timer < (self.wait_duration + self.anim_duration):
            self.anim_timer += dt
        else:
            # 2. カウントダウン
            if not self.is_counting:
                self.is_counting = True
            
            if self.countdown_timer > 0:
                # ★修正: 時間の進みを遅くして重厚感を出す
                self.countdown_timer -= dt * self.time_speed
                
                if self.countdown_timer <= 0: 
                    self.countdown_timer = 0
                    print("SHUTTER!")
                    # TODO: 撮影処理

    def draw(self):
        # 1. カメラ映像
        ret, frame = self.app.hardware.read_frame()
        if ret:
            frame = self.app.hardware.process_pose(frame)
            cam_surf = Utils.cvimage_to_pygame(frame)
            cam_surf = pygame.transform.scale(cam_surf, (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
            cam_surf = pygame.transform.flip(cam_surf, True, False)
            self.screen.blit(cam_surf, (0, 0))

        # 2. アニメーション（蓋）
        if self.anim_timer < (self.wait_duration + self.anim_duration):
            if self.anim_timer < self.wait_duration:
                self.screen.blit(self.dummy_surf, (0, 0))
            else:
                progress = (self.anim_timer - self.wait_duration) / self.anim_duration
                eased = Utils.ease_out_cubic(progress)
                
                self.dummy_surf.set_alpha(int(255 * (1.0 - eased)))
                scale = 1.0 - (eased * 0.8)
                
                nw = int(Config.SCREEN_WIDTH * scale)
                nh = int(Config.SCREEN_HEIGHT * scale)
                scaled = pygame.transform.scale(self.dummy_surf, (nw, nh))
                
                tx = -nw * 0.5 * eased
                ty = -nh * 0.5 * eased
                self.screen.blit(scaled, (int(tx), int(ty)))

        # 3. UI
        self._draw_ui()

    def _draw_ui(self):
        # お題
        t_theme = self.renderer.render(f"おだい: {self.theme}", 24, Config.WHITE)
        t_shadow = self.renderer.render(f"おだい: {self.theme}", 24, Config.BLACK)
        self.screen.blit(t_shadow, (22, 22))
        self.screen.blit(t_theme, (20, 20))
        
        # ターン表示
        self._draw_turn()
        
        # ★修正: カウントダウン演出 (超巨大・ゆっくり)
        if self.is_counting and self.countdown_timer > 0:
            display_num = int(self.countdown_timer) + 1
            
            # 進行度 (1.0 -> 0.0)
            progress = self.countdown_timer - int(self.countdown_timer)
            
            # --- 演出計算 ---
            # 透明度: ゆっくり消える
            alpha = int(255 * (progress ** 0.5))
            
            # 拡大率: 1.0倍 -> 1.8倍まで迫ってくる
            scale = 1.0 + (1.0 - progress) * 0.8
            
            # ★サイズ変更: 画面いっぱい (500px)
            base_size = 500
            
            # 数字を描画 (Paintballフォント)
            t_timer = self.renderer.render(str(display_num), base_size, Config.RED)
            
            # 拡大縮小
            new_w = int(t_timer.get_width() * scale)
            new_h = int(t_timer.get_height() * scale)
            
            # 処理落ち防止のため、あまりに巨大すぎる場合は制限をかける
            if new_w < Config.SCREEN_WIDTH * 3:
                t_timer_scaled = pygame.transform.smoothscale(t_timer, (new_w, new_h))
                t_timer_scaled.set_alpha(alpha)
                
                # 画面中央に配置
                cx = (Config.SCREEN_WIDTH - new_w) // 2
                cy = (Config.SCREEN_HEIGHT - new_h) // 2
                self.screen.blit(t_timer_scaled, (cx, cy))

    def _draw_turn(self):
        bx, by = 20, 65
        bw, bh = 80, 35
        
        p1 = pygame.Surface((bw, bh))
        p1.fill(Config.RED)
        t1 = self.renderer.render("せんこう", 20, Config.WHITE)
        p1.blit(t1, t1.get_rect(center=(bw//2, bh//2)))
        
        p2 = pygame.Surface((bw, bh))
        p2.fill(Config.BLUE)
        t2 = self.renderer.render("こうこう", 20, Config.WHITE)
        p2.blit(t2, t2.get_rect(center=(bw//2, bh//2)))
        
        if self.player_turn == 1:
            p1.set_alpha(255)
            p2.set_alpha(80)
            pygame.draw.rect(p1, Config.WHITE, (0,0,bw,bh), 2)
        else:
            p1.set_alpha(80)
            p2.set_alpha(255)
            pygame.draw.rect(p2, Config.WHITE, (0,0,bw,bh), 2)
            
        self.screen.blit(p1, (bx, by))
        self.screen.blit(p2, (bx + bw + 10, by))



# ====================================================
# 5. GameApp: アプリケーション本体 (監督)
# ====================================================
class GameApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(Config.CAPTION)
        self.clock = pygame.time.Clock()

        # 各マネージャー初期化
        self.resource_manager = ResourceManager()
        self.text_renderer = TextRenderer(self.resource_manager)
        self.hardware = HardwareManager()

        # 初期シーン
        self.current_scene = None
        self.change_scene(Phase3Scene(self))

        self.running = True

    def change_scene(self, new_scene):
        if self.current_scene:
            self.current_scene.on_exit()
        self.current_scene = new_scene
        if self.current_scene:
            self.current_scene.on_enter()

    def run(self):
        while self.running:
            # デルタタイム計算 (秒単位)
            dt = self.clock.tick(Config.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                # シーンごとのイベント処理があれば呼ぶ
                if self.current_scene:
                    self.current_scene.handle_event(event)

            if self.current_scene:
                self.current_scene.update(dt)
                self.current_scene.draw()

            pygame.display.flip()

        # 終了処理
        if self.current_scene:
            self.current_scene.on_exit()
        self.hardware.release()
        pygame.quit()
        sys.exit()


# ====================================================
# エントリーポイント
# ====================================================
if __name__ == "__main__":
    app = GameApp()
    app.run()
