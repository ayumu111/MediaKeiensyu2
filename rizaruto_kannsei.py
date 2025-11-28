import pygame
import sys
import math
import time
import os

# ====================================
# ★ 先攻勝利か後攻勝利かを設定する場所
# ====================================
FIRST_PLAYER_WIN = True   # True = 先攻勝利 / False = 後攻勝利
# FIRST_PLAYER_WIN = False   # True = 先攻勝利 / False = 後攻勝利
# ====================================

pygame.init()
SCREEN_SIZE = (800, 600)
screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()

WIDTH, HEIGHT = screen.get_size()
CENTER = (WIDTH // 2, HEIGHT // 2)

# --- 勝敗による設定変更 ---
if FIRST_PLAYER_WIN:
    BACKGROUND_COLOR = (255, 80, 80)     # 赤系
    IMAGE_FILENAME = "img1.png"
    TEXT_STR = "WINER 1P!"
else:
    BACKGROUND_COLOR = (80, 80, 255)     # 水色系（今まで通り）
    IMAGE_FILENAME = "img2.png"
    TEXT_STR = "WINER 2P!"

# ====================================
# ここから下は元コードと同じ（変数は勝敗で変化済）
# ====================================

initial_width = 4
expand_speed = 900
rotation_speed = 100
pause_time = 0.3

FADE_DURATION = 1.0

DONUT_THICKNESS = 200
DONUT_MAX_RADIUS = int(math.hypot(WIDTH, HEIGHT) * 2.0)
DONUT_SPEED_STABLE = DONUT_MAX_RADIUS / 3.2

DONUT_CENTER_1 = (int(WIDTH * 0.5), int(HEIGHT * 0.5))
DONUT_CENTER_2 = (int(WIDTH * 0.5), int(HEIGHT * 0.5))

rotation_speed_fast = 720
rotation_speed_slow = 5
target_rotations = 1

FONT_SIZE = 150
TEXT_ANGLE = 12
TEXT_SPEED_FAST = 2200
TEXT_SPEED_SLOW = 60
TEXT_SLOW_RADIUS = WIDTH * 0.12
TEXT_START_Y = HEIGHT * 0.68

PHASE1_THRESHOLD_FACTOR = 1.1

SHADOW_OFFSET = (6, 6)
SHADOW_ALPHA = 120
OUTLINE_OFFSETS = [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,-2),(-2,2),(2,2)]

def draw_donut(surface, center, inner_r, outer_r, color=(255, 255, 255, 255)):
    tmp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(tmp, color, center, outer_r)
    pygame.draw.circle(tmp, (0, 0, 0, 0), center, inner_r)
    surface.blit(tmp, (0, 0))


# ============================
#   画像ロード
# ============================
if not os.path.exists(IMAGE_FILENAME):
    print("画像が見つかりません:", IMAGE_FILENAME)
    pygame.quit()
    sys.exit()

photo = pygame.image.load(IMAGE_FILENAME).convert_alpha()
scale_ratio = min(WIDTH * 0.45 / photo.get_width(), HEIGHT * 0.65 / photo.get_height())
photo = pygame.transform.smoothscale(
    photo,
    (int(photo.get_width()*scale_ratio), int(photo.get_height()*scale_ratio))
)

# ============================
#   文字描画準備
# ============================
FONT_PATH = "Paintball_Beta_3.ttf"
font = pygame.font.Font(FONT_PATH, FONT_SIZE)

text_surface = font.render(TEXT_STR, True, (255, 255, 255))
shadow_surface = font.render(TEXT_STR, True, (0, 0, 0))
shadow_surface.set_alpha(SHADOW_ALPHA)

outline_surfaces = []
for ox, oy in OUTLINE_OFFSETS:
    s = font.render(TEXT_STR, True, (0, 0, 0))
    outline_surfaces.append((s, ox, oy))

rotated_text_surface = pygame.transform.rotate(text_surface, TEXT_ANGLE)
rotated_shadow_surface = pygame.transform.rotate(shadow_surface, TEXT_ANGLE)

rotated_outline_surfaces = []
for s, ox, oy in outline_surfaces:
    rotated_s = pygame.transform.rotate(s, TEXT_ANGLE)
    rotated_outline_surfaces.append((rotated_s, ox, oy))

text_w, text_h = rotated_text_surface.get_size()
text_x = -text_w
text_y = TEXT_START_Y
center_target_x = (WIDTH - text_w) / 2

rad = math.radians(TEXT_ANGLE)
move_dx = math.cos(rad)
move_dy = -math.sin(rad)


# ============================
#   ドーナツクラス
# ============================
class Donut:
    def __init__(self, center):
        self.center = center
        self.speed = DONUT_SPEED_STABLE
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
        if self.outer >= DONUT_MAX_RADIUS:
            self.active = False
            return False
        self.inner = max(0, self.outer - DONUT_THICKNESS)
        return True

    def draw(self, s, alpha=255):
        if self.active:
            draw_donut(s, self.center, self.inner, self.outer, (255, 255, 255, alpha))


