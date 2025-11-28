import pygame, sys, os, time

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Score Meter (Title with Shadow)")
clock = pygame.time.Clock()

# --- フォント設定 ---
# font_path1 = "IoEI.ttf" # タイトル用
font_path2 = "Paintball_Beta_3.ttf" # スコア＆Winner用
font_path1 = "Splatfont2.ttf" # タイトル用
#font_path2 = "Splatfont2.ttf" # スコア＆Winner用
try:
    score_font = pygame.font.Font(font_path2, 24)
    title_font = pygame.font.Font(font_path1, 80)
    winner_font = pygame.font.Font(font_path2, 80)
    print(f"成功: フォント読み込み完了。")
except FileNotFoundError as e:
    print(f"エラー: フォントファイルが見つかりません: {e}")
    score_font = pygame.font.SysFont("arial", 24, bold=True)
    title_font = pygame.font.SysFont("arial", 80, bold=True)
    winner_font = pygame.font.SysFont("arial", 80, bold=True)
except Exception as e:
    print(f"フォント読み込みエラー: {e}")
    score_font = pygame.font.SysFont(None, 24)
    title_font = pygame.font.SysFont(None, 80)

# 各回の上限値
SEGMENT_LIMITS = [100.0, 100.0, 300.0]

# --- 初期値 ---
current_red_segs = [0.0, 0.0, 0.0]
current_blue_segs = [0.0, 0.0, 0.0]
target_red_segs = [80.0, 90.0, 150.0]
target_blue_segs = [50.0, 50.0, 100.0]

ANIM_SPEED = 180.0
SCORES_FILE = "scores.txt"
READ_INTERVAL = 0.5
_last_read = 0.0

# --- タイトルアニメーション用の変数 ---
TITLE_STR = "けっかはっぴょう！！"
TITLE_TARGET_Y = 50
TITLE_START_Y = -130.0
TITLE_EASING = 0.12
CHAR_DROP_DELAY = 0.15
START_DELAY = 0.5

# --- タイトルの色定義 ---
TITLE_COLOR_MAIN = pygame.Color("YELLOW")
TITLE_COLOR_OUTLINE = pygame.Color(30, 80, 220)
# 追加: 影の色
TITLE_COLOR_SHADOW = pygame.Color("BLACK")

title_chars = []
total_width = title_font.size(TITLE_STR)[0]
current_char_x = WIDTH // 2 - total_width // 2
start_time_base = time.time() + START_DELAY

for i, char in enumerate(TITLE_STR):
    # メインの文字（黄色）
    main_surf = title_font.render(char, True, TITLE_COLOR_MAIN)
    # 縁取り用の文字（青色）
    outline_surf = title_font.render(char, True, TITLE_COLOR_OUTLINE)
    # 追加: 影用の文字（黒色）
    shadow_surf = title_font.render(char, True, TITLE_COLOR_SHADOW)
    
    title_chars.append({
        'main_surf': main_surf,
        'outline_surf': outline_surf,
        'shadow_surf': shadow_surf, # 追加
        'tx': current_char_x,
        'cy': TITLE_START_Y,
        'start_time': start_time_base + i * CHAR_DROP_DELAY+0.1*i,
        'finished': False
    })
    current_char_x += main_surf.get_width()

title_animation_done = False

