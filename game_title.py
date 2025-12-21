
import pygame
import sys
import math
import random
import os
import pygame

# ========== 設定 ==========
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60

# ===== 追加（設定）=====
# 好きなフォントファイルを指定（拡張子 .ttf / .otf）
CUSTOM_FONT_PATH = "title/Paintball_Beta_3.ttf"   # 例：同じフォルダに置いた場合
FONT_SIZE = 36                    # 文字サイズ
TEXT_COLOR = (255, 255, 255)
TEXT_SHADOW = (0, 0, 0)
TEXT_DELAY_MS = 3000  # タイトル開始から4秒後に表示開始

# ===== フォントのロード =====
def load_font_safely(path: str, size: int):
    """
    指定フォントが見つからない場合はデフォルトにフォールバックする。
    """
    if os.path.isfile(path):
        try:
            return pygame.font.Font(path, size)
        except Exception as e:
            print(f"[WARN] フォントの読み込みに失敗: {e}. デフォルトフォントに切り替えます。")
    else:
        print(f"[WARN] フォントファイルが見つかりません: {path}. デフォルトフォントを使用します。")
    return pygame.font.Font(None, size)



# 演出のタイミング（ミリ秒）
LOGO_DELAY_MS = 1000   # 背景の後、ロゴが出るまで
CHARS_DELAY_MS = 2000  # ロゴの後、キャラが出るまで
FADE_MS = 800          # ロゴ・キャラのフェードイン時間

# 攻撃ループ設定（ミリ秒）
ATTACK_CYCLE_MS = 1200   # 1攻撃サイクルの長さ
ATTACK_PEAK_MS = 600     # 突進ピーク（ヒット）のタイミング
DASH_AMPLITUDE = 24      # 前後移動の振幅（px）
SHAKE_DURATION_MS = 180  # 画面シェイクの持続時間
SHAKE_INTENSITY = 4      # 画面シェイクの強さ（px）

# テキスト表示
FONT_NAME = None  # デフォルトフォント
TEXT_COLOR = (255, 196, 70)
TEXT_SHADOW = (0, 0, 0)

# 画像ファイル名（必要に応じて変更）
BACKGROUND_IMG = "title/background.PNG"
TITLE_LOGO_IMG = "title/logo.PNG"
CHAR1_IMG = "title/chara1_shadow.PNG"
CHAR2_IMG = "title/chara2_shadow.PNG"

# 追加する定数（好みに応じて調整）
HIT_SPARK_IMG = "title/spark.png"
HIT_SPARK_SCALE = 0.5        # 画像の拡大率（1.0で原寸）
HIT_SPARK_DURATION_MS = 120  # 表示時間（ms）
HIT_SPARK_ALPHA = 220        # 不透明度（0-255）


# ==========================

def load_scaled_image(path, max_w=None, max_h=None):
    """画像を読み込み、必要なら最大サイズに収まるように等比スケーリングして返す。"""
    img = pygame.image.load(path).convert_alpha()
    if max_w is None and max_h is None:
        return img
    w, h = img.get_size()
    scale = 1.0
    if max_w is not None:
        scale = min(scale, max_w / w)
    if max_h is not None:
        scale = min(scale, max_h / h)
    if scale < 1.0:
        img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
    return img



def blit_fade(surface, img, pos, start_ms, now_ms, fade_ms):
    """start_msからfade_msの間でフェードイン（アルファ）しながら描画。"""
    if now_ms < start_ms:
        return
    alpha = 255
    elapsed = now_ms - start_ms
    if elapsed < fade_ms:
        alpha = int(255 * (elapsed / fade_ms))
    temp = img.copy()
    temp.set_alpha(alpha)
    surface.blit(temp, pos)



def draw_text_center(surface, text, font, y, color=(255,255,255), shadow=(0,0,0)):
    """中央寄せテキスト（ドロップシャドウ付き）。"""
    render = font.render(text, True, color)
    shadow_r = font.render(text, True, shadow)
    x = SCREEN_WIDTH // 2
    rect = render.get_rect(center=(x, y))
    shadow_rect = shadow_r.get_rect(center=(x+1, y+1))
    surface.blit(shadow_r, shadow_rect)
    surface.blit(render, rect)

