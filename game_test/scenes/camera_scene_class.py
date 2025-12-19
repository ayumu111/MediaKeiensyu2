import os
from datetime import datetime

import pygame

from core.scene import Scene
from core.manager import Config, Utils  # ←実態に合わせて修正


class CameraScene(Scene):
    """
    カメラ・骨格推定・撮影（元: game1.py の Phase4Scene）
    前段の RouletteScene が app.shared["theme"] に入れている前提。
    """
    SCENE_NAME = "camera"

    def __init__(self, app):
        super().__init__(app)
        self.theme = ""
        self.latest_frame = None
        self.camera_ready = False

        self.anim_timer = 0.0
        self.wait_duration = 1.0
        self.anim_duration = 2.0

        self.is_counting = False
        self.countdown_timer = Config.COUNTDOWN_SECONDS
        self.time_speed = 0.7

        self.dummy_surf = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        self.dummy_surf.fill(Config.DUMMY_BG)

        self._next_scene = None

    def on_enter(self):
        # theme 受け取り
        if hasattr(self.app, "shared") and "theme" in self.app.shared:
            self.theme = self.app.shared["theme"]
        else:
            self.theme = "（未設定）"

        # dummyに theme を焼く
        self.dummy_surf.fill(Config.DUMMY_BG)
        t_theme = self.app.text_renderer.render(f"おだい: {self.theme}", 40, Config.WHITE)
        self.dummy_surf.blit(
            t_theme,
            t_theme.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 - 30)),
        )
        t_info = self.app.text_renderer.render("ここに カメラが うつります", 24, Config.GRAY)
        self.dummy_surf.blit(
            t_info,
            t_info.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 + 30)),
        )

        # camera start（HardwareManagerが app.hardware としてある前提）
        self.camera_ready = self.app.hardware.start_camera()
        if not self.camera_ready:
            print("Failed to start camera.")

    def request_next(self):
        return self._next_scene

    def update(self, dt):
        if not self.camera_ready:
            return

        if self.anim_timer < (self.wait_duration + self.anim_duration):
            self.anim_timer += dt
            return

        if not self.is_counting:
            self.is_counting = True

        if self.countdown_timer > 0:
            self.countdown_timer -= dt * self.time_speed
            if self.countdown_timer <= 0:
                self.countdown_timer = 0
                self._capture_shutter()
                # 撮影後の遷移（次が未確定なら仮名で）
                self._next_scene = "ex_result"  # ←本番の次シーン名が決まったら差し替え

    def draw(self):
        if self.camera_ready:
            ret, frame = self.app.hardware.read_frame()
        else:
            ret, frame = False, None

        if ret and frame is not None:
            frame = self.app.hardware.process_pose(frame)
            cv2 = self.app.hardware.cv2
            flipped = cv2.flip(frame, 1) if cv2 else frame
            self.latest_frame = flipped.copy()
            cam_surf = Utils.cvimage_to_pygame(flipped)
            cam_surf = pygame.transform.scale(cam_surf, (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
            self.screen.blit(cam_surf, (0, 0))
        else:
            self.screen.blit(self.dummy_surf, (0, 0))

        # 蓋アニメーション
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

        self._draw_ui()

    def _draw_ui(self):
        t_theme = self.app.text_renderer.render(f"おだい: {self.theme}", 24, Config.WHITE)
        t_shadow = self.app.text_renderer.render(f"おだい: {self.theme}", 24, Config.BLACK)
        self.screen.blit(t_shadow, (22, 22))
        self.screen.blit(t_theme, (20, 20))

        if not self.camera_ready:
            msg = self.app.text_renderer.render("カメラが見つかりません。接続を確認してください。", 24, Config.RED)
            shadow = self.app.text_renderer.render("カメラが見つかりません。接続を確認してください。", 24, Config.BLACK)
            self.screen.blit(shadow, (22, Config.SCREEN_HEIGHT - 62))
            self.screen.blit(msg, (20, Config.SCREEN_HEIGHT - 64))

        if self.is_counting and self.countdown_timer > 0:
            display_num = int(self.countdown_timer) + 1
            progress = self.countdown_timer - int(self.countdown_timer)
            alpha = int(255 * (progress**0.5))
            scale = 1.0 + (1.0 - progress) * 0.8
            base_size = 500

            t_timer = self.app.text_renderer.render(str(display_num), base_size, Config.RED)
            new_w = int(t_timer.get_width() * scale)
            new_h = int(t_timer.get_height() * scale)

            if new_w < Config.SCREEN_WIDTH * 3:
                t_timer_scaled = pygame.transform.smoothscale(t_timer, (new_w, new_h))
                t_timer_scaled.set_alpha(alpha)
                cx = (Config.SCREEN_WIDTH - new_w) // 2
                cy = (Config.SCREEN_HEIGHT - new_h) // 2
                self.screen.blit(t_timer_scaled, (cx, cy))

    def _capture_shutter(self):
        if not self.camera_ready or self.latest_frame is None:
            return
        cv2 = self.app.hardware.cv2
        if not cv2:
            return

        os.makedirs(Config.PATH_SHUTTER_DIR, exist_ok=True)
        filename = datetime.now().strftime("shutter_%Y%m%d_%H%M%S_%f.jpg")
        save_path = os.path.join(Config.PATH_SHUTTER_DIR, filename)
        cv2.imwrite(save_path, self.latest_frame)
