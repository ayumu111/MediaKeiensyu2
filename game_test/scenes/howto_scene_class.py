# scenes/howto_scene_class.py
import numpy as np
import pygame
from core.scene import Scene

from common import Config


class HowToScene(Scene):
    """Phase2: 説明画面（チュートリアル版を移植）"""

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
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.index += 1
            self.char_y_offset = -15

            # 最後まで進んだら次のシーンへ
            if self.index >= len(self.dialogues):
                # core側のScene実装に合わせて、次シーン要求の出し方を変えてください。
                # よくある実装: self.request_next("roulette") / self.next_scene = "roulette"
                if hasattr(self, "request_next"):
                    self.request_next("roulette")
                else:
                    self.next_scene = "roulette"
                self.index = len(self.dialogues) - 1  # 画面崩れ防止

    def update(self, dt):
        # ちょいジャンプ演出
        if self.char_y_offset < 0:
            self.char_y_offset += 150 * dt
            if self.char_y_offset > 0:
                self.char_y_offset = 0

        self.sim_time += dt

        # 1) ミニルーレット
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

        # 2) ミニカメラ
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
        pygame.draw.rect(self.screen, (255, 230, 0), (0, 0, Config.SCREEN_WIDTH, footer_y))

        # タイトル
        title_y = Config.PHASE2_TITLE_Y
        title_bg_h = Config.PHASE2_TITLE_BG_HEIGHT
        pygame.draw.rect(
            self.screen,
            (200, 150, 50),
            (0, title_y - title_bg_h // 2, Config.SCREEN_WIDTH, title_bg_h),
        )
        title = self.renderer.render_system("ゲームの遊び方", 40, Config.WHITE, bold=True)
        self.screen.blit(title, title.get_rect(center=(Config.SCREEN_WIDTH // 2, title_y)))

        # Wモニター
        monitor_y = Config.PHASE2_MONITOR_Y
        margin_center = Config.PHASE2_MONITOR_MARGIN

        left_x = Config.SCREEN_WIDTH // 2 - self.mini_w - margin_center // 2
        self._draw_simulation_roulette(self.surf_roulette)
        self.screen.blit(self.surf_roulette, (left_x, monitor_y))
        pygame.draw.rect(self.screen, (100, 80, 0), (left_x, monitor_y, self.mini_w, self.mini_h), 4)

        right_x = Config.SCREEN_WIDTH // 2 + margin_center // 2
        self._draw_simulation_camera(self.surf_camera)
        self.screen.blit(self.surf_camera, (right_x, monitor_y))
        pygame.draw.rect(self.screen, (100, 80, 0), (right_x, monitor_y, self.mini_w, self.mini_h), 4)

        # 矢印 & ラベル
        arrow_y = monitor_y + self.mini_h // 2 + Config.PHASE2_ARROW_OFFSET_Y
        arrow = self.renderer.render_system("→", 60, (200, 100, 0), bold=True)
        self.screen.blit(arrow, arrow.get_rect(center=(Config.SCREEN_WIDTH // 2, arrow_y)))

        label_y = monitor_y + Config.PHASE2_LABEL_OFFSET_Y
        lbl_1 = self.renderer.render_system("1. お題を決める", 24, (100, 80, 0), bold=True)
        self.screen.blit(lbl_1, lbl_1.get_rect(center=(left_x + self.mini_w // 2, label_y)))
        lbl_2 = self.renderer.render_system("2. ポーズをとる", 24, (100, 80, 0), bold=True)
        self.screen.blit(lbl_2, lbl_2.get_rect(center=(right_x + self.mini_w // 2, label_y)))

        # フッター
        pygame.draw.rect(self.screen, Config.WHITE, (0, footer_y, Config.SCREEN_WIDTH, footer_h))
        pygame.draw.line(self.screen, (220, 180, 100), (0, footer_y), (Config.SCREEN_WIDTH, footer_y), 3)

        # 会話
        current_data = self.dialogues[self.index]
        is_red_turn = current_data["sp"] == 0
        name = "アカ" if is_red_turn else "アオ"
        name_color = Config.RED if is_red_turn else Config.BLUE
        name_x = 180 if is_red_turn else Config.SCREEN_WIDTH - 250
        name_surf = self.renderer.render_system(name, 20, name_color, bold=True)
        self.screen.blit(name_surf, (name_x, footer_y + 15))

        text = current_data["text"]
        text_surf = self.renderer.render_system(text, 18, Config.BLACK)
        text_rect = text_surf.get_rect(center=(Config.SCREEN_WIDTH // 2, footer_y + 60))
        self.screen.blit(text_surf, text_rect)

        next_guide = self.renderer.render_system("SPACE で 次へ", 16, Config.GRAY)
        self.screen.blit(next_guide, (Config.SCREEN_WIDTH - 150, Config.SCREEN_HEIGHT - 25))

        # キャラ
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

            bg_col = (255, 100, 100) if is_center else Config.DARK_BLUE
            rect = pygame.Rect(cx - box_w // 2, draw_y - box_h // 2, box_w, box_h - 4)
            pygame.draw.rect(surface, bg_col, rect, border_radius=5)

            txt = self.renderer.render(theme_text, 30, Config.WHITE)
            surface.blit(txt, txt.get_rect(center=rect.center))

        surface.set_clip(None)

        hl_rect = pygame.Rect(cx - box_w // 2 - 2, cy - box_h // 2 - 2, box_w + 4, box_h + 4)
        pygame.draw.rect(surface, Config.YELLOW, hl_rect, 3, border_radius=8)

        # 導火線と爆弾
        bomb_y = Config.MINI_BOMB_Y
        fuse_y = bomb_y + Config.MINI_FUSE_OFFSET_Y

        bomb = self.app.resource_manager.bomb_img_gray or self.app.resource_manager.bomb_img
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

    def _draw_simulation_camera(self, surface):
        surface.fill(Config.DUMMY_BG)
        w, h = surface.get_size()
        cx, cy = w // 2, h // 2 + 20

        arm_move = self.sim_arm_angle

        pygame.draw.circle(surface, Config.WHITE, (cx, cy - 60), 15, 2)
        pygame.draw.line(surface, Config.WHITE, (cx, cy - 45), (cx, cy + 20), 2)
        pygame.draw.line(surface, Config.WHITE, (cx, cy - 30), (cx - 40, cy - 60 + arm_move), 2)
        pygame.draw.line(surface, Config.WHITE, (cx, cy - 30), (cx + 40, cy - 60 - arm_move), 2)
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
            pygame.draw.rect(surface, Config.BLACK, (0, h - self.sim_shutter_y, w, self.sim_shutter_y))
