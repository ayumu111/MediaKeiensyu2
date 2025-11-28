import pygame, sys, os, time

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Score Meter (Overlay Text)")
clock = pygame.time.Clock()

# --- フォント設定 ---
font_path1 = "IoEI.ttf" # タイトル用（フィバ字フォント）
# font_path2 = "C:/Windows/Fonts/msgothic.ttc" # スコア用（標準フォント）
font_path2 = "Paintball_Beta_3.ttf"

try:
    # スコア用フォントを少し大きくして見やすくします (20 -> 24)
    score_font = pygame.font.Font(font_path2, 24)
    title_font = pygame.font.Font(font_path1, 80)
    print(f"成功: フォント読み込み完了。")
except FileNotFoundError as e:
    print(f"エラー: フォントファイルが見つかりません: {e}")
    score_font = pygame.font.SysFont("arial", 24, bold=True)
    title_font = pygame.font.SysFont("arial", 80, bold=True)
except Exception as e:
    print(f"フォント読み込みエラー: {e}")
    score_font = pygame.font.SysFont(None, 24)
    title_font = pygame.font.SysFont(None, 80)

# 各回の上限値
SEGMENT_LIMITS = [100.0, 100.0, 300.0]

# --- 初期値を0にする ---
current_red_segs = [0.0, 0.0, 0.0]
current_blue_segs = [0.0, 0.0, 0.0]
target_red_segs = [80.0, 90.0, 150.0]
target_blue_segs = [50.0, 50.0, 100.0]

ANIM_SPEED = 180.0
SCORES_FILE = "scores.txt"
READ_INTERVAL = 0.5
_last_read = 0.0

# --- タイトルアニメーション用の変数 ---
TITLE_STR = "けっかはっぴょう"
TITLE_TARGET_Y = 30
TITLE_START_Y = -150.0
TITLE_EASING = 0.12
CHAR_DROP_DELAY = 0.15
START_DELAY = 0.5

title_chars = []
total_width = title_font.size(TITLE_STR)[0]
current_char_x = WIDTH // 2 - total_width // 2
start_time_base = time.time() + START_DELAY

for i, char in enumerate(TITLE_STR):
    char_surf = title_font.render(char, True, pygame.Color("WHITE"))
    title_chars.append({
        'surf': char_surf,
        'tx': current_char_x,
        'cy': TITLE_START_Y,
        'start_time': start_time_base + i * CHAR_DROP_DELAY+0.1*i,
        'finished': False
    })
    current_char_x += char_surf.get_width()

title_animation_done = False


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

# --- 変更点: 描画順序を変更し、テキストをバーの上に重ねる ---
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
    # 文字色を WHITE に変更
    txt = score_font.render(f"{int(round(total))} / 500 ({pct}%)", True, pygame.Color("WHITE"))
    
    # テキストの描画位置：バーの開始位置付近（少し右にずらす）に設定して重ねる
    text_x = x + 20
    # 上下中央揃え
    text_y = y + h//2 - txt.get_height()//2
    
    # テキストの影（任意：視認性を上げるため黒い影を少しずらして描画）
    shadow_txt = score_font.render(f"{int(round(total))} / 500 ({pct}%)", True, pygame.Color("BLACK"))
    screen.blit(shadow_txt, (text_x + 2, text_y + 2))
    
    # 白いテキスト本体を描画
    screen.blit(txt, (text_x, text_y))


RED_COLS = [pygame.Color(255,140,140), pygame.Color(255,80,80), pygame.Color(180,0,0)]
BLUE_COLS = [pygame.Color(160,200,255), pygame.Color(80,160,255), pygame.Color(0,80,200)]

# --- メインループ ---
while True:
    dt = clock.tick(30) / 1000.0
    current_time = time.time()
    try_read_scores_file()

    # --- タイトルアニメーションの更新 ---
    all_chars_finished = True
    for char_data in title_chars:
        if current_time >= char_data['start_time']:
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

    # 描画開始
    screen.fill((45,124,124))

    # --- タイトル各文字の描画 ---
    for char_data in title_chars:
        screen.blit(char_data['surf'], (char_data['tx'], char_data['cy']))
    
    # --- メーターの描画 ---
    meter_width = 680
    draw_stacked_meter(100, 200, meter_width, 80, current_red_segs, RED_COLS, pygame.Color("BLACK"))
    draw_stacked_meter(100, 300, meter_width, 80, current_blue_segs, BLUE_COLS, pygame.Color("BLACK"))

    # アイコン描画
    pygame.draw.circle(screen, RED_COLS[-1], (45, 240), 40)
    pygame.draw.circle(screen, BLUE_COLS[-1], (45, 350), 40)

    pygame.display.update()

    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        elif event.type == pygame.KEYDOWN:
            change = 15.0 / 3.0
            if event.key == pygame.K_r:
                target_red_segs = [clamp_val(v + change, SEGMENT_LIMITS[i]) for i, v in enumerate(target_red_segs)]
            elif event.key == pygame.K_f:
                target_red_segs = [clamp_val(v - change, SEGMENT_LIMITS[i]) for i, v in enumerate(target_red_segs)]
            elif event.key == pygame.K_b:
                target_blue_segs = [clamp_val(v + change, SEGMENT_LIMITS[i]) for i, v in enumerate(target_blue_segs)]
            elif event.key == pygame.K_v:
                target_blue_segs = [clamp_val(v - change, SEGMENT_LIMITS[i]) for i, v in enumerate(target_blue_segs)]