donut1 = Donut(DONUT_CENTER_1)
donut2 = Donut(DONUT_CENTER_2)
donut2_started = False

phase = 1
phase_start = time.time()

photo_x = -photo.get_width()
photo_y = CENTER[1]
rotation_angle = 0.0

current_width = initial_width
current_angle = 0.0

text_active = False
text_fixed = False


# ============================
#   メインループ
# ============================
running = True
while running:
    dt = clock.tick(60)/1000.0
    now = time.time()
    phase_elapsed = now - phase_start

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Phase 1
    if phase == 1:
        if phase_elapsed < pause_time:
            current_width = initial_width
        else:
            t = phase_elapsed - pause_time
            current_width = initial_width + expand_speed*t
            current_angle = rotation_speed*t

        screen.fill((0, 0, 0))

        diag = int(math.hypot(WIDTH, HEIGHT)*2.0)
        rect_s = pygame.Surface((max(1, int(current_width)), diag), pygame.SRCALPHA)
        rect_s.fill((255, 255, 255))
        rotated = pygame.transform.rotate(rect_s, current_angle)
        rect = rotated.get_rect(center=CENTER)
        screen.blit(rotated, rect)

        if current_width >= WIDTH * PHASE1_THRESHOLD_FACTOR:
            phase = 2
            phase_start = now

    # Phase 2
    elif phase == 2:
        alpha = min(phase_elapsed / FADE_DURATION, 1.0)
        bg = (
            int(255*(1-alpha)+BACKGROUND_COLOR[0]*alpha),
            int(255*(1-alpha)+BACKGROUND_COLOR[1]*alpha),
            int(255*(1-alpha)+BACKGROUND_COLOR[2]*alpha)
        )
        screen.fill(bg)
        if alpha >= 1.0:
            phase = 3
            phase_start = now

    # Phase 3
    elif phase == 3:
        rotation_angle = rotation_speed_fast * phase_elapsed

        time_for_rot = 360 * target_rotations / rotation_speed_fast
        move_ratio = min(phase_elapsed / time_for_rot, 1.0)
        photo_x = (-photo.get_width())*(1-move_ratio) + CENTER[0]*move_ratio

        screen.fill(BACKGROUND_COLOR)
        rotated = pygame.transform.rotate(photo, rotation_angle)
        rect = rotated.get_rect(center=(photo_x, photo_y))
        screen.blit(rotated, rect)

        if move_ratio >= 1.0:
            donut1.start()
            text_active = True
            text_x = -text_w
            text_y = TEXT_START_Y
            text_fixed = False
            phase = 4
            phase_start = now

    # Phase 4
    elif phase == 4:
        rotation_angle += rotation_speed_slow * dt
        screen.fill(BACKGROUND_COLOR)

        alive1 = donut1.update()
        donut1.draw(screen, 230)

        if (not alive1) and (not donut2.active) and (not donut2_started):
            donut2.start()
            donut2_started = True

        if donut2.active:
            donut2.update()
            donut2.draw(screen, 230)

        rotated = pygame.transform.rotate(photo, rotation_angle)
        rect = rotated.get_rect(center=CENTER)
        screen.blit(rotated, rect)

        if text_active:
            if not text_fixed:
                dist = center_target_x - text_x
                speed = TEXT_SPEED_FAST if abs(dist) > TEXT_SLOW_RADIUS else TEXT_SPEED_SLOW

                if text_x < center_target_x:
                    text_x += move_dx * speed * dt
                    text_y += move_dy * speed * dt

                if text_x >= center_target_x:
                    text_x = center_target_x
                    text_fixed = True

            shadow_pos = (text_x+SHADOW_OFFSET[0], text_y+SHADOW_OFFSET[1])
            screen.blit(rotated_shadow_surface, shadow_pos)

            for surf, ox, oy in rotated_outline_surfaces:
                screen.blit(surf, (text_x+ox, text_y+oy))

            screen.blit(rotated_text_surface, (text_x, text_y))

        if donut2_started and (not donut2.active) and text_fixed:
            phase = 5
            phase_start = now

    # Phase 5
    elif phase == 5:
        screen.fill(BACKGROUND_COLOR)
        rotated = pygame.transform.rotate(photo, rotation_angle)
        rect = rotated.get_rect(center=CENTER)
        screen.blit(rotated, rect)

        shadow_pos = (text_x+SHADOW_OFFSET[0], text_y+SHADOW_OFFSET[1])
        screen.blit(rotated_shadow_surface, shadow_pos)

        for surf, ox, oy in rotated_outline_surfaces:
            screen.blit(surf, (text_x+ox, text_y+oy))

        screen.blit(rotated_text_surface, (text_x, text_y))

        if now - phase_start > 2.0:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()
