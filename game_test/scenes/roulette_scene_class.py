import random
import pygame

from core.scene import Scene
from core.manager import Config  # ←実態に合わせて修正


class RouletteScene(Scene):
    """
    お題決定ルーレット（元: game1.py の Phase3Scene）
    次シーン: "camera" へ theme を渡す必要があるため、app 側に共有領域を置く想定。
    例: app.shared["theme"] = final_theme
    """
    SCENE_NAME = "roulette"

    def __init__(self, app):
        super().__init__(app)
        self.state = 0  # 0:Spin, 1:Stop, 2:Fuse, 3:Explosion
        self.scroll_pos = 0.0
        self.current_speed = 2500.0
        self.elapsed_spin = 0.0

        self.final_theme = ""
        self.spin_duration = random.uniform(Config.ROULETTE_SPIN_MIN, Config.ROULETTE_SPIN_MAX)

        self.fuse_timer = 0.0
        self.expl_timer = 0.0

        self._next_scene = None

    def request_next(self):
        return self._next_scene

    def update(self, dt):
        if self.state == 0:
            self.scroll_pos += self.current_speed * dt
            self.elapsed_spin += dt
            if self.elapsed_spin > self.spin_duration:
                self.state = 1

        elif self.state == 1:
            self.current_speed *= 0.95
            self.scroll_pos += self.current_speed * dt

            if self.current_speed < 50.0:
                h = Config.ROULETTE_ITEM_HEIGHT
                target_pos = round(self.scroll_pos / h) * h
                diff = target_pos - self.scroll_pos
                self.scroll_pos += diff * 10 * dt

                if abs(diff) < 1.0:
                    self.scroll_pos = target_pos
                    self.state = 2
                    center_idx = int(self.scroll_pos / h)
                    self.final_theme = Config.THEMES[center_idx % len(Config.THEMES)]
                    # 次へ渡す（app 側に shared dict がある想定）
                    if not hasattr(self.app, "shared"):
                        self.app.shared = {}
                    self.app.shared["theme"] = self.final_theme

        elif self.state == 2:
            self.fuse_timer += dt
            if self.fuse_timer >= Config.FUSE_DURATION:
                self.state = 3

        elif self.state == 3:
            self.expl_timer += dt
            if self.expl_timer > 0.5:
                self._next_scene = "camera"

    def draw(self):
        self.screen.fill(Config.WHITE)

        msg = "おだいを きめています..."
        if self.state == 2:
            rem = max(0, Config.FUSE_DURATION - self.fuse_timer)
            msg = f"さつえい まで {rem:.2f} びょう"
        elif self.state == 3:
            msg = "さつえい かいし！"

        t_surf = self.app.text_renderer.render(msg, 30, Config.BLACK)
        self.screen.blit(t_surf, (50, 30))

        self._draw_roulette()
        self._draw_fuse()
        if self.state == 3:
            self._draw_explosion()

    def _draw_roulette(self):
        h = Config.ROULETTE_ITEM_HEIGHT
        box_w, box_h = 400, 100
        center_y = Config.SCREEN_HEIGHT // 2 + 50

        base_idx = int(self.scroll_pos / h)
        offset_y = self.scroll_pos % h

        bg_rect = pygame.Rect(
            (Config.SCREEN_WIDTH - box_w) // 2 - 20,
            center_y - (h * 1.5) - 20,
            box_w + 40,
            h * 3 + 40,
        )
        pygame.draw.rect(self.screen, Config.GRAY, bg_rect)
        self.screen.set_clip(bg_rect)

        for i in range(base_idx - 2, base_idx + 3):
            text = Config.THEMES[i % len(Config.THEMES)]
            pos_y = center_y + (i - base_idx) * h - offset_y - box_h // 2
            is_center = abs(pos_y + box_h // 2 - center_y) < h // 2

            if self.state >= 2 and is_center:
                color = (255, 100, 100)
            else:
                color = Config.LIGHT_BLUE if is_center else Config.DARK_BLUE

            r = pygame.Rect((Config.SCREEN_WIDTH - box_w) // 2, pos_y, box_w, box_h)
            pygame.draw.rect(self.screen, color, r, border_radius=10)

            ts = self.app.text_renderer.render(text, 60, Config.WHITE)
            self.screen.blit(ts, ts.get_rect(center=r.center))

        self.screen.set_clip(None)

    def _draw_fuse(self):
        progress = (
            min(1.0, self.fuse_timer / Config.FUSE_DURATION)
            if self.state == 2
            else (1.0 if self.state == 3 else 0.0)
        )

        sx, ex, y = 100, 680, 80

        bomb = getattr(self.app.resource_manager, "bomb_img", None)
        if bomb:
            self.screen.blit(bomb, (ex - 10, y - 20))
        else:
            pygame.draw.rect(self.screen, Config.RED, (ex, y - 15, 30, 60))

        curr_x = sx + (ex - sx) * progress
        if curr_x < ex:
            pygame.draw.line(self.screen, Config.GRAY, (curr_x, y + 3), (ex + 1, y + 3), 2)
            if 0.0 < progress < 1.0:
                size = random.randint(8, 16)
                pygame.draw.circle(self.screen, Config.ORANGE, (int(curr_x), y), size)
                pygame.draw.circle(self.screen, Config.YELLOW, (int(curr_x), y), size // 2)

    def _draw_explosion(self):
        radius = int(self.expl_timer * 1500)
        if radius < Config.SCREEN_WIDTH * 1.5:
            pygame.draw.circle(self.screen, Config.YELLOW, (700, 80), radius)

        fade = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        fade.fill(Config.RED)
        fade.set_alpha(min(255, int(self.expl_timer * 2 * 255)))
        self.screen.blit(fade, (0, 0))
