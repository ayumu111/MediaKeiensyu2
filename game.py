import pygame, sys, os, time

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Score Meter (Sequential Animation)")
clock = pygame.time.Clock()

# --- フォント設定 ---
font_path1 = "IoEI.ttf" # タイトル用（フィバ字フォント）
font_path2 = "C:/Windows/Fonts/msgothic.ttc" # スコア用（標準フォント）

try:
    score_font = pygame.font.Font(font_path2, 20)
    title_font = pygame.font.Font(font_path1, 80)
    print(f"成功: フォント読み込み完了。")
except FileNotFoundError as e:
    print(f"エラー: フォントファイルが見つかりません: {e}")
    score_font = pygame.font.SysFont("arial", 20)
    title_font = pygame.font.SysFont("arial", 80, bold=True)
except Exception as e:
    print(f"フォント読み込みエラー: {e}")
    score_font = pygame.font.SysFont(None, 20)
    title_font = pygame.font.SysFont(None, 80)

# 各回の上限値
SEGMENT_LIMITS = [100.0, 100.0, 300.0]

# --- 変更点: 初期値を0にする（タイトルが終わるまで待機するため）---
current_red_segs = [0.0, 0.0, 0.0]
current_blue_segs = [0.0, 0.0, 0.0]
# 目標値は設定ファイルから読むのでとりあえず初期値を入れておく
target_red_segs = [80.0, 90.0, 150.0]
target_blue_segs = [50.0, 50.0, 100.0]

ANIM_SPEED = 180.0
SCORES_FILE = "scores.txt"
READ_INTERVAL = 0.5
_last_read = 0.0

# --- 変更点: タイトルアニメーション用の変数を準備 ---
TITLE_STR = "けっかはっぴょう"
TITLE_TARGET_Y = 30
TITLE_START_Y = -150.0
TITLE_EASING = 0.12  # 個別落下なので少しキビキビさせる
CHAR_DROP_DELAY = 0.15 # 文字ごとの落下遅延時間（秒）
START_DELAY = 0.5      # 開始までのタメ時間（秒）

title_chars = []
# 全体の幅を計算して中央揃えの開始X座標を求める
total_width = title_font.size(TITLE_STR)[0]
current_char_x = WIDTH // 2 - total_width // 2
start_time_base = time.time() + START_DELAY

for i, char in enumerate(TITLE_STR):
    char_surf = title_font.render(char, True, pygame.Color("WHITE"))
    # 各文字のデータを辞書で管理
    title_chars.append({
        'surf': char_surf,
        'tx': current_char_x,        # 目標X座標
        'cy': TITLE_START_Y,         # 現在のY座標
        'start_time': start_time_base + i * CHAR_DROP_DELAY+0.1*i, # 落下開始時刻
        'finished': False            # 落下完了フラグ
    })
    # 次の文字のX座標へ（文字幅分ずらす）
    current_char_x += char_surf.get_width()

# タイトルアニメーション完了フラグ
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

def draw_stacked_meter(x, y, w, h, segs, colors, border_color):
    pygame.draw.rect(screen, pygame.Color("WHITE"), (x-10, y-10, w+20, h+20))
    pygame.draw.rect(screen, border_color, (x, y, w, h))
    
    total_max = 500.0
    x0 = x + 4
    inner_w = w - 8
    
    for v, col in zip(segs, colors):
        safe_v = max(0.0, v)
        seg_w = int((safe_v / total_max) * inner_w)
        if seg_w > 0:
            pygame.draw.rect(screen, col, (x0, y+4, seg_w, h-8))
            x0 += seg_w
            
    total = sum(segs)
    pct = int(round((total / total_max) * 100))
    txt = score_font.render(f"{int(round(total))} / 500 ({pct}%)", True, pygame.Color("BLACK"))
    screen.blit(txt, (x + w + 12, y + h//2 - txt.get_height()//2))

RED_COLS = [pygame.Color(255,140,140), pygame.Color(255,80,80), pygame.Color(180,0,0)]
BLUE_COLS = [pygame.Color(160,200,255), pygame.Color(80,160,255), pygame.Color(0,80,200)]

# --- メインループ ---
while True:
    dt = clock.tick(30) / 1000.0
    current_time = time.time()
    try_read_scores_file()

    # --- 変更点: タイトルアニメーションの更新 ---
    all_chars_finished = True
    for char_data in title_chars:
        # 開始時間が来ていたらアニメーション
        if current_time >= char_data['start_time']:
            dist_y = TITLE_TARGET_Y - char_data['cy']
            if dist_y > 0.5:
                char_data['cy'] += dist_y * TITLE_EASING
                all_chars_finished = False # まだ動いている文字がある
            else:
                char_data['cy'] = TITLE_TARGET_Y
                char_data['finished'] = True
        else:
             all_chars_finished = False # まだ開始していない文字がある
    
    # 全ての文字が完了したらフラグを立てる
    if all_chars_finished:
        title_animation_done = True

    # --- 変更点: メーターのアニメーション更新（タイトル完了後のみ） ---
    if title_animation_done:
        current_red_segs = step_toward_list(current_red_segs, target_red_segs, dt)
        current_blue_segs = step_toward_list(current_blue_segs, target_blue_segs, dt)

    # 描画開始
    screen.fill((45,124,124))

    # --- 変更点: タイトル各文字の描画 ---
    for char_data in title_chars:
        screen.blit(char_data['surf'], (char_data['tx'], char_data['cy']))
    
    # メーター描画
    draw_stacked_meter(100, 200, 600, 80, current_red_segs, RED_COLS, pygame.Color("BLACK"))
    draw_stacked_meter(100, 300, 600, 80, current_blue_segs, BLUE_COLS, pygame.Color("BLACK"))

    # アイコン描画
    pygame.draw.circle(screen, RED_COLS[-1], (50, 240), 40)
    pygame.draw.circle(screen, BLUE_COLS[-1], (50, 340), 40)

    pygame.display.update()

    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        # メーターアニメーション中もキー操作は受け付けるようにしています
        # もしタイトルアニメーション中は操作無効にしたい場合は、
        # ここにも `if title_animation_done:` を追加してください。
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