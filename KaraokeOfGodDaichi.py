import pygame
import sys
import math

pygame.init()
SCREEN_SIZE = (800, 600)
screen = pygame.display.set_mode(SCREEN_SIZE)
clock = pygame.time.Clock()

# -------------------------------
# 色の設定（←ここで変更可能）
# -------------------------------
CIRCLE_COLOR = (240, 240, 240, 180)             # 円の色（半透明）
BASE_TRI_COLOR = (180, 180, 180, 180)    # 基準三角形の色
SCORE_COLOR = (255, 230, 0, 255)         # スコア三角形の色（塗り）
SCORE_EDGE_COLOR = (200, 160, 0, 200)       # スコア三角形の縁
LABEL_COLOR = (0, 0, 0)                  # ラベル文字色

BG_COLOR = (84, 209, 255)                 # 背景色

# -------------------------------
# アウトライン描画
# -------------------------------
def render_outline(text, font, text_color, outline_color, outline_width=2):
    base = font.render(text, True, text_color)
    w, h = base.get_size()
    surf = pygame.Surface((w + outline_width*2, h + outline_width*2), pygame.SRCALPHA)

    for dx in (-outline_width, outline_width):
        for dy in (-outline_width, outline_width):
            shadow = font.render(text, True, outline_color)
            surf.blit(shadow, (dx + outline_width, dy + outline_width))

    surf.blit(base, (outline_width, outline_width))
    return surf

# -------------------------------
# フェード関数
# -------------------------------
def fade_in(surface, target_alpha, step=5):
    alpha = surface.get_alpha() or 0
    alpha = min(alpha + step, target_alpha)
    surface.set_alpha(alpha)
    return alpha == target_alpha

# -------------------------------
# フォント準備（←ここでサイズ調節）
# -------------------------------
font_en = pygame.font.Font("Paintball_Beta_3.ttf", 60)
font_hira_title = pygame.font.Font("IoEI.ttf", 80)
font_players = pygame.font.Font("Paintball_Beta_3.ttf", 50)
font_labels = pygame.font.Font("IoEI.ttf", 30)
font_score = pygame.font.Font("Paintball_Beta_3.ttf", 30)
font_total = pygame.font.Font("Paintball_Beta_3.ttf", 90)

# -------------------------------
# 背景
# -------------------------------
background = pygame.Surface(SCREEN_SIZE)
background.fill(BG_COLOR)
background.set_alpha(0)

# タイトル
title_surf = render_outline("とくてん", font_hira_title, (255,255,255), (0,0,0))
title_surf.set_alpha(0)
title_pos = title_surf.get_rect(center=(400, 80))

# 中央ライン
line_surf = pygame.Surface((4, 450))
line_surf.fill((0, 0, 0))
line_surf.set_alpha(0)
line_pos = line_surf.get_rect(center=(400, 350))

# 1P / 2P
p1_surf = render_outline("1P", font_players, (255,255,255), (255,80,80))
p2_surf = render_outline("2P", font_players, (255,255,255), (80,80,255))
p1_surf.set_alpha(0)
p2_surf.set_alpha(0)
p1_pos = p1_surf.get_rect(center=(200, 150))
p2_pos = p2_surf.get_rect(center=(600, 150))

# -------------------------------
# レーダーチャート描画準備
# -------------------------------
RADIUS = 120
LABEL_DIST = 150
CENTER_L = (200, 350)
CENTER_R = (600, 350)

circle_left = pygame.Surface((300, 300), pygame.SRCALPHA)
circle_right = pygame.Surface((300, 300), pygame.SRCALPHA)
circle_left.set_alpha(0)
circle_right.set_alpha(0)

pygame.draw.circle(circle_left, CIRCLE_COLOR, (150, 150), RADIUS)
pygame.draw.circle(circle_right, CIRCLE_COLOR, (150, 150), RADIUS)

# 基準三角形
def draw_base_triangle(surface, color=BASE_TRI_COLOR):
    cx, cy = 150, 150
    pts = []
    for i in range(3):
        ang = -90 + i * 120
        rad = math.radians(ang)
        x = cx + RADIUS * math.cos(rad)
        y = cy + RADIUS * math.sin(rad)
        pts.append((x, y))
    pygame.draw.polygon(surface, color, pts, 3)

draw_base_triangle(circle_left)
draw_base_triangle(circle_right)

# ラベル
labels = [
    ("ダイナミック", -90),
    ("あんてい", 30),
    ("こせい", 150)
]
label_surfs = [(font_labels.render(t, True, LABEL_COLOR), ang) for t, ang in labels]

# -------------------------------
# スコア
# -------------------------------
score_dynamic_1P = 3
score_stable_1P = 3
score_unique_1P = 3

score_dynamic_2P = 8
score_stable_2P = 3
score_unique_2P = 10

total_1P = score_dynamic_1P + score_stable_1P + score_unique_1P
total_2P = score_dynamic_2P + score_stable_2P + score_unique_2P

score_progress = 0.0
SCORE_GROW_SPEED = 0.015

# -------------------------------
# 下の項目
# -------------------------------
bottom_labels = ["ダイナミック", "あんてい", "こせい"]

bottom = {
    "L": {"x": 50, "y": 480},
    "R": {"x": 430, "y": 480},
}

