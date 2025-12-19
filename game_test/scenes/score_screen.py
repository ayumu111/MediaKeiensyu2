import pygame
import time
import os
# あなたのSceneクラス定義があるファイルをインポート
# もしSceneクラスが common.py にあるなら from common import Scene など
# ここでは便宜上、上記のSceneクラスを継承する前提で書きます
from core.scene import Scene  # ※Sceneクラスが定義されているファイル名に合わせて変更してください

class ScoreScene(Scene):
    def __init__(self):
        super().__init__() # 親クラス(Scene)の初期化
        
        # ▼ 修正前：これだと scenes フォルダの中を見てしまう
        # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # ▼ 修正後：os.path.dirname を2回使って、1つ上の階層(game_test)を取得する
        file_path = os.path.abspath(__file__)     # .../game_test/scenes/score_scene.py
        scene_dir = os.path.dirname(file_path)    # .../game_test/scenes
        BASE_DIR = os.path.dirname(scene_dir)     # .../game_test  <-- ここが欲しい！

        # --- 設定 ---
        self.WIDTH, self.HEIGHT = 800, 600
        self.SEGMENT_LIMITS = [100.0, 100.0, 300.0]
        self.ANIM_SPEED = 180.0
        
        # これで game_test/finalscores.txt を指すようになります
        self.SCORES_FILE = os.path.join(BASE_DIR, "finalscores.txt")
        self.READ_INTERVAL = 0.5
        
        
        # フォント設定 (適宜パスを合わせてください)
        self.font_path_title = "Splatfont2.ttf"
        self.font_path_main = "Paintball_Beta_3.ttf"
        self.load_fonts()

        # 色定義
        self.TITLE_COLOR_MAIN = pygame.Color("YELLOW")
        self.TITLE_COLOR_OUTLINE = pygame.Color(30, 80, 220)
        self.TITLE_COLOR_SHADOW = pygame.Color("BLACK")
        self.RED_COLS = [pygame.Color(255,140,140), pygame.Color(255,80,80), pygame.Color(180,0,0)]
        self.BLUE_COLS = [pygame.Color(160,200,255), pygame.Color(80,160,255), pygame.Color(0,80,200)]

        # 状態リセット
        self.reset_state()

    def load_fonts(self):
        # ★ここが修正ポイント★
        # このファイル (score_screen.py) があるフォルダのパスを取得
        current_dir = os.path.dirname(__file__)

        # フォルダパスとファイル名を結合して、絶対パスを作る
        # これでどこから実行しても正しく読み込めます
        path_main = os.path.join(current_dir, "../font/Paintball_Beta_3.ttf")
        path_title = os.path.join(current_dir, "../font/Splatfont2.ttf")

        try:
            # 作成したパス (path_main, path_title) を使う
            self.score_font = pygame.font.Font(path_main, 24)
            self.title_font = pygame.font.Font(path_title, 80)
            self.winner_font = pygame.font.Font(path_main, 80)
            self.countdown_font = pygame.font.Font(path_main, 150)
            print("フォント読み込み成功！")
        except FileNotFoundError:
            print(f"フォントが見つかりません: {path_main}")
            # エラー時のフォールバック
            self.score_font = pygame.font.SysFont(None, 24)
            self.title_font = pygame.font.SysFont(None, 80)
            self.winner_font = pygame.font.SysFont(None, 80)
            self.countdown_font = pygame.font.SysFont(None, 150)
        except Exception as e:
            print(f"フォント読み込みエラー: {e}")
            self.score_font = pygame.font.SysFont(None, 24)
            self.title_font = pygame.font.SysFont(None, 80)
            self.winner_font = pygame.font.SysFont(None, 80)
            self.countdown_font = pygame.font.SysFont(None, 150)

    def reset_state(self):
        """シーン開始時の初期化"""
        self.current_red_segs = [0.0, 0.0, 0.0]
        self.current_blue_segs = [0.0, 0.0, 0.0]
        self.target_red_segs = [0.0, 0.0, 0.0]
        self.target_blue_segs = [0.0, 0.0, 0.0]
        self._last_read = 0.0

        # タイトルアニメーション用
        self.TITLE_STR = "けっかはっぴょう！！"
        self.TITLE_TARGET_Y = 50
        self.TITLE_START_Y = -130.0
        self.TITLE_EASING = 0.12
        self.CHAR_DROP_DELAY = 0.15
        
        self.title_chars = []
        total_width = self.title_font.size(self.TITLE_STR)[0]
        current_char_x = self.WIDTH // 2 - total_width // 2
        start_time_base = time.time() + 0.5 # 0.5秒後に開始

        for i, char in enumerate(self.TITLE_STR):
            m = self.title_font.render(char, True, self.TITLE_COLOR_MAIN)
            o = self.title_font.render(char, True, self.TITLE_COLOR_OUTLINE)
            s = self.title_font.render(char, True, self.TITLE_COLOR_SHADOW)
            self.title_chars.append({
                'main': m, 'outline': o, 'shadow': s,
                'tx': current_char_x, 'cy': self.TITLE_START_Y,
                'start_time': start_time_base + i * self.CHAR_DROP_DELAY + 0.1 * i,
                'finished': False
            })
            current_char_x += m.get_width()

        self.title_animation_done = False
        
        # Winner演出用
        self.show_winner = False
        self.dot_count = 0
        self.dot_timer = 0
        self.DOT_INTERVAL = 500 # ms
        self.winner_surf = self.winner_font.render("Winner", True, pygame.Color("YELLOW"))
        self.winner_shadow = self.winner_font.render("Winner", True, pygame.Color("BLACK"))
        self.winner_rect = self.winner_surf.get_rect(center=(self.WIDTH // 2 - 30, 480))
        self.dot_surf = self.winner_font.render(".", True, pygame.Color("YELLOW"))
        self.dot_shadow = self.winner_font.render(".", True, pygame.Color("BLACK"))

        # カウントダウン用
        self.show_countdown = False
        self.countdown_val = 3
        self.countdown_timer = 0
        self.all_done = False
        
        # 初回のスコア読み込み
        self.try_read_scores_file()

    def clamp_val(self, v, limit):
        return max(0.0, min(limit, v))

    def try_read_scores_file(self):
        now = time.time()
        if now - self._last_read < self.READ_INTERVAL: return
        self._last_read = now
        
        if not os.path.exists(self.SCORES_FILE): return
        try:
            with open(self.SCORES_FILE, "r", encoding="utf-8") as f:
                s = f.read().strip()
            if not s: return
            parts = [p.strip() for p in s.replace(",", " ").split() if p.strip()]
            if len(parts) >= 6:
                r, b = [], []
                for i in range(3):
                    r.append(self.clamp_val(float(parts[i]), self.SEGMENT_LIMITS[i]))
                    b.append(self.clamp_val(float(parts[i+3]), self.SEGMENT_LIMITS[i]))
                self.target_red_segs = r
                self.target_blue_segs = b
        except: pass

    def step_list(self, curr, targ, dt):
        out = []
        maxstep = self.ANIM_SPEED * dt
        for c, t in zip(curr, targ):
            diff = t - c
            if abs(diff) <= maxstep: out.append(t)
            else: out.append(c + (maxstep if diff > 0 else -maxstep))
        return out

    def is_reached(self, curr, targ):
        for c, t in zip(curr, targ):
            if abs(c - t) > 0.5: return False
        return True

    # ==========================================
    # ここから Scene クラス固有のメソッド実装
    # ==========================================

    def handle_events(self, events):
        """イベント処理"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # デバッグ用: スペースキーで強制スキップ
                if event.key == pygame.K_SPACE:
                    self.request_next("round_result") # ←次のシーン名を指定

    def update(self, dt):
        """更新処理 (dtは秒単位)"""
        self.try_read_scores_file()
        current_time = time.time()
        current_ticks = pygame.time.get_ticks()

        # 1. タイトル落下アニメーション
        all_chars_finished = True
        for c in self.title_chars:
            if current_time >= c['start_time']:
                dist = self.TITLE_TARGET_Y - c['cy']
                if dist > 0.5:
                    c['cy'] += dist * self.TITLE_EASING
                    all_chars_finished = False
                else:
                    c['cy'] = self.TITLE_TARGET_Y
                    c['finished'] = True
            else:
                all_chars_finished = False
        
        if all_chars_finished:
            self.title_animation_done = True

        # 2. メーター伸びるアニメーション
        if self.title_animation_done:
            self.current_red_segs = self.step_list(self.current_red_segs, self.target_red_segs, dt)
            self.current_blue_segs = self.step_list(self.current_blue_segs, self.target_blue_segs, dt)

            if not self.show_winner:
                if self.is_reached(self.current_red_segs, self.target_red_segs) and \
                   self.is_reached(self.current_blue_segs, self.target_blue_segs):
                    self.show_winner = True
                    self.dot_timer = current_ticks
            
            # 3. Winnerドットアニメ
            if self.show_winner and self.dot_count < 3:
                if current_ticks - self.dot_timer > self.DOT_INTERVAL:
                    self.dot_count += 1
                    self.dot_timer = current_ticks
            
            # 4. カウントダウン開始判定
            if self.show_winner and self.dot_count == 3 and not self.all_done:
                self.all_done = True
                self.show_countdown = True
                self.countdown_timer = current_ticks
                self.countdown_val = 3

        # 5. カウントダウン更新
        if self.show_countdown and self.countdown_val >= 0:
            if current_ticks - self.countdown_timer > 1000: # 1秒
                self.countdown_val -= 1
                self.countdown_timer = current_ticks
        
        # 6. シーン遷移
        # 6. シーン遷移
        if self.show_countdown and self.countdown_val < 0:
            # カウントダウンが終わったらタイトル画面へ戻る
            self.request_next("round_result") # <--- game_main.py に登録されている名前にする

    def draw(self, surface):
        """描画処理"""
        surface.fill((22,155,155)) # 背景色

        # タイトル
        for c in self.title_chars:
            surface.blit(c['shadow'], (c['tx']+4, c['cy']+4))
            surface.blit(c['outline'], (c['tx']-3, c['cy']))
            surface.blit(c['outline'], (c['tx']+3, c['cy']))
            surface.blit(c['outline'], (c['tx'], c['cy']-3))
            surface.blit(c['outline'], (c['tx'], c['cy']+3))
            surface.blit(c['main'], (c['tx'], c['cy']))

        # メーター描画関数 (内部関数)
        def draw_meter(x, y, segs, cols):
            w, h = 680, 80
            pygame.draw.rect(surface, pygame.Color("WHITE"), (x-10, y-10, w+20, h+20))
            pygame.draw.rect(surface, pygame.Color("BLACK"), (x, y, w, h))
            cur_x = x + 4
            inner_w = w - 8
            for v, col in zip(segs, cols):
                sw = int((v / 500.0) * inner_w)
                if sw > 0:
                    pygame.draw.rect(surface, col, (cur_x, y+4, sw, h-8))
                    cur_x += sw
            # 数値
            total = sum(segs)
            pct = int((total/500)*100)
            txt = self.score_font.render(f"{int(total)} / 500 ({pct}%)", True, pygame.Color("WHITE"))
            stxt = self.score_font.render(f"{int(total)} / 500 ({pct}%)", True, pygame.Color("BLACK"))
            tx, ty = x + 20, y + h//2 - txt.get_height()//2
            surface.blit(stxt, (tx+2, ty+2))
            surface.blit(txt, (tx, ty))

        draw_meter(100, 200, self.current_red_segs, self.RED_COLS)
        draw_meter(100, 300, self.current_blue_segs, self.BLUE_COLS)

        # アイコン
        pygame.draw.circle(surface, self.RED_COLS[-1], (45, 240), 40)
        pygame.draw.circle(surface, self.BLUE_COLS[-1], (45, 350), 40)

        # Winner
        if self.show_winner:
            surface.blit(self.winner_shadow, (self.winner_rect.x+4, self.winner_rect.y+4))
            surface.blit(self.winner_surf, self.winner_rect)
            bx = self.winner_rect.right + 5
            for i in range(self.dot_count):
                dx = bx + i * (self.dot_surf.get_width()*0.7)
                dy = self.winner_rect.y
                surface.blit(self.dot_shadow, (dx+4, dy+4))
                surface.blit(self.dot_surf, (dx, dy))

        # CountDown
        if self.show_countdown and self.countdown_val >= 0:
            cs = str(self.countdown_val)
            c_surf = self.countdown_font.render(cs, True, pygame.Color("YELLOW"))
            c_shad = self.countdown_font.render(cs, True, pygame.Color("BLACK"))
            cr = c_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2))
            surface.blit(c_shad, (cr.x+5, cr.y+5))
            surface.blit(c_surf, cr)