# --- Winner表示用の変数 ---
WINNER_STR = "Winner1P"
winner_surf = winner_font.render(WINNER_STR, True, pygame.Color("YELLOW"))
winner_shadow = winner_font.render(WINNER_STR, True, pygame.Color("BLACK"))
winner_rect = winner_surf.get_rect(center=(WIDTH // 2 - 30, 480))

# --- ドットアニメーション用の変数 ---
DOT_STR = "."
dot_surf = winner_font.render(DOT_STR, True, pygame.Color("YELLOW"))
dot_shadow = winner_font.render(DOT_STR, True, pygame.Color("BLACK"))
dot_width = dot_surf.get_width()

show_winner = False
dot_count = 0
dot_timer = 0
DOT_INTERVAL = 500


def clamp_val(v, limit):
    return max(0.0, min(limit, v))

def try_read_scores_file():
    global target_red_segs, target_blue_segs, _last_read
    now = time.time()
    if now - _last_read < READ_INTERVAL:
        return
    _last_read = now
    if not os.path.exists(SCORES_FILE):
        return
    try:
        s = open(SCORES_FILE, "r", encoding="utf-8").read().strip()
        if not s:
            return
        parts = [p.strip() for p in s.replace("\t", ",").replace(" ", ",").split(",") if p.strip()!=""]
        
        if len(parts) >= 6:
            r = []
            b = []
            for i in range(3):
                r.append(clamp_val(float(parts[i]), SEGMENT_LIMITS[i]))
                b.append(clamp_val(float(parts[i+3]), SEGMENT_LIMITS[i]))
            target_red_segs = r
            target_blue_segs = b
        elif len(parts) >= 3:
            r = []
            for i in range(3):
                r.append(clamp_val(float(parts[i]), SEGMENT_LIMITS[i]))
            target_red_segs = r
        elif len(parts) >= 1:
            val = float(parts[0]) / 3.0
            r = []
            for i in range(3):
                r.append(clamp_val(val, SEGMENT_LIMITS[i]))
            target_red_segs = r
    except Exception as e:
        print("scores.txt parse error:", e)

def step_toward_list(curr_list, target_list, dt):
    out = []
    maxstep = ANIM_SPEED * dt
    for c, t in zip(curr_list, target_list):
        diff = t - c
        if abs(diff) <= maxstep:
            out.append(t)
        else:
            out.append(c + (maxstep if diff > 0 else -maxstep))
    return out

def are_segs_reached(curr, targ):
    tolerance = 0.5 
    for c, t in zip(curr, targ):
        if abs(c - t) > tolerance:
            return False
    return True

def draw_stacked_meter(x, y, w, h, segs, colors, border_color):
    # 1. 背景枠と枠線を描画
    pygame.draw.rect(screen, pygame.Color("WHITE"), (x-10, y-10, w+20, h+20))
    pygame.draw.rect(screen, border_color, (x, y, w, h))
    
    total_max = 500.0
    
    # バーの描画開始位置を枠の左端に戻す
    bar_start_x = x + 4
    # バーが使える幅（左右の余白4pxずつを引く）
    inner_w = w - 8
    
    current_bar_x = bar_start_x
    
    # 2. 色付きバーを先に描画する
    for v, col in zip(segs, colors):
        safe_v = max(0.0, v)
        seg_w = int((safe_v / total_max) * inner_w)
        if seg_w > 0:
            pygame.draw.rect(screen, col, (current_bar_x, y+4, seg_w, h-8))
            current_bar_x += seg_w

    # 3. スコアテキストを白色でレンダリングし、バーの上に重ねて描画する
    total = sum(segs)
    pct = int(round((total / total_max) * 100))
    # 文字色を WHITE に設定
    txt = score_font.render(f"{int(round(total))} / 500 ({pct}%)", True, pygame.Color("WHITE"))
    
    # テキストの描画位置：バーの開始位置付近（少し右にずらす）に設定して重ねる
    text_x = x + 20
    # 上下中央揃え
    text_y = y + h//2 - txt.get_height()//2
    
    # テキストの影（黒）を描画
    shadow_txt = score_font.render(f"{int(round(total))} / 500 ({pct}%)", True, pygame.Color("BLACK"))
    screen.blit(shadow_txt, (text_x + 2, text_y + 2))
    
    # 白いテキスト本体を描画
    screen.blit(txt, (text_x, text_y))

RED_COLS = [pygame.Color(255,140,140), pygame.Color(255,80,80), pygame.Color(180,0,0)]
BLUE_COLS = [pygame.Color(160,200,255), pygame.Color(80,160,255), pygame.Color(0,80,200)]

# --- メインループ ---
while True:
    dt = clock.tick(30) / 1000.0
    current_time_sec = time.time()
    current_ticks = pygame.time.get_ticks()
    try_read_scores_file()

    # --- タイトルアニメーションの更新 ---
    all_chars_finished = True
    for char_data in title_chars:
        if current_time_sec >= char_data['start_time']:
            dist_y = TITLE_TARGET_Y - char_data['cy']
            if dist_y > 0.5:
                char_data['cy'] += dist_y * TITLE_EASING
                all_chars_finished = False
            else:
                char_data['cy'] = TITLE_TARGET_Y
                char_data['finished'] = True
        else:
             all_chars_finished = False
    
    if all_chars_finished:
        title_animation_done = True

    # --- メーターのアニメーション更新 ---
    if title_animation_done:
        current_red_segs = step_toward_list(current_red_segs, target_red_segs, dt)
        current_blue_segs = step_toward_list(current_blue_segs, target_blue_segs, dt)

        # --- すべてのアニメーションが完了したかチェック ---
        if not show_winner:
            red_done = are_segs_reached(current_red_segs, target_red_segs)
            blue_done = are_segs_reached(current_blue_segs, target_blue_segs)
            if red_done and blue_done:
                show_winner = True
                dot_count = 0
                dot_timer = current_ticks
        
        # --- ドットを増やすロジック ---
        if show_winner and dot_count < 3:
            if current_ticks - dot_timer > DOT_INTERVAL:
                dot_count += 1
                dot_timer = current_ticks

    # 描画開始
    screen.fill((22,155,155))

    # --- 変更点: タイトル各文字の描画（影＋縁取り＋メイン） ---
    for char_data in title_chars:
        cx, cy = char_data['tx'], char_data['cy']
        out_surf = char_data['outline_surf']
        main_surf = char_data['main_surf']
        shadow_surf = char_data['shadow_surf'] # 追加
        
        # 1. 影を描画（少し右下にずらす）
        shadow_offset = 4
        screen.blit(shadow_surf, (cx + shadow_offset, cy + shadow_offset))

        # 2. 縁取り（上下左右にずらして描画）
        offset = 3 # 縁取りの太さ
        screen.blit(out_surf, (cx - offset, cy))
        screen.blit(out_surf, (cx + offset, cy))
        screen.blit(out_surf, (cx, cy - offset))
        screen.blit(out_surf, (cx, cy + offset))
        
        # 3. メインの文字（中央に描画）
        screen.blit(main_surf, (cx, cy))
    
    # --- メーターの描画 ---
    meter_width = 680
    draw_stacked_meter(100, 200, meter_width, 80, current_red_segs, RED_COLS, pygame.Color("BLACK"))
    draw_stacked_meter(100, 300, meter_width, 80, current_blue_segs, BLUE_COLS, pygame.Color("BLACK"))

    # アイコン描画
    pygame.draw.circle(screen, (255,0,0), (45, 240), 40)
    pygame.draw.circle(screen, (0,0,255), (45, 350), 40)

    # --- Winnerテキストとドットの描画 ---
    if show_winner:
        screen.blit(winner_shadow, (winner_rect.x + 4, winner_rect.y + 4))
        screen.blit(winner_surf, winner_rect)
        
        base_dot_x = winner_rect.right + 5
        for i in range(dot_count):
            dot_x = base_dot_x + i * (dot_width * 0.7) 
            dot_y = winner_rect.y
            screen.blit(dot_shadow, (dot_x + 4, dot_y + 4))
            screen.blit(dot_surf, (dot_x, dot_y))

    pygame.display.update()

    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        elif event.type == pygame.KEYDOWN:
            show_winner = False 
            dot_count = 0
            change = 15.0 / 3.0
            if event.key == pygame.K_r:
                target_red_segs = [clamp_val(v + change, SEGMENT_LIMITS[i]) for i, v in enumerate(target_red_segs)]
            elif event.key == pygame.K_f:
                target_red_segs = [clamp_val(v - change, SEGMENT_LIMITS[i]) for i, v in enumerate(target_red_segs)]
            elif event.key == pygame.K_b:
                target_blue_segs = [clamp_val(v + change, SEGMENT_LIMITS[i]) for i, v in enumerate(target_blue_segs)]
            elif event.key == pygame.K_v:
                target_blue_segs = [clamp_val(v - change, SEGMENT_LIMITS[i]) for i, v in enumerate(target_blue_segs)]