for side in bottom:
    bottom[side]["label_surfs"] = [
        font_labels.render(name, True, (0,0,0)) for name in bottom_labels
    ]
    for surf in bottom[side]["label_surfs"]:
        surf.set_alpha(0)

    score_list = (
        [score_dynamic_1P, score_stable_1P, score_unique_1P]
        if side == "L"
        else [score_dynamic_2P, score_stable_2P, score_unique_2P]
    )

    bottom[side]["scores"] = []
    for sc in score_list:
        if side == "L":
            s = render_outline(str(sc), font_score, (255, 255, 255), (255, 80, 80))
        else:
            s = render_outline(str(sc), font_score, (255, 255, 255), (80, 80, 255))
        s.set_alpha(0)
        bottom[side]["scores"].append(s)

    bottom[side]["total_now"] = 0
    bottom[side]["total_target"] = total_1P if side == "L" else total_2P

# -------------------------------
# STEP管理（順番を修正済み）
# -------------------------------
STEP_BACKGROUND = 0
STEP_TITLE = 1
STEP_LINE = 2
STEP_PLAYERS = 3
STEP_CHART_FRAME = 4       # 半透明円＋基準三角形
STEP_SCORE_LABELS = 5      # 下ラベル
STEP_SCORE_NUMBERS = 6     # 下の点数
STEP_CHART_SCORE = 7       # 黄色スコア三角形（←後ろにずらした）
STEP_TOTAL_SCORE = 8       # 合計

step = STEP_BACKGROUND

# -------------------------------
# メインループ
# -------------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))
    screen.blit(background, (0, 0))

    # 上部共通描画
    if step >= STEP_TITLE:
        screen.blit(title_surf, title_pos)
    if step >= STEP_LINE:
        screen.blit(line_surf, line_pos)
    if step >= STEP_PLAYERS:
        screen.blit(p1_surf, p1_pos)
        screen.blit(p2_surf, p2_pos)

    # STEP
    if step == STEP_BACKGROUND:
        if fade_in(background, 255):
            step = STEP_TITLE

    elif step == STEP_TITLE:
        if fade_in(title_surf, 255):
            step = STEP_LINE

    elif step == STEP_LINE:
        if fade_in(line_surf, 255):
            step = STEP_PLAYERS

    elif step == STEP_PLAYERS:
        left_done = fade_in(p1_surf, 255)
        right_done = fade_in(p2_surf, 255)
        if left_done and right_done:
            step = STEP_CHART_FRAME

    elif step == STEP_CHART_FRAME:
        left_done = fade_in(circle_left, 255)
        right_done = fade_in(circle_right, 255)
        if left_done and right_done:
            step = STEP_SCORE_LABELS

    elif step == STEP_SCORE_LABELS:
        done = True
        for side in bottom:
            for surf in bottom[side]["label_surfs"]:
                if not fade_in(surf, 255):
                    done = False
        if done:
            step = STEP_SCORE_NUMBERS

    elif step == STEP_SCORE_NUMBERS:
        done = True
        for side in bottom:
            for surf in bottom[side]["scores"]:
                if not fade_in(surf, 255):
                    done = False
        if done:
            step = STEP_CHART_SCORE

    elif step == STEP_CHART_SCORE:
        score_progress = min(score_progress + SCORE_GROW_SPEED, 1.0)
        if score_progress >= 1.0:
            step = STEP_TOTAL_SCORE

    elif step == STEP_TOTAL_SCORE:
        for side in bottom:
            if bottom[side]["total_now"] < bottom[side]["total_target"]:
                bottom[side]["total_now"] += 1

    # 円
    screen.blit(circle_left, (CENTER_L[0] - 150, CENTER_L[1] - 150))
    screen.blit(circle_right, (CENTER_R[0] - 150, CENTER_R[1] - 150))

    # ラベル
    if step >= STEP_CHART_FRAME:
        for surf, ang in label_surfs:
            rad = math.radians(ang)
            for center in (CENTER_L, CENTER_R):
                x = center[0] + LABEL_DIST * math.cos(rad)
                y = center[1] + LABEL_DIST * math.sin(rad)
                pos = surf.get_rect(center=(x, y))
                screen.blit(surf, pos)

    # 黄色スコア三角
    if step >= STEP_CHART_SCORE:
        def draw_score_triangle(center, s1, s2, s3):
            surf = pygame.Surface((300, 300), pygame.SRCALPHA)
            cx, cy = 150, 150
            scores = [s1, s2, s3]
            pts = []
            for i, sc in enumerate(scores):
                ang = -90 + i * 120
                rad = math.radians(ang)
                r = (sc / 10) * RADIUS * score_progress
                pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
            pygame.draw.polygon(surf, SCORE_COLOR, pts)
            pygame.draw.polygon(surf, SCORE_EDGE_COLOR, pts, 2)
            screen.blit(surf, (center[0] - 150, center[1] - 150))

        draw_score_triangle(CENTER_L, score_dynamic_1P, score_stable_1P, score_unique_1P)
        draw_score_triangle(CENTER_R, score_dynamic_2P, score_stable_2P, score_unique_2P)

    # 下テキスト
    for side in bottom:
        x0 = bottom[side]["x"]
        y0 = bottom[side]["y"]

        for i, surf in enumerate(bottom[side]["label_surfs"]):
            screen.blit(surf, (x0, y0 + i * 30))

        for i, surf in enumerate(bottom[side]["scores"]):
            screen.blit(surf, (x0 + 150, y0 + i * 30))

        if step >= STEP_TOTAL_SCORE:
            total = bottom[side]["total_now"]
            total_text = f"{total:02d}"

            if side == "L":
                total_surf = render_outline(total_text, font_total, (255,255,255), (255,80,80))
            else:
                total_surf = render_outline(total_text, font_total, (255,255,255), (80,80,255))

            screen.blit(total_surf, (x0 + 220, y0 + 0))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