def main():
    pygame.init()
    pygame.display.set_caption("Title Screen Example")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    # main() の中で
    font = load_font_safely(CUSTOM_FONT_PATH, FONT_SIZE)

    # フォント
    #font = pygame.font.Font(FONT_NAME, 24)

    # 画像読み込み＆スケーリング
    try:
        bg_img = load_scaled_image(BACKGROUND_IMG, SCREEN_WIDTH, SCREEN_HEIGHT)
    except Exception as e:
        print(f"[ERROR] 背景画像の読み込みに失敗: {e}")
        pygame.quit()
        sys.exit(1)
    try:
        logo_img = load_scaled_image(TITLE_LOGO_IMG, max_w=SCREEN_WIDTH, max_h=SCREEN_HEIGHT//1.05)
    except Exception as e:
        print(f"[ERROR] ロゴ画像の読み込みに失敗: {e}")
        pygame.quit()
        sys.exit(1)
    try:
        char1_img = load_scaled_image(CHAR1_IMG, max_w=SCREEN_WIDTH//1, max_h=SCREEN_HEIGHT//1.1)
        char2_img = load_scaled_image(CHAR2_IMG, max_w=SCREEN_WIDTH//1, max_h=SCREEN_HEIGHT//1.1)
    except Exception as e:
        print(f"[ERROR] キャラ画像の読み込みに失敗: {e}")
        pygame.quit()
        sys.exit(1)
    
    # 画像読み込み（ロゴ・キャラ読み込みの近くに）
    try:
        hit_spark_img = pygame.image.load(HIT_SPARK_IMG).convert_alpha()
        # 拡大縮小（必要なら）
        if HIT_SPARK_SCALE != 1.0:
            w, h = hit_spark_img.get_size()
            hit_spark_img = pygame.transform.smoothscale(
                hit_spark_img, (int(w * HIT_SPARK_SCALE), int(h * HIT_SPARK_SCALE))
            )
    except Exception as e:
        print(f"[WARN] 火花画像の読み込みに失敗: {e}")
        hit_spark_img = None


    # 背景は画面サイズに合わせる
    bg_img = pygame.transform.smoothscale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # ロゴ位置（上部中央）
    logo_rect = logo_img.get_rect(midtop=(SCREEN_WIDTH//2, 20))

    # キャラの基準位置（下部左右）
    char1_rect = char1_img.get_rect()
    char2_rect = char2_img.get_rect()
    # 左右に配置、床から少し上げる
    floor_y = SCREEN_HEIGHT - 60
    char1_rect.midbottom = (SCREEN_WIDTH*3//7, floor_y+40)
    char2_rect.midbottom = (SCREEN_WIDTH*4//7, floor_y+40)

    # 攻撃演出用
    start_time_ms = pygame.time.get_ticks()
    shake_until_ms = 0

    
    # 火花の表示状態（Noneなら未表示）
    hit_spark_until_ms = 0
    hit_spark_pos = (0, 0)  # 画面上での描画位置（中心）


    running = True
    while running:
        dt = clock.tick(FPS)
        now_ms = pygame.time.get_ticks()

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # タイトル画面終了（ここでメインゲームへ遷移など）
                    running = False

        # 画面シェイクオフセット
        offset_x = offset_y = 0
        if now_ms < shake_until_ms:
            offset_x = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)
            offset_y = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)

        # 背景描画
        screen.blit(bg_img, (offset_x, offset_y))

        elapsed_ms = now_ms - start_time_ms

        # ロゴのフェードイン
        blit_fade(screen, logo_img, logo_rect.topleft, LOGO_DELAY_MS, elapsed_ms, FADE_MS)

        # キャラのフェードイン＋攻撃モーション
        chars_visible = elapsed_ms >= CHARS_DELAY_MS
        if chars_visible:
            # 攻撃サイクルの進行度（0.0〜1.0）
            cycle_t = (elapsed_ms - CHARS_DELAY_MS) % ATTACK_CYCLE_MS
            progress = cycle_t / ATTACK_CYCLE_MS

            # 前後移動：sin波で近づいたり離れたり
            # 左右それぞれ反対方向に動いて、ピークで衝突
            dash_offset = int(DASH_AMPLITUDE * math.sin(2 * math.pi * progress))

            # キャラの現在位置を計算（基準位置からオフセット）
            c1_pos = (char1_rect.x + dash_offset, char1_rect.y)
            c2_pos = (char2_rect.x - dash_offset, char2_rect.y)

            # フェードイン（表示開始からFADE_MSの間のみ）
            fade_alpha = 255
            chars_elapsed = elapsed_ms - CHARS_DELAY_MS
            if chars_elapsed < FADE_MS:
                fade_alpha = int(255 * (chars_elapsed / FADE_MS))
            c1_draw = char1_img.copy(); c1_draw.set_alpha(fade_alpha)
            c2_draw = char2_img.copy(); c2_draw.set_alpha(fade_alpha)

            screen.blit(c1_draw, (c1_pos[0] + offset_x, c1_pos[1] + offset_y))
            screen.blit(c2_draw, (c2_pos[0] + offset_x, c2_pos[1] + offset_y))

            # ヒットタイミング（ピーク付近）でエフェクトとシェイク
            # ピーク近傍に入ったら一瞬火花を出す
            peak_window = 80  # ピーク判定幅（ms）
            if abs(cycle_t - ATTACK_PEAK_MS) < peak_window:
                # 衝突位置（キャラの間）
                c1_front_x = c1_pos[0] + char1_rect.width
                c2_front_x = c2_pos[0]
                hit_x = (c1_front_x + c2_front_x) // 2
                hit_y = min(c1_pos[1] + char1_rect.height, c2_pos[1] + char2_rect.height) - char1_rect.height // 2

                # 火花（簡易スター型）
                #for angle_deg in range(0, 360, 45):
                    #rad = math.radians(angle_deg)
                    #length = 16
                    #x2 = int(hit_x + math.cos(rad) * length) + offset_x
                    #y2 = int(hit_y + math.sin(rad) * length) + offset_y
                    #pygame.draw.line(screen, (255, 220, 90), (hit_x + offset_x, hit_y + offset_y), (x2, y2), 2)

                # 画像火花の表示予約（hit_spark_imgが読み込めている場合）
                if hit_spark_img:
                    hit_spark_until_ms = now_ms + HIT_SPARK_DURATION_MS
                    hit_spark_pos = (hit_x + offset_x, hit_y + offset_y)

                
                # 画像火花の描画（期限内のみ）
                if hit_spark_img and now_ms < hit_spark_until_ms:
                    # 中心合わせ用にrectを取得して center を指定
                    spark = hit_spark_img.copy()
                    spark.set_alpha(HIT_SPARK_ALPHA)

                    spark_rect = spark.get_rect(center=hit_spark_pos)
                    # 加算合成っぽい見た目にしたい場合は BLEND_ADD を使う（背景が暗めのときに映えます）
                    # 通常合成で十分なら下の1行だけでOK（BLEND_ADDはコメントアウト）
                    screen.blit(spark, spark_rect)  # これが基本
                    # screen.blit(spark, spark_rect, special_flags=pygame.BLEND_ADD)  # もっと眩しく


                # 軽いフラッシュ
                flash_alpha = max(0, 150 - int(150 * abs(cycle_t - ATTACK_PEAK_MS) / peak_window))
                flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash.fill((255, 255, 255, flash_alpha))
                screen.blit(flash, (0, 0))

                # シェイクを延長
                shake_until_ms = now_ms + SHAKE_DURATION_MS

        # 「Press SPACE to Start」点滅
        
# 「Press SPACE to Start」点滅（一定時間経過後に表示）
        if elapsed_ms >= TEXT_DELAY_MS:  # 4秒経過後に表示開始
            blink = (now_ms // 400) % 2 == 0
            if blink:
                draw_text_center(screen, "Press SPACE to Start", font,
                                SCREEN_HEIGHT - 100, TEXT_COLOR, TEXT_SHADOW)


        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
