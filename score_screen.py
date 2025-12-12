import pygame
import os
import time

class ScoreScreen:
    def __init__(self):
        # --- 定数設定 ---
        self.WIDTH, self.HEIGHT = 800, 600
        self.SEGMENT_LIMITS = [100.0, 100.0, 300.0]
        self.ANIM_SPEED = 180.0
        self.SCORES_FILE = "finalscores.txt" # または "scores.txt"
        self.READ_INTERVAL = 0.5
        
        # タイトルアニメーション設定
        self.TITLE_STR = "けっかはっぴょう！！"
        self.TITLE_TARGET_Y = 50
        self.TITLE_START_Y = -130.0
        self.TITLE_EASING = 0.12
        self.CHAR_DROP_DELAY = 0.15
        self.START_DELAY = 0.5

        # 色定義
        self.TITLE_COLOR_MAIN = pygame.Color("YELLOW")
        self.TITLE_COLOR_OUTLINE = pygame.Color(30, 80, 220)
        self.TITLE_COLOR_SHADOW = pygame.Color("BLACK")
        self.RED_COLS = [pygame.Color(255,140,140), pygame.Color(255,80,80), pygame.Color(180,0,0)]
        self.BLUE_COLS = [pygame.Color(160,200,255), pygame.Color(80,160,255), pygame.Color(0,80,200)]

        # フォント読み込み
        self.load_fonts()

        # 変数の初期化
        self.reset()

    def load_fonts(self):
        # フォントパス（環境に合わせて適宜変更してください）
        font_path2 = "Paintball_Beta_3.ttf"
        font_path1 = "Splatfont2.ttf"
        
        try:
            self.score_font = pygame.font.Font(font_path2, 24)
            self.title_font = pygame.font.Font(font_path1, 80)
            self.winner_font = pygame.font.Font(font_path2, 80)
            self.countdown_font = pygame.font.Font(font_path2, 150)
        except FileNotFoundError:
            print("警告: 指定されたフォントが見つかりません。デフォルトフォントを使用します。")
            self.score_font = pygame.font.SysFont("arial", 24, bold=True)
            self.title_font = pygame.font.SysFont("arial", 80, bold=True)
            self.winner_font = pygame.font.SysFont("arial", 80, bold=True)
            self.countdown_font = pygame.font.SysFont("arial", 150, bold=True)
        except Exception as e:
            print(f"フォント読み込みエラー: {e}")
            self.score_font = pygame.font.SysFont(None, 24)
            self.title_font = pygame.font.SysFont(None, 80)
            self.winner_font = pygame.font.SysFont(None, 80)
            self.countdown_font = pygame.font.SysFont(None, 150)

    def reset(self):
        """画面遷移時に毎回呼び出して状態をリセットする"""
        # バーの数値
        self.current_red_segs = [0.0, 0.0, 0.0]
        self.current_blue_segs = [0.0, 0.0, 0.0]
        self.target_red_segs = [0.0, 0.0, 0.0] # 初期値は0、ファイルから読む
        self.target_blue_segs = [0.0, 0.0, 0.0]

        self._last_read = 0.0

        # タイトルアニメーション用
        self.title_chars = []
        total_width = self.title_font.size(self.TITLE_STR)[0]
        current_char_x = self.WIDTH // 2 - total_width // 2
        start_time_base = time.time() + self.START_DELAY

        for i, char in enumerate(self.TITLE_STR):
            main_surf = self.title_font.render(char, True, self.TITLE_COLOR_MAIN)
            outline_surf = self.title_font.render(char, True, self.TITLE_COLOR_OUTLINE)
            shadow_surf = self.title_font.render(char, True, self.TITLE_COLOR_SHADOW)
            
            self.title_chars.append({
                'main_surf': main_surf,
                'outline_surf': outline_surf,
                'shadow_surf': shadow_surf,
                'tx': current_char_x,
                'cy': self.TITLE_START_Y,
                'start_time': start_time_base + i * self.CHAR_DROP_DELAY + 0.1 * i,
                'finished': False
            })
            current_char_x += main_surf.get_width()

        self.title_animation_done = False

        # Winner表示用
        self.WINNER_STR = "Winner"
        self.winner_surf = self.winner_font.render(self.WINNER_STR, True, pygame.Color("YELLOW"))
        self.winner_shadow = self.winner_font.render(self.WINNER_STR, True, pygame.Color("BLACK"))
        self.winner_rect = self.winner_surf.get_rect(center=(self.WIDTH // 2 - 30, 480))

        # ドットアニメーション用
        self.DOT_STR = "."
        self.dot_surf = self.winner_font.render(self.DOT_STR, True, pygame.Color("YELLOW"))
        self.dot_shadow = self.winner_font.render(self.DOT_STR, True, pygame.Color("BLACK"))
        self.dot_width = self.dot_surf.get_width()

        self.show_winner = False
        self.dot_count = 0
        self.dot_timer = 0
        self.DOT_INTERVAL = 500

        # カウントダウン用
        self.countdown_value = 3
        self.countdown_timer = 0
        self.COUNTDOWN_INTERVAL = 1000
        self.show_countdown = False
        self.all_animations_done = False
        
        # 初回読み込み
        self.try_read_scores_file()

    def clamp_val(self, v, limit):
        return max(0.0, min(limit, v))

    def try_read_scores_file(self):
        now = time.time()
        if now - self._last_read < self.READ_INTERVAL:
            return
        self._last_read = now
        
        if not os.path.exists(self.SCORES_FILE):
            return
        try:
            with open(self.SCORES_FILE, "r", encoding="utf-8") as f:
                s = f.read().strip()
            if not s:
                return
            parts = [p.strip() for p in s.replace("\t", ",").replace(" ", ",").split(",") if p.strip()!=""]
            
            if len(parts) >= 6:
                r = []
                b = []
                for i in range(3):
                    r.append(self.clamp_val(float(parts[i]), self.SEGMENT_LIMITS[i]))
                    b.append(self.clamp_val(float(parts[i+3]), self.SEGMENT_LIMITS[i]))
                self.target_red_segs = r
                self.target_blue_segs = b
            # (省略可能: 3つだけの場合や1つの場合のロジックも必要ならここに記述)
            
        except Exception as e:
            print("finalscores.txt parse error:", e)

    def step_toward_list(self, curr_list, target_list, dt):
        out = []
        maxstep = self.ANIM_SPEED * dt
        for c, t in zip(curr_list, target_list):
            diff = t - c
            if abs(diff) <= maxstep:
                out.append(t)
            else:
                out.append(c + (maxstep if diff > 0 else -maxstep))
        return out

    def are_segs_reached(self, curr, targ):
        tolerance = 0.5 
        for c, t in zip(curr, targ):
            if abs(c - t) > tolerance:
                return False
        return True

    def update(self, events):
        """
        メインループから呼ばれる更新処理
        戻り値: 次のシーン名 (遷移しない場合は None)
        """
        # 時間管理用のdt計算 (pygame.clockはmainで管理されている想定だが、簡易的に計算)
        # 厳密には main.py から dt を渡す設計が良いが、ここでは固定値または計算で代用
        dt = 0.033 # 約30FPS想定
        current_time_sec = time.time()
        current_ticks = pygame.time.get_ticks()
        
        self.try_read_scores_file()

        # イベント処理
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # スペースキーでスキップ/次の画面へ (デバッグ用)
                    return "game" # または "title"

        # --- タイトルアニメーション ---
        all_chars_finished = True
        for char_data in self.title_chars:
            if current_time_sec >= char_data['start_time']:
                dist_y = self.TITLE_TARGET_Y - char_data['cy']
                if dist_y > 0.5:
                    char_data['cy'] += dist_y * self.TITLE_EASING
                    all_chars_finished = False
                else:
                    char_data['cy'] = self.TITLE_TARGET_Y
                    char_data['finished'] = True
            else:
                 all_chars_finished = False
        
        if all_chars_finished:
            self.title_animation_done = True

        # --- メーターアニメーション ---
        if self.title_animation_done:
            self.current_red_segs = self.step_toward_list(self.current_red_segs, self.target_red_segs, dt)
            self.current_blue_segs = self.step_toward_list(self.current_blue_segs, self.target_blue_segs, dt)

            if not self.show_winner:
                red_done = self.are_segs_reached(self.current_red_segs, self.target_red_segs)
                blue_done = self.are_segs_reached(self.current_blue_segs, self.target_blue_segs)
                if red_done and blue_done:
                    self.show_winner = True
                    self.dot_count = 0
                    self.dot_timer = current_ticks
            
            # ドットアニメーション
            if self.show_winner and self.dot_count < 3:
                if current_ticks - self.dot_timer > self.DOT_INTERVAL:
                    self.dot_count += 1
                    self.dot_timer = current_ticks
            
            # カウントダウン開始判定
            if self.show_winner and self.dot_count == 3 and not self.all_animations_done:
                self.all_animations_done = True
                self.show_countdown = True
                self.countdown_timer = current_ticks
                self.countdown_value = 3

        # --- カウントダウン更新 ---
        if self.show_countdown and self.countdown_value >= 0:
            if current_ticks - self.countdown_timer > self.COUNTDOWN_INTERVAL:
                self.countdown_value -= 1
                self.countdown_timer = current_ticks
        
        # カウントダウン終了後の遷移 (0になった1秒後など)
        if self.show_countdown and self.countdown_value < 0:
            return "game" # カウントダウンが終わったらゲーム画面へ遷移

        return None

    def draw_stacked_meter(self, screen, x, y, w, h, segs, colors, border_color):
        pygame.draw.rect(screen, pygame.Color("WHITE"), (x-10, y-10, w+20, h+20))
        pygame.draw.rect(screen, border_color, (x, y, w, h))
        
        total_max = 500.0
        bar_start_x = x + 4
        inner_w = w - 8
        current_bar_x = bar_start_x
        
        for v, col in zip(segs, colors):
            safe_v = max(0.0, v)
            seg_w = int((safe_v / total_max) * inner_w)
            if seg_w > 0:
                pygame.draw.rect(screen, col, (current_bar_x, y+4, seg_w, h-8))
                current_bar_x += seg_w

        total = sum(segs)
        pct = int(round((total / total_max) * 100))
        txt = self.score_font.render(f"{int(round(total))} / 500 ({pct}%)", True, pygame.Color("WHITE"))
        
        text_x = x + 20
        text_y = y + h//2 - txt.get_height()//2
        
        shadow_txt = self.score_font.render(f"{int(round(total))} / 500 ({pct}%)", True, pygame.Color("BLACK"))
        screen.blit(shadow_txt, (text_x + 2, text_y + 2))
        screen.blit(txt, (text_x, text_y))

    def draw(self, screen):
        screen.fill((22,155,155))

        # タイトル描画
        for char_data in self.title_chars:
            cx, cy = char_data['tx'], char_data['cy']
            screen.blit(char_data['shadow_surf'], (cx + 4, cy + 4))
            screen.blit(char_data['outline_surf'], (cx - 3, cy))
            screen.blit(char_data['outline_surf'], (cx + 3, cy))
            screen.blit(char_data['outline_surf'], (cx, cy - 3))
            screen.blit(char_data['outline_surf'], (cx, cy + 3))
            screen.blit(char_data['main_surf'], (cx, cy))
        
        # メーター描画
        meter_width = 680
        self.draw_stacked_meter(screen, 100, 200, meter_width, 80, self.current_red_segs, self.RED_COLS, pygame.Color("BLACK"))
        self.draw_stacked_meter(screen, 100, 300, meter_width, 80, self.current_blue_segs, self.BLUE_COLS, pygame.Color("BLACK"))

        # アイコン
        pygame.draw.circle(screen, self.RED_COLS[-1], (45, 240), 40)
        pygame.draw.circle(screen, self.BLUE_COLS[-1], (45, 350), 40)

        # Winner & Dot
        if self.show_winner:
            screen.blit(self.winner_shadow, (self.winner_rect.x + 4, self.winner_rect.y + 4))
            screen.blit(self.winner_surf, self.winner_rect)
            
            base_dot_x = self.winner_rect.right + 5
            for i in range(self.dot_count):
                dot_x = base_dot_x + i * (self.dot_width * 0.7) 
                dot_y = self.winner_rect.y
                screen.blit(self.dot_shadow, (dot_x + 4, dot_y + 4))
                screen.blit(self.dot_surf, (dot_x, dot_y))

        # カウントダウン
        if self.show_countdown and self.countdown_value >= 0:
            count_str = str(self.countdown_value)
            count_surf = self.countdown_font.render(count_str, True, pygame.Color("YELLOW"))
            count_shadow = self.countdown_font.render(count_str, True, pygame.Color("BLACK"))
            count_rect = count_surf.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            
            screen.blit(count_shadow, (count_rect.x + 5, count_rect.y + 5))
            screen.blit(count_surf, count_rect)