import pygame
import math
pygame.init()

screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# ==================================================
# 設定
# ==================================================
images = ["img1.png", "img2.png", "img3.png"]
n = len(images)

# 画像読み込み
loaded_images = [pygame.image.load(path).convert_alpha() for path in images]

# 余白ありの初期表示
margin = 60
slot_width = (800 - margin * 2) // n
slot_height = 400
top_y = 100
normal_size = (slot_width, slot_height)

# 縮小サイズ
shrink_factor = 0.85
shrink_size = (int(normal_size[0]*shrink_factor), int(normal_size[1]*shrink_factor))

# 画面いっぱいの最終表示（横均等割り）
full_width = 800 // n
full_height = 600
full_size = (full_width, full_height)

# ==================================================
# 斜め線
# ==================================================
angle_rad = math.radians(45)
belt_width = 3
expand_speed_line = 20

# ==================================================
# フェーズ管理
# ==================================================
phase = "expand"
hold_time = 1000
shrink_duration = 100
pause_after_shrink = 100   # ←追加：縮んだ後の一瞬停止
expand_duration = 100

phase_timer = 0

# 日本語対応フォント
font = pygame.font.Font("C:/Windows/Fonts/meiryo.ttc", 72)
win_text = font.render("player1の勝利!", True, (255, 0, 0))
win_rect = win_text.get_rect(center=(400, 300))

running = True
while running:
    dt = clock.tick(60)
    phase_timer += dt
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ===================================================
    # ① 斜め線フェーズ
    # ===================================================
    if phase == "expand":
        screen.fill((0, 0, 0))
        belt_width += expand_speed_line
        if belt_width >= 1300:
            belt_width = 1300
            phase = "show_hold"
            phase_timer = 0

        cx, cy = 400, 300
        dx = math.cos(angle_rad)
        dy = math.sin(angle_rad)
        px = -dy
        py = dx
        hw = belt_width / 2

        p1 = (cx + px*hw + dx*1200, cy + py*hw + dy*1200)
        p2 = (cx - px*hw + dx*1200, cy - py*hw + dy*1200)
        p3 = (cx - px*hw - dx*1200, cy - py*hw - dy*1200)
        p4 = (cx + px*hw - dx*1200, cy + py*hw - dy*1200)

        pygame.draw.polygon(screen, (255, 255, 255), [p1, p2, p3, p4])

    # ===================================================
    # ② 画像を余白を残して表示 → 固定
    # ===================================================
    elif phase == "show_hold":
        screen.fill((255, 255, 255))

        for i in range(n):
            img = loaded_images[i]
            img_s = pygame.transform.smoothscale(img, normal_size)
            x = margin + slot_width * i + (slot_width - normal_size[0]) // 2
            y = top_y
            screen.blit(img_s, (x, y))

        if phase_timer >= hold_time:
            phase = "shrink"
            phase_timer = 0

    # ===================================================
    # ③ 0.3秒で縮む
    # ===================================================
    elif phase == "shrink":
        screen.fill((255, 255, 255))

        t = min(phase_timer / shrink_duration, 1)
        cur_w = int(normal_size[0] + (shrink_size[0] - normal_size[0]) * t)
        cur_h = int(normal_size[1] + (shrink_size[1] - normal_size[1]) * t)

        for i in range(n):
            img_s = pygame.transform.smoothscale(loaded_images[i], (cur_w, cur_h))
            x = margin + slot_width*i + (slot_width - cur_w)//2
            y = top_y + (slot_height - cur_h)//2
            screen.blit(img_s, (x, y))

        if phase_timer >= shrink_duration:
            phase = "pause"
            phase_timer = 0

    # ===================================================
    # ④ 縮んだ後の「一瞬停止」
    # ===================================================
    elif phase == "pause":
        screen.fill((255, 255, 255))

        # 縮小後の状態を維持
        for i in range(n):
            img_s = pygame.transform.smoothscale(loaded_images[i], shrink_size)
            x = margin + slot_width*i + (slot_width - shrink_size[0])//2
            y = top_y + (slot_height - shrink_size[1])//2
            screen.blit(img_s, (x, y))

        if phase_timer >= pause_after_shrink:
            phase = "expand_images"
            phase_timer = 0

    # ===================================================
    # ⑤ 0.2秒で一気に画面いっぱいに拡大＋勝利表示
    # ===================================================
    elif phase == "expand_images":
        screen.fill((255, 255, 255))

        t = min(phase_timer / expand_duration, 1)
        cur_w = int(shrink_size[0] + (full_size[0] - shrink_size[0]) * t)
        cur_h = int(shrink_size[1] + (full_size[1] - shrink_size[1]) * t)

        for i in range(n):
            img_s = pygame.transform.smoothscale(loaded_images[i], (cur_w, cur_h))
            x = full_width * i + (full_width - cur_w) // 2
            y = (full_height - cur_h) // 2
            screen.blit(img_s, (x, y))

        # 勝利メッセージ
        screen.blit(win_text, win_rect)

        if phase_timer >= expand_duration:
            phase = "done"

    # ===================================================
    # ⑥ 完了フェーズ：画面いっぱいのまま固定
    # ===================================================
    elif phase == "done":
        screen.fill((255, 255, 255))

        for i in range(n):
            img_s = pygame.transform.smoothscale(loaded_images[i], full_size)
            x = full_width * i
            y = 0
            screen.blit(img_s, (x, y))

        screen.blit(win_text, win_rect)

    pygame.display.flip()

pygame.quit()