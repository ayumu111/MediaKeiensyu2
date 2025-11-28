import pygame
import sys
import math
import time
import os

# ==============================
# 初期化
# ==============================
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

WIDTH, HEIGHT = screen.get_size()
CENTER = (WIDTH // 2, HEIGHT // 2)

# ==============================
# パラメータ定義
# ==============================

# Phase 1: 白線拡張
initial_width = 4
expand_speed = 900
rotation_speed = 100
pause_time = 0.3

# Phase 2: 背景 + X フェード
BACKGROUND_COLOR = (180, 220, 255)
FADE_DURATION = 1.0

diag = math.hypot(WIDTH, HEIGHT)
LINE_LENGTH = int(diag * 2.0)
LINE_WIDTH_THICK = 60
LINE_WIDTH_THIN = 20
ANGLE1 = 85
ANGLE2 = -45
X_CENTER = (int(WIDTH * 0.62), int(HEIGHT * 0.50))

# Phase 3–4: 画像回転・移動
IMAGE_FILENAME = "img1.png"
rotation_speed_fast = 720      # 画像の高速回転 (deg/sec)
slow_rotation_speed = 2       # 低速回転 (deg/sec)
target_rotations = 1
hold_duration = 1.0           # 低速維持の最低時間（秒）→その間に文字が出る

# Phase 5: 文字演出
TEXT_STR = "せんこうのかち！"
FONT_SIZE = 100
TEXT_ANGLE = 12               # 文字の傾き（度）
TEXT_SPEED_FAST = 2200         # 文字高速移動 (px/sec)
TEXT_SPEED_SLOW = 60         # 文字減速時の速度
TEXT_SLOW_RADIUS = WIDTH * 0.12

# 移動は文字の横方向（文字角度に平行）
# 文字初期Yは画面上部寄せ
TEXT_START_Y = HEIGHT * 0.68

# Phase1->2 切替しやすくする係数 (早めにする)
PHASE1_THRESHOLD_FACTOR = 1.1  # WIDTH * 1.1 で早めに切替

# ========== 追加：アウトライン & シャドウ設定 ==========
SHADOW_OFFSET = (6, 6)      # 影のオフセット (x, y)
SHADOW_ALPHA = 120          # 影の不透明度 (0-255)
OUTLINE_OFFSETS = [         # アウトラインのオフセット (x, y)
    (-3, 0), (3, 0), (0, -3), (0, 3),
    (-2, -2), (2, -2), (-2, 2), (2, 2)
]
# =======================================================

# ==============================
# 共通描画関数
# ==============================
def draw_line(length, width, angle, alpha, center):
    surf = pygame.Surface((length, width), pygame.SRCALPHA)
    surf.fill((255, 255, 255, alpha))
    rot = pygame.transform.rotate(surf, angle)
    rect = rot.get_rect(center=center)
    screen.blit(rot, rect)

# ==============================
# 画像ロード
# ==============================
if not os.path.exists(IMAGE_FILENAME):
    print("画像ファイルが見つかりません:", IMAGE_FILENAME)
    pygame.quit()
    sys.exit()

photo = pygame.image.load(IMAGE_FILENAME).convert_alpha()
scale_ratio = min(WIDTH * 0.45 / photo.get_width(),
                  HEIGHT * 0.65 / photo.get_height())
photo = pygame.transform.smoothscale(
    photo,
    (int(photo.get_width() * scale_ratio),
     int(photo.get_height() * scale_ratio))
)

# photo の初期状態
photo_x = -photo.get_width()
photo_y = CENTER[1]
rotation_angle = 0.0

# ========== 文字準備（本体・影・アウトラインを作成して回転） ==========
font = pygame.font.SysFont("meiryo", FONT_SIZE, bold=True)

# 本体（白）
text_surface = font.render(TEXT_STR, True, (255, 255, 255))

# 影（黒・半透明）
shadow_surface = font.render(TEXT_STR, True, (0, 0, 0))
# set_alpha が効くように convert_alpha は不要；ただし surface 単位の alpha を設定
shadow_surface.set_alpha(SHADOW_ALPHA)

# アウトライン（黒、複数方向）
outline_surfaces = []
for ox, oy in OUTLINE_OFFSETS:
    s = font.render(TEXT_STR, True, (0, 0, 0))
    outline_surfaces.append((s, ox, oy))

# 回転は文字角に合わせて一度だけ作る（テキストは固定）
rotated_text_surface = pygame.transform.rotate(text_surface, TEXT_ANGLE)
rotated_shadow_surface = pygame.transform.rotate(shadow_surface, TEXT_ANGLE)
rotated_outline_surfaces = []
for s, ox, oy in outline_surfaces:
    rotated_s = pygame.transform.rotate(s, TEXT_ANGLE)
    rotated_outline_surfaces.append((rotated_s, ox, oy))
# =======================================================

# 文字サイズ（回転後のサイズ）
text_w, text_h = rotated_text_surface.get_size()

# 文字移動開始位置（画面左外）
text_x = -text_w
text_y = TEXT_START_Y

# 文字停止ターゲット（中央寄せ）
center_target_x = (WIDTH - text_w) / 2

# 文字移動ベクトル（文字の横方向に平行）
rad = math.radians(TEXT_ANGLE)
move_dx = math.cos(rad)   # 右向き
move_dy = -1 * math.sin(rad)   # Y軸方向の符号はここで調整（上に行く場合 negative）

# ==============================
# フェーズ管理（統合ループ）
# ==============================
phase = 1
phase_start = time.time()

# 状態フラグ（文字が出ているか）
text_active = False
text_start_time = None

# Phase1 用変数（start時は0）
current_width = initial_width
current_angle = 0.0

running = True
while running:
    dt = clock.tick(60) / 1000.0
    now = time.time()
    phase_elapsed = now - phase_start

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ---------- Phase 1: 白い線拡張 ----------
    if phase == 1:
        if phase_elapsed < pause_time:
            current_width = initial_width
            current_angle = 0.0
        else:
            t = phase_elapsed - pause_time
            current_width = initial_width + expand_speed * t
            current_angle = rotation_speed * t

        # 描画
        screen.fill((0, 0, 0))
        # 長さを十分大きくして回転しても途切れないようにする
        diag_len = int(math.hypot(WIDTH, HEIGHT) * 2.0)
        rect_surface = pygame.Surface((max(1, int(current_width)), diag_len), pygame.SRCALPHA)
        rect_surface.fill((255, 255, 255))
        rotated = pygame.transform.rotate(rect_surface, current_angle)
        rect = rotated.get_rect(center=CENTER)
        screen.blit(rotated, rect)

        # 早めに Phase2 に切り替える（WIDTH * PHASE1_THRESHOLD_FACTOR）
        if current_width >= WIDTH * PHASE1_THRESHOLD_FACTOR:
            phase = 2
            phase_start = time.time()
            # ensure small delay variables reset
            # no display.flip here — unified loop avoids lag

    # ---------- Phase 2: 背景 + X フェード ----------
    elif phase == 2:
        alpha_ratio = min(phase_elapsed / FADE_DURATION, 1.0)
        screen.fill(BACKGROUND_COLOR)

        line_alpha = int(alpha_ratio * 255)
        draw_line(LINE_LENGTH, LINE_WIDTH_THICK, ANGLE1, line_alpha, X_CENTER)
        draw_line(LINE_LENGTH, LINE_WIDTH_THIN, ANGLE2, line_alpha, X_CENTER)

        # 白オーバーレイを上に置く（だんだん透明）
        white_overlay = pygame.Surface((WIDTH, HEIGHT))
        white_overlay.fill((255, 255, 255))
        white_overlay.set_alpha(int((1.0 - alpha_ratio) * 255))
        screen.blit(white_overlay, (0, 0))

        if alpha_ratio >= 1.0:
            phase = 3
            phase_start = time.time()

    # ---------- Phase 3: 画像 回転 + 左→中央へスライド ----------
    elif phase == 3:
        # 高速回転（時間から角度を計算）
        rotation_angle = rotation_speed_fast * phase_elapsed

        # 移動のための時間（1回転で中央到達）
        time_for_rot = (360 * target_rotations) / rotation_speed_fast
        movement_ratio = min(phase_elapsed / time_for_rot, 1.0)

        photo_x = (1 - movement_ratio) * (-photo.get_width()) + movement_ratio * CENTER[0]

        # 描画
        screen.fill(BACKGROUND_COLOR)
        draw_line(LINE_LENGTH, LINE_WIDTH_THICK, ANGLE1, 255, X_CENTER)
        draw_line(LINE_LENGTH, LINE_WIDTH_THIN, ANGLE2, 255, X_CENTER)
        rotated = pygame.transform.rotate(photo, rotation_angle)
        rect = rotated.get_rect(center=(photo_x, photo_y))
        screen.blit(rotated, rect)

        # 到達したらすぐに減速フェーズへ移行 AND 同時に文字出現開始
        if movement_ratio >= 1.0:
            phase = 4
            phase_start = time.time()
            # start text simultaneously
            text_active = True
            text_start_time = time.time()
            # Ensure text initial position (left outside)
            text_x = -text_w
            text_y = TEXT_START_Y

    # ---------- Phase 4: 画像 減速回転（低速） ＋ 文字並行出現 ----------
    elif phase == 4:
        # 画像低速回転（累積更新）
        rotation_angle += slow_rotation_speed * dt

        # draw photo (centered)
        rotated = pygame.transform.rotate(photo, rotation_angle)
        rect = rotated.get_rect(center=(CENTER[0], photo_y))

        # If text_active, update its motion each frame (parallel to text horizontal)
        if text_active:
            # distance to target measured along X (sufficient since movement is rightwards)
            dist_x = center_target_x - text_x

            # speed selection
            if abs(dist_x) > TEXT_SLOW_RADIUS:
                speed = TEXT_SPEED_FAST
            else:
                speed = TEXT_SPEED_SLOW

            # move along text horizontal (dx, dy)
            text_x += move_dx * speed * dt
            text_y += move_dy * speed * dt

            # clamp so it doesn't overshoot deeply
            if text_x >= center_target_x:
                text_x = center_target_x

        # draw everything
        screen.fill(BACKGROUND_COLOR)
        draw_line(LINE_LENGTH, LINE_WIDTH_THICK, ANGLE1, 255, X_CENTER)
        draw_line(LINE_LENGTH, LINE_WIDTH_THIN, ANGLE2, 255, X_CENTER)
        screen.blit(rotated, rect)

        # ---------- ここで影・アウトライン・本体の順で描画 ----------
        if text_active:
            # 1) 影（オフセットして描画）
            shadow_pos = (text_x + SHADOW_OFFSET[0], text_y + SHADOW_OFFSET[1])
            screen.blit(rotated_shadow_surface, shadow_pos)

            # 2) アウトライン群（各オフセットで描画）
            for rot_surf, ox, oy in rotated_outline_surfaces:
                screen.blit(rot_surf, (text_x + ox, text_y + oy))

            # 3) 本体
            screen.blit(rotated_text_surface, (text_x, text_y))

        # After holding a short while (optional), move to final phase (keeping text)
        if (now - phase_start) >= hold_duration and text_active and text_x >= center_target_x:
            phase = 5
            phase_start = time.time()

    # ---------- Phase 5: 最終保持フェーズ（テキスト停止・余韻） ----------
    elif phase == 5:
        # keep slight rotation on photo
        rotation_angle += slow_rotation_speed * dt

        rotated = pygame.transform.rotate(photo, rotation_angle)
        rect = rotated.get_rect(center=(CENTER[0], photo_y))

        # draw base
        screen.fill(BACKGROUND_COLOR)
        draw_line(LINE_LENGTH, LINE_WIDTH_THICK, ANGLE1, 255, X_CENTER)
        draw_line(LINE_LENGTH, LINE_WIDTH_THIN, ANGLE2, 255, X_CENTER)
        screen.blit(rotated, rect)

        # 描画：影→アウトライン→本体（最終表示）
        shadow_pos = (text_x + SHADOW_OFFSET[0], text_y + SHADOW_OFFSET[1])
        screen.blit(rotated_shadow_surface, shadow_pos)

        for rot_surf, ox, oy in rotated_outline_surfaces:
            screen.blit(rot_surf, (text_x + ox, text_y + oy))

        screen.blit(rotated_text_surface, (text_x, text_y))

        # Optionally stop after some time (here 2.0s of final display), then exit
        if (now - phase_start) > 2.0:
            running = False

    # Flip once per frame
    pygame.display.flip()

# 終了
pygame.quit()
sys.exit()
