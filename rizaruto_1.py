import pygame
import math
import random
pygame.init()

screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# ==================================================
# 設定
# ==================================================
images = ["img1.png", "img2.png", "img3.png"]  # 使用する画像
n = len(images)

# 画像読み込み
loaded_images = [pygame.image.load(path).convert() for path in images]

slot_width = 800 // n

resized_images = [
    pygame.transform.scale(img, (slot_width, 600)) for img in loaded_images
]

slide_y = [-600 for _ in range(n)]
slide_speed = 20
delay_interval = 300
delay_timer = 0
current_img = 0

# ==================================================
# 斜め線設定
# ==================================================
angle_deg = 45
angle_rad = math.radians(angle_deg)

initial_width = 3
belt_width = initial_width
expand_speed = 20

phase = "expand"

# ★★★ 日本語フォントを正しく表示するための修正 ★★★
# font = pygame.font.Font("C:/Windows/Fonts/meiryo.ttc", 80)
font = pygame.font.Font("C:/Windows/Fonts/YuGothB.ttc", 80)
victory_text = font.render("player1の勝利！", True, (255, 0, 0))
text_rect = victory_text.get_rect(center=(400, 300))

running = True
while running:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ------------------------------------------------------
    # ① 斜め線（白）で広がる
    # ------------------------------------------------------
    if phase == "expand":
        screen.fill((0, 0, 0))

        belt_width += expand_speed
        if belt_width >= 1300:
            belt_width = 1300
            phase = "slide_in"

        line_color = (255, 255, 255)

        cx, cy = 400, 300
        dx = math.cos(angle_rad)
        dy = math.sin(angle_rad)

        px = -dy
        py = dx

        hw = belt_width / 2

        p1 = (cx + px * hw + dx * 1200, cy + py * hw + dy * 1200)
        p2 = (cx - px * hw + dx * 1200, cy - py * hw + dy * 1200)
        p3 = (cx - px * hw - dx * 1200, cy - py * hw - dy * 1200)
        p4 = (cx + px * hw - dx * 1200, cy + py * hw - dy * 1200)

        pygame.draw.polygon(screen, line_color, [p1, p2, p3, p4])

    # ------------------------------------------------------
    # ② スライドイン画像 + 白枠線 + 勝利メッセージ
    # ------------------------------------------------------
    elif phase == "slide_in":
        screen.fill((255, 255, 255))

        delay_timer += dt
        if current_img < n and delay_timer >= delay_interval:
            current_img += 1
            delay_timer = 0

        for i in range(current_img):
            if slide_y[i] < 0:
                slide_y[i] += slide_speed
                if slide_y[i] > 0:
                    slide_y[i] = 0

            x = slot_width * i
            screen.blit(resized_images[i], (x, slide_y[i]))

        # 枠線（白）
        border_width = 8
        border_color = (255, 255, 255)
        pygame.draw.rect(screen, border_color, (0, 0, 800, 600), border_width)

        # スライドインが完了したら勝利メッセージを表示
        if current_img == n and all(y == 0 for y in slide_y):
            screen.blit(victory_text, text_rect)

    pygame.display.flip()

pygame.quit()