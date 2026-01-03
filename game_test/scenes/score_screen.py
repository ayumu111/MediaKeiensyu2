import pygame
import time
import os
# Sceneクラスのインポートパスは環境に合わせて調整してください
from core.scene import Scene 

class ScoreScene(Scene):
    def __init__(self):
        super().__init__() 
        
        # パスの構築
        file_path = os.path.abspath(__file__)     
        scene_dir = os.path.dirname(file_path)    
        BASE_DIR = os.path.dirname(scene_dir)     

        # --- 設定 ---
        self.WIDTH, self.HEIGHT = 800, 600
        
        # 読み込むファイル
        self.SCORE_FILE_1P = os.path.join(BASE_DIR, "1Pscores.txt")
        self.SCORE_FILE_2P = os.path.join(BASE_DIR, "2Pscores.txt")
        
        self.READ_INTERVAL = 0.5
        self.ANIM_SPEED = 150.0  # アニメーション速度
        self.MAX_SCORE_RANGE = 300.0 # バーの最大値（3ラウンド分として300点満点想定）

        # フォント設定
        self.load_fonts()

        # --- 色定義 ---
        self.TITLE_COLOR_MAIN = pygame.Color("YELLOW")
        self.TITLE_COLOR_OUTLINE = pygame.Color(30, 80, 220)
        self.TITLE_COLOR_SHADOW = pygame.Color("BLACK")
        
        # 1Pカラー
        self.P1_COLOR_NEW  = pygame.Color(255, 80, 80)   # 今回のスコア（明るい赤）
        self.P1_COLOR_PREV = pygame.Color(160, 40, 40)   # 前回の合計（暗い赤）
        self.P1_BG_COLOR   = pygame.Color(60, 0, 0)      # 背景

        # 2Pカラー
        self.P2_COLOR_NEW  = pygame.Color(80, 160, 255)  # 今回のスコア（明るい青）
        self.P2_COLOR_PREV = pygame.Color(40, 80, 160)   # 前回の合計（暗い青）
        self.P2_BG_COLOR   = pygame.Color(0, 0, 60)      # 背景

        # 状態リセット
        self.reset_state()

    def load_fonts(self):
        current_dir = os.path.dirname(__file__)
        path_main = os.path.join(current_dir, "../font/Paintball_Beta_3.ttf")
        path_title = os.path.join(current_dir, "../font/Splatfont2.ttf")

        try:
            self.score_font = pygame.font.Font(path_main, 30)
            self.round_font = pygame.font.Font(path_main, 30)
            self.title_font = pygame.font.Font(path_title, 80)
            self.msg_font = pygame.font.Font(path_main, 60)     # Winner/Next用
            self.countdown_font = pygame.font.Font(path_main, 150)
        except Exception as e:
            print(f"フォント読み込みエラー(デフォルトを使用): {e}")
            self.score_font = pygame.font.SysFont(None, 30)
            self.round_font = pygame.font.SysFont(None, 30)
            self.title_font = pygame.font.SysFont(None, 80)
            self.msg_font = pygame.font.SysFont(None, 60)
            self.countdown_font = pygame.font.SysFont(None, 150)

    def reset_state(self):
        """シーン開始時の初期化"""
        # 現在のアニメーション用スコア（前回の合計点からスタートする）
        self.anim_score_1p = 0.0
        self.anim_score_2p = 0.0
        
        # 目標値（今回の合計点）
        self.target_total_1p = 0.0
        self.target_total_2p = 0.0

        # 前回の合計点（バーの土台部分）
        self.prev_total_1p = 0.0
        self.prev_total_2p = 0.0
        
        self.round_count = 1 
        self._last_read = 0.0

        # タイトルアニメーション設定
        self.TITLE_STR = "けっかはっぴょう！！"
        self.TITLE_TARGET_Y = 50
        self.TITLE_START_Y = -130.0
        self.TITLE_EASING = 0.12
        self.CHAR_DROP_DELAY = 0.15
        
        self.title_chars = []
        total_width = self.title_font.size(self.TITLE_STR)[0]
        current_char_x = self.WIDTH // 2 - total_width // 2
        start_time_base = time.time() + 0.5

        for i, char in enumerate(self.TITLE_STR):
            m = self.title_font.render(char, True, self.TITLE_COLOR_MAIN)
            o = self.title_font.render(char, True, self.TITLE_COLOR_OUTLINE)
            s = self.title_font.render(char, True, self.TITLE_COLOR_SHADOW)
            self.title_chars.append({
                'main': m, 'outline': o, 'shadow': s,
                'tx': current_char_x, 'cy': self.TITLE_START_Y,
                'start_time': start_time_base + i * self.CHAR_DROP_DELAY,
                'finished': False
            })
            current_char_x += m.get_width()

        self.title_animation_done = False
        self.show_message = False
        self.dot_count = 0
        self.dot_timer = 0
        self.DOT_INTERVAL = 500 

        # メッセージ用（Winner...? または Go to next...）
        self.message_surf = None 
        self.message_rect = None

        self.show_countdown = False
        self.countdown_val = 3
        self.countdown_timer = 0
        self.all_done = False
        
        # 初回のスコア読み込み
        self.try_read_scores_file()
        
        # アニメーション初期値を「前回の合計」にセット（ここから伸びる）
        self.anim_score_1p = self.prev_total_1p
        self.anim_score_2p = self.prev_total_2p

    def try_read_scores_file(self):
        """
        ファイルからスコア履歴を読み込み、
        「前回の合計(prev)」と「今回の合計(target)」を算出する。
        """
        now = time.time()
        if now - self._last_read < self.READ_INTERVAL: return
        self._last_read = now
        
        def parse_scores(filepath):
            # 戻り値: (前回の合計, 今回の合計, ラウンド数)
            if not os.path.exists(filepath): return 0.0, 0.0, 1
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content: return 0.0, 0.0, 1
                    
                    # カンマ区切りで数値リスト化
                    parts = [float(x) for x in content.split(",")]
                    
                    total_score = sum(parts) # 現在の全合計
                    rounds = len(parts)
                    
                    if rounds > 1:
                        # 2ラウンド目以降: (全合計 - 今回のスコア) が前回の合計
                        prev_total = sum(parts[:-1])
                    else:
                        # 1ラウンド目: 前回の合計は0
                        prev_total = 0.0
                        
                    return prev_total, total_score, rounds
            except:
                return 0.0, 0.0, 1

        self.prev_total_1p, self.target_total_1p, r1 = parse_scores(self.SCORE_FILE_1P)
        self.prev_total_2p, self.target_total_2p, r2 = parse_scores(self.SCORE_FILE_2P)

        # ラウンド数は多い方を採用
        self.round_count = max(r1, r2) 

    def step_val(self, curr, targ, dt):
        """数値を徐々に目標値へ近づける"""
        diff = targ - curr
        maxstep = self.ANIM_SPEED * dt
        if abs(diff) <= maxstep:
            return targ
        else:
            return curr + (maxstep if diff > 0 else -maxstep)

    # --- Scene API ---

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.perform_transition()

    def perform_transition(self):
        """次のシーンへ遷移する処理 (ラウンド数で分岐)"""
        print(f"現在のラウンド数: {self.round_count}")
        
        # 3ラウンド終了時の分岐
        if self.round_count >= 3:
            print(">> 3ラウンド終了 -> 最終結果へ")
            self.request_next("final_result")
        else:
            print(">> 次のラウンドへ")
            self.request_next("roulette")

    def update(self, dt):
        self.try_read_scores_file()
        current_time = time.time()
        current_ticks = pygame.time.get_ticks()

        # 1. タイトル落下
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

        # 2. メーターアニメーション
        if self.title_animation_done:
            # アニメーション用変数を目標値(今回の合計)まで増やす
            self.anim_score_1p = self.step_val(self.anim_score_1p, self.target_total_1p, dt)
            self.anim_score_2p = self.step_val(self.anim_score_2p, self.target_total_2p, dt)

            if not self.show_message:
                reached1 = abs(self.anim_score_1p - self.target_total_1p) < 0.5
                reached2 = abs(self.anim_score_2p - self.target_total_2p) < 0.5
                
                if reached1 and reached2:
                    self.show_message = True
                    self.dot_timer = current_ticks
                    
                    # 表示テキストの決定
                    if self.round_count >= 3:
                        txt = "Winner"
                        col = pygame.Color("YELLOW")
                    else:
                        txt = "Go to next round!!"
                        col = pygame.Color("GREEN")
                        
                    self.message_surf = self.msg_font.render(txt, True, col)
                    # 画面中央下部に配置
                    self.message_rect = self.message_surf.get_rect(center=(self.WIDTH // 2, 480))
                    
                    # Go to next... の場合は右に寄りすぎないよう調整
                    if self.round_count < 3:
                        # 点滅ドット用に少し左へずらすなどの調整はお好みで
                        pass
            
            # 3. メッセージ後のドット演出 (". . ." or "!!")
            if self.show_message and self.dot_count < 3:
                if current_ticks - self.dot_timer > self.DOT_INTERVAL:
                    self.dot_count += 1
                    self.dot_timer = current_ticks
            
            # 4. カウントダウン開始
            if self.show_message and self.dot_count == 3 and not self.all_done:
                self.all_done = True
                self.show_countdown = True
                self.countdown_timer = current_ticks
                self.countdown_val = 3

        # 5. カウントダウン進行
        if self.show_countdown and self.countdown_val >= 0:
            if current_ticks - self.countdown_timer > 1000:
                self.countdown_val -= 1
                self.countdown_timer = current_ticks
        
        # 6. 次のシーンへ
        if self.show_countdown and self.countdown_val < 0:
            self.perform_transition()

    def draw(self, surface):
        surface.fill((22, 155, 155)) # 背景色

        # タイトル描画
        for c in self.title_chars:
            surface.blit(c['shadow'], (c['tx']+4, c['cy']+4))
            surface.blit(c['outline'], (c['tx']-3, c['cy']))
            surface.blit(c['outline'], (c['tx']+3, c['cy']))
            surface.blit(c['outline'], (c['tx'], c['cy']-3))
            surface.blit(c['outline'], (c['tx'], c['cy']+3))
            surface.blit(c['main'], (c['tx'], c['cy']))

        # ラウンド数
        round_str = f"Round {self.round_count}"
        r_surf = self.round_font.render(round_str, True, pygame.Color("WHITE"))
        surface.blit(r_surf, (self.WIDTH//2 - r_surf.get_width()//2, 160))

        # --- メーター描画関数 (2段階描画) ---
        def draw_stacked_bar(label, current_anim, prev_total, x, y, col_new, col_prev, col_bg):
            bar_w, bar_h = 500, 60
            
            # 外枠と背景
            pygame.draw.rect(surface, pygame.Color("WHITE"), (x-5, y-5, bar_w+10, bar_h+10))
            pygame.draw.rect(surface, col_bg, (x, y, bar_w, bar_h))
            
            # 1. 前回の合計分 (暗い色)
            ratio_prev = min(1.0, prev_total / self.MAX_SCORE_RANGE)
            w_prev = int(bar_w * ratio_prev)
            if w_prev > 0:
                pygame.draw.rect(surface, col_prev, (x, y, w_prev, bar_h))
            
            # 2. 今回のアニメーション分 (前回の後ろに追加、明るい色)
            # current_anim は「前回の合計」からスタートして「今回の合計」まで増えている
            # 描画すべき長さは current_anim 全体に対応する長さから、w_prev を引いた残りではない
            # 重ねて描画すれば簡単
            
            ratio_curr = min(1.0, current_anim / self.MAX_SCORE_RANGE)
            w_curr = int(bar_w * ratio_curr)
            
            # 暗いバーの上から描画するのではなく、「暗いバーの右端から、現在の合計までの差分」を描画する
            # あるいは単純に「現在の合計の長さ」を明るい色で描き、そのあと「前回の合計」を暗い色で上書きしてもよいが
            # ここでは「暗い色を描画済み」なので、「その右」に「今回の増分」を描画する
            
            if w_curr > w_prev:
                # 増分だけを描画
                pygame.draw.rect(surface, col_new, (x + w_prev, y, w_curr - w_prev, bar_h))
            
            # テキスト表示 (合計点)
            score_txt = f"{int(current_anim)} pts"
            txt = self.score_font.render(f"{label}: {score_txt}", True, pygame.Color("WHITE"))
            
            # 文字の影
            stxt = self.score_font.render(f"{label}: {score_txt}", True, pygame.Color("BLACK"))
            
            surface.blit(stxt, (x + 22, y + bar_h//2 - 10 + 2))
            surface.blit(txt, (x + 20, y + bar_h//2 - 10))

        # 1P/2P メーター描画実行
        draw_stacked_bar("1P Total", self.anim_score_1p, self.prev_total_1p, 
                         150, 250, self.P1_COLOR_NEW, self.P1_COLOR_PREV, self.P1_BG_COLOR)
        
        draw_stacked_bar("2P Total", self.anim_score_2p, self.prev_total_2p, 
                         150, 350, self.P2_COLOR_NEW, self.P2_COLOR_PREV, self.P2_BG_COLOR)

        # アイコン
        pygame.draw.circle(surface, self.P1_COLOR_NEW, (100, 280), 35)
        pygame.draw.circle(surface, self.P2_COLOR_NEW, (100, 380), 35)
        p1_txt = self.score_font.render("1P", True, pygame.Color("WHITE"))
        p2_txt = self.score_font.render("2P", True, pygame.Color("WHITE"))
        surface.blit(p1_txt, p1_txt.get_rect(center=(100, 280)))
        surface.blit(p2_txt, p2_txt.get_rect(center=(100, 380)))

        # メッセージ表示 (Winner...? / Go to next...)
        if self.show_message:
            surface.blit(self.message_surf, self.message_rect)
            
            # ドットアニメーション ("." を追加で描画)
            if self.round_count >= 3:
                # Winner...? の場合のドット
                dot_char = "."
            else:
                # Go to next!! の場合はエクスクラメーションなどを増やすか、あるいは点滅させる
                dot_char = "!" 

            dot_surf = self.msg_font.render(dot_char, True, self.message_surf.get_at((0,0))) # 文字色を取得して合わせる
            
            bx = self.message_rect.right + 5
            for i in range(self.dot_count):
                dx = bx + i * 15
                surface.blit(dot_surf, (dx, self.message_rect.y))

        # CountDown
        if self.show_countdown and self.countdown_val >= 0:
            cs = str(self.countdown_val)
            c_surf = self.countdown_font.render(cs, True, pygame.Color("YELLOW"))
            c_shad = self.countdown_font.render(cs, True, pygame.Color("BLACK"))
            cr = c_surf.get_rect(center=(self.WIDTH//2, self.HEIGHT//2))
            surface.blit(c_shad, (cr.x+5, cr.y+5))
            surface.blit(c_surf, cr)