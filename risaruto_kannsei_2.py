import pygame
import sys
import math
import time
import os


class ResultAnimation:
    def __init__(self, first_player_win=True):

        #====================================
        # 1P 勝利 or 2P 勝利
        #====================================
        self.FIRST_PLAYER_WIN = first_player_win

        pygame.init()
        self.SCREEN_SIZE = (800, 600)
        self.screen = pygame.display.set_mode(self.SCREEN_SIZE)
        self.clock = pygame.time.Clock()

        self.WIDTH, self.HEIGHT = self.screen.get_size()
        self.CENTER = (self.WIDTH // 2, self.HEIGHT // 2)

        # 勝敗による設定
        if self.FIRST_PLAYER_WIN:
            self.BACKGROUND_COLOR = (255, 80, 80)
            self.IMAGE_FILENAME = "img1.png"
            self.TEXT_STR = "WINER 1P!"
        else:
            self.BACKGROUND_COLOR = (80, 80, 255)
            self.IMAGE_FILENAME = "img2.png"
            self.TEXT_STR = "WINER 2P!"

        # --------------------------------------
        # パラメータ類
        # --------------------------------------
        self.initial_width = 4
        self.expand_speed = 900
        self.rotation_speed = 100
        self.pause_time = 0.3
        self.FADE_DURATION = 1.0

        self.DONUT_THICKNESS = 200
        self.DONUT_MAX_RADIUS = int(math.hypot(self.WIDTH, self.HEIGHT) * 2.0)
        self.DONUT_SPEED_STABLE = self.DONUT_MAX_RADIUS / 3.2
        self.DONUT_CENTER_1 = (int(self.WIDTH * 0.5), int(self.HEIGHT * 0.5))
        self.DONUT_CENTER_2 = (int(self.WIDTH * 0.5), int(self.HEIGHT * 0.5))

        self.rotation_speed_fast = 720
        self.rotation_speed_slow = 5
        self.target_rotations = 1

        self.FONT_SIZE = 150
        self.TEXT_ANGLE = 12
        self.TEXT_SPEED_FAST = 2200
        self.TEXT_SPEED_SLOW = 60
        self.TEXT_SLOW_RADIUS = self.WIDTH * 0.12
        self.TEXT_START_Y = self.HEIGHT * 0.68

        self.PHASE1_THRESHOLD_FACTOR = 1.1

        self.SHADOW_OFFSET = (6, 6)
        self.SHADOW_ALPHA = 120
        self.OUTLINE_OFFSETS = [
            (-3,0),(3,0),(0,-3),(0,3),
            (-2,-2),(2,-2),(-2,2),(2,2)
        ]

        #====================================
        # 画像ロード
        #====================================
        if not os.path.exists(self.IMAGE_FILENAME):
            print("画像が見つかりません:", self.IMAGE_FILENAME)
            pygame.quit()
            sys.exit()

        photo = pygame.image.load(self.IMAGE_FILENAME).convert_alpha()
        scale_ratio = min(
            self.WIDTH * 0.45 / photo.get_width(),
            self.HEIGHT * 0.65 / photo.get_height()
        )
        self.photo = pygame.transform.smoothscale(
            photo,
            (int(photo.get_width()*scale_ratio), int(photo.get_height()*scale_ratio))
        )

        #====================================
        # 文字描画準備
        #====================================
        FONT_PATH = "Paintball_Beta_3.ttf"
        self.font = pygame.font.Font(FONT_PATH, self.FONT_SIZE)

        text_surface = self.font.render(self.TEXT_STR, True, (255, 255, 255))
        shadow_surface = self.font.render(self.TEXT_STR, True, (0, 0, 0))
        shadow_surface.set_alpha(self.SHADOW_ALPHA)

        outline_surfaces = []
        for ox, oy in self.OUTLINE_OFFSETS:
            s = self.font.render(self.TEXT_STR, True, (0, 0, 0))
            outline_surfaces.append((s, ox, oy))

        self.rotated_text_surface = pygame.transform.rotate(text_surface, self.TEXT_ANGLE)
        self.rotated_shadow_surface = pygame.transform.rotate(shadow_surface, self.TEXT_ANGLE)

        self.rotated_outline_surfaces = []
        for s, ox, oy in outline_surfaces:
            rotated_s = pygame.transform.rotate(s, self.TEXT_ANGLE)
            self.rotated_outline_surfaces.append((rotated_s, ox, oy))

        self.text_w, self.text_h = self.rotated_text_surface.get_size()
        self.text_x = -self.text_w
        self.text_y = self.TEXT_START_Y
        self.center_target_x = (self.WIDTH - self.text_w) / 2

        rad = math.radians(self.TEXT_ANGLE)
        self.move_dx = math.cos(rad)
        self.move_dy = -math.sin(rad)

        #====================================
        # ドーナツクラス
        #====================================
        class Donut:
            def __init__(self, parent, center):
                self.parent = parent
                self.center = center
                self.speed = parent.DONUT_SPEED_STABLE
                self.start_time = None
                self.active = False
                self.outer = 0
                self.inner = 0

            def start(self):
                self.start_time = time.time()
                self.active = True
                self.outer = 0

            def update(self):
                if not self.active:
                    return False
                elapsed = time.time() - self.start_time
                self.outer = int(elapsed * self.speed)
                if self.outer >= self.parent.DONUT_MAX_RADIUS:
                    self.active = False
                    return False
                self.inner = max(0, self.outer - self.parent.DONUT_THICKNESS)
                return True

            def draw(self, s, alpha=255):
                if self.active:
                    self.parent.draw_donut(s, self.center, self.inner, self.outer, (255, 255, 255, alpha))

        self.Donut = Donut
        self.donut1 = Donut(self, self.DONUT_CENTER_1)
        self.donut2 = Donut(self, self.DONUT_CENTER_2)
        self.donut2_started = False

        #====================================
        # 状態管理
        #====================================
        self.phase = 1
        self.phase_start = time.time()

        self.photo_x = -self.photo.get_width()
        self.photo_y = self.CENTER[1]
        self.rotation_angle = 0.0
        self.current_width = self.initial_width
        self.current_angle = 0.0

        self.text_active = False
        self.text_fixed = False


    #--------------------------------------
    # ドーナツ描画
    #--------------------------------------
    def draw_donut(self, surface, center, inner_r, outer_r, color):
        tmp = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(tmp, color, center, outer_r)
        pygame.draw.circle(tmp, (0, 0, 0, 0), center, inner_r)
        surface.blit(tmp, (0, 0))


    #====================================
    # メイン実行
    #====================================
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)/1000.0
            now = time.time()
            phase_elapsed = now - self.phase_start

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # ---------------------
            # Phase 1
            # ---------------------
            if self.phase == 1:
                if phase_elapsed < self.pause_time:
                    self.current_width = self.initial_width
                else:
                    t = phase_elapsed - self.pause_time
                    self.current_width = self.initial_width + self.expand_speed*t
                    self.current_angle = self.rotation_speed*t

                self.screen.fill((0, 0, 0))

                diag = int(math.hypot(self.WIDTH, self.HEIGHT)*2.0)
                rect_s = pygame.Surface((max(1, int(self.current_width)), diag), pygame.SRCALPHA)
                rect_s.fill((255, 255, 255))
                rotated = pygame.transform.rotate(rect_s, self.current_angle)
                rect = rotated.get_rect(center=self.CENTER)
                self.screen.blit(rotated, rect)

                if self.current_width >= self.WIDTH * self.PHASE1_THRESHOLD_FACTOR:
                    self.phase = 2
                    self.phase_start = now

            # ---------------------
            # Phase 2
            # ---------------------
            elif self.phase == 2:
                alpha = min(phase_elapsed / self.FADE_DURATION, 1.0)
                bg = (
                    int(255*(1-alpha)+self.BACKGROUND_COLOR[0]*alpha),
                    int(255*(1-alpha)+self.BACKGROUND_COLOR[1]*alpha),
                    int(255*(1-alpha)+self.BACKGROUND_COLOR[2]*alpha)
                )
                self.screen.fill(bg)

                if alpha >= 1.0:
                    self.phase = 3
                    self.phase_start = now

            # ---------------------
            # Phase 3
            # ---------------------
            elif self.phase == 3:
                self.rotation_angle = self.rotation_speed_fast * phase_elapsed

                time_for_rot = 360 * self.target_rotations / self.rotation_speed_fast
                move_ratio = min(phase_elapsed / time_for_rot, 1.0)
                self.photo_x = (-self.photo.get_width())*(1-move_ratio) + self.CENTER[0]*move_ratio

                self.screen.fill(self.BACKGROUND_COLOR)
                rotated = pygame.transform.rotate(self.photo, self.rotation_angle)
                rect = rotated.get_rect(center=(self.photo_x, self.photo_y))
                self.screen.blit(rotated, rect)

                if move_ratio >= 1.0:
                    self.donut1.start()
                    self.text_active = True
                    self.text_x = -self.text_w
                    self.text_y = self.TEXT_START_Y
                    self.text_fixed = False

                    self.phase = 4
                    self.phase_start = now

            # ---------------------
            # Phase 4
            # ---------------------
            elif self.phase == 4:

                self.rotation_angle += self.rotation_speed_slow * dt
                self.screen.fill(self.BACKGROUND_COLOR)

                alive1 = self.donut1.update()
                self.donut1.draw(self.screen, 230)

                if (not alive1) and (not self.donut2.active) and (not self.donut2_started):
                    self.donut2.start()
                    self.donut2_started = True

                if self.donut2.active:
                    self.donut2.update()
                    self.donut2.draw(self.screen, 230)

                rotated = pygame.transform.rotate(self.photo, self.rotation_angle)
                rect = rotated.get_rect(center=self.CENTER)
                self.screen.blit(rotated, rect)

                # --- Text animation ---
                if self.text_active:
                    if not self.text_fixed:
                        dist = self.center_target_x - self.text_x
                        speed = (
                            self.TEXT_SPEED_FAST
                            if abs(dist) > self.TEXT_SLOW_RADIUS
                            else self.TEXT_SPEED_SLOW
                        )

                        if self.text_x < self.center_target_x:
                            self.text_x += self.move_dx * speed * dt
                            self.text_y += self.move_dy * speed * dt

                        if self.text_x >= self.center_target_x:
                            self.text_x = self.center_target_x
                            self.text_fixed = True

                    shadow_pos = (self.text_x+self.SHADOW_OFFSET[0], self.text_y+self.SHADOW_OFFSET[1])
                    self.screen.blit(self.rotated_shadow_surface, shadow_pos)

                    for surf, ox, oy in self.rotated_outline_surfaces:
                        self.screen.blit(surf, (self.text_x+ox, self.text_y+oy))

                    self.screen.blit(self.rotated_text_surface, (self.text_x, self.text_y))

                if self.donut2_started and (not self.donut2.active) and self.text_fixed:
                    self.phase = 5
                    self.phase_start = now

            # ---------------------
            # Phase 5
            # ---------------------
            elif self.phase == 5:
                self.screen.fill(self.BACKGROUND_COLOR)
                rotated = pygame.transform.rotate(self.photo, self.rotation_angle)
                rect = rotated.get_rect(center=self.CENTER)
                self.screen.blit(rotated, rect)

                shadow_pos = (self.text_x+self.SHADOW_OFFSET[0], self.text_y+self.SHADOW_OFFSET[1])
                self.screen.blit(self.rotated_shadow_surface, shadow_pos)

                for surf, ox, oy in self.rotated_outline_surfaces:
                    self.screen.blit(surf, (self.text_x+ox, self.text_y+oy))

                self.screen.blit(self.rotated_text_surface, (self.text_x, self.text_y))

                if now - self.phase_start > 2.0:
                    running = False

            pygame.display.flip()

        pygame.quit()
        sys.exit()



#==============================================
# main
#==============================================
def main():
    anim = ResultAnimation(first_player_win=True)   # ←1P勝利
    # anim = ResultAnimation(first_player_win=False)  # ←2P勝利
    anim.run()


if __name__ == "__main__":
    main()
