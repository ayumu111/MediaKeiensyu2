import pygame
import sys
import math


class ResultScreen:
    def __init__(self, score_file="scores.txt"):
        pygame.init()
        self.SCREEN_SIZE = (800, 600)
        self.screen = pygame.display.set_mode(self.SCREEN_SIZE)
        self.clock = pygame.time.Clock()

        # =========================
        # 色設定
        # =========================
        self.CIRCLE_COLOR = (240, 240, 240, 180)
        self.BASE_TRI_COLOR = (180, 180, 180, 180)
        self.SCORE_COLOR = (255, 230, 0, 255)
        self.SCORE_EDGE_COLOR = (200, 160, 0, 200)
        self.LABEL_COLOR = (0, 0, 0)
        self.BG_COLOR = (84, 209, 255)

        # =========================
        # フォント
        # =========================
        self.font_en = pygame.font.Font("Paintball_Beta_3.ttf", 60)
        self.font_hira_title = pygame.font.Font("IoEI.ttf", 80)
        self.font_players = pygame.font.Font("Paintball_Beta_3.ttf", 50)
        self.font_labels = pygame.font.Font("IoEI.ttf", 30)
        self.font_score = pygame.font.Font("Paintball_Beta_3.ttf", 30)
        self.font_total = pygame.font.Font("Paintball_Beta_3.ttf", 90)

        # =========================
        # スコア読み込み
        # =========================
        self.load_scores(score_file)

        # =========================
        # 描画準備
        # =========================
        self.prepare_assets()

        # ステップ管理
        self.STEP_BACKGROUND = 0
        self.STEP_TITLE = 1
        self.STEP_LINE = 2
        self.STEP_PLAYERS = 3
        self.STEP_CHART_FRAME = 4
        self.STEP_SCORE_LABELS = 5
        self.STEP_SCORE_NUMBERS = 6
        self.STEP_CHART_SCORE = 7
        self.STEP_TOTAL_SCORE = 8

        self.step = self.STEP_BACKGROUND

        # スコア三角アニメ
        self.score_progress = 0.0
        self.SCORE_GROW_SPEED = 0.015

    # ==============================================================
    # ファイル読み込み
    # ==============================================================
    def load_scores(self, score_file):
        with open(score_file, "r", encoding="utf-8") as f:
            data = f.read().strip()

        values = list(map(int, data.split(",")))
        if len(values) != 6:
            raise ValueError("scores.txt には 6 個の数値が必要です。")

        self.s1_dyn, self.s1_sta, self.s1_uni = values[:3]
        self.s2_dyn, self.s2_sta, self.s2_uni = values[3:]

        self.total_1P = self.s1_dyn + self.s1_sta + self.s1_uni
        self.total_2P = self.s2_dyn + self.s2_sta + self.s2_uni

    # ==============================================================
    # アウトラインテキスト
    # ==============================================================
    def outline(self, text, font, color, outline, w=2):
        base = font.render(text, True, color)
        tw, th = base.get_size()
        surf = pygame.Surface((tw + w*2, th + w*2), pygame.SRCALPHA)
        for dx in (-w, w):
            for dy in (-w, w):
                s = font.render(text, True, outline)
                surf.blit(s, (dx + w, dy + w))
        surf.blit(base, (w, w))
        return surf

    # ==============================================================
    # 描画準備
    # ==============================================================
    def prepare_assets(self):
        # 背景
        self.background = pygame.Surface(self.SCREEN_SIZE)
        self.background.fill(self.BG_COLOR)
        self.background.set_alpha(0)

        # タイトル
        self.title_surf = self.outline("とくてん", self.font_hira_title,
                                       (255,255,255), (0,0,0))
        self.title_surf.set_alpha(0)
        self.title_pos = self.title_surf.get_rect(center=(400, 80))

        # 中央線
        self.line_surf = pygame.Surface((4,450))
        self.line_surf.fill((0,0,0))
        self.line_surf.set_alpha(0)
        self.line_pos = self.line_surf.get_rect(center=(400,350))

        # プレイヤー
        self.p1_surf = self.outline("1P", self.font_players,
                                    (255,255,255), (255,80,80))
        self.p2_surf = self.outline("2P", self.font_players,
                                    (255,255,255), (80,80,255))
        self.p1_surf.set_alpha(0)
        self.p2_surf.set_alpha(0)
        self.p1_pos = self.p1_surf.get_rect(center=(200,150))
        self.p2_pos = self.p2_surf.get_rect(center=(600,150))

        # レーダーチャート
        self.RADIUS = 120
        self.LABEL_DIST = 150
        self.CENTER_L = (200,350)
        self.CENTER_R = (600,350)

        self.circle_left = pygame.Surface((300,300), pygame.SRCALPHA)
        self.circle_right = pygame.Surface((300,300), pygame.SRCALPHA)
        self.circle_left.set_alpha(0)
        self.circle_right.set_alpha(0)

        pygame.draw.circle(self.circle_left, self.CIRCLE_COLOR, (150,150), self.RADIUS)
        pygame.draw.circle(self.circle_right, self.CIRCLE_COLOR, (150,150), self.RADIUS)

        self.draw_base_triangle(self.circle_left)
        self.draw_base_triangle(self.circle_right)

        # ラベル
        labels = [("ダイナミック",-90), ("あんてい",30), ("こせい",150)]
        self.label_surfs = [
            (self.font_labels.render(t, True, self.LABEL_COLOR), ang)
            for t,ang in labels
        ]

        # 下に表示する項目
        self.bottom = {
            "L": {"x": 50, "y": 480},
            "R": {"x": 430, "y": 480},
        }
        self.prepare_bottom_text()

    # --------------------------------------------------------------
    def prepare_bottom_text(self):
        bottom_labels = ["ダイナミック","あんてい","こせい"]

        for side in self.bottom:
            self.bottom[side]["label_surfs"] = [
                self.font_labels.render(name, True, (0,0,0))
                for name in bottom_labels
            ]
            for s in self.bottom[side]["label_surfs"]:
                s.set_alpha(0)

            scores = (
                [self.s1_dyn, self.s1_sta, self.s1_uni]
                if side=="L" else
                [self.s2_dyn, self.s2_sta, self.s2_uni]
            )

            self.bottom[side]["scores"] = []
            for sc in scores:
                if side=="L":
                    surf = self.outline(str(sc), self.font_score,
                                        (255,255,255),(255,80,80))
                else:
                    surf = self.outline(str(sc), self.font_score,
                                        (255,255,255),(80,80,255))
                surf.set_alpha(0)
                self.bottom[side]["scores"].append(surf)

            self.bottom[side]["total_now"] = 0
            self.bottom[side]["total_target"] = (
                self.total_1P if side=="L" else self.total_2P
            )

    # --------------------------------------------------------------
    def fade_in(self, surf, target, step=5):
        a = surf.get_alpha() or 0
        a = min(a + step, target)
        surf.set_alpha(a)
        return a == target

    # --------------------------------------------------------------
    def draw_base_triangle(self, surface):
        cx, cy = 150, 150
        pts = []
        for i in range(3):
            ang = -90 + i*120
            rad = math.radians(ang)
            x = cx + self.RADIUS * math.cos(rad)
            y = cy + self.RADIUS * math.sin(rad)
            pts.append((x,y))
        pygame.draw.polygon(surface, self.BASE_TRI_COLOR, pts, 3)

    # --------------------------------------------------------------
    def draw_score_triangle(self, center, s1, s2, s3):
        surf = pygame.Surface((300,300), pygame.SRCALPHA)
        cx, cy = 150,150
        scores = [s1,s2,s3]
        pts = []

        for i,sc in enumerate(scores):
            ang = -90 + i*120
            rad = math.radians(ang)
            r = (sc/10)*self.RADIUS * self.score_progress
            pts.append((cx + r*math.cos(rad), cy + r*math.sin(rad)))

        pygame.draw.polygon(surf, self.SCORE_COLOR, pts)
        pygame.draw.polygon(surf, self.SCORE_EDGE_COLOR, pts, 2)
        self.screen.blit(surf, (center[0]-150, center[1]-150))

    # ==============================================================
    # メインループ
    # ==============================================================
    def run(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False

            self.screen.fill((0,0,0))
            self.screen.blit(self.background, (0,0))

            # === 上部共通描画 ===
            if self.step >= self.STEP_TITLE:
                self.screen.blit(self.title_surf, self.title_pos)
            if self.step >= self.STEP_LINE:
                self.screen.blit(self.line_surf, self.line_pos)
            if self.step >= self.STEP_PLAYERS:
                self.screen.blit(self.p1_surf, self.p1_pos)
                self.screen.blit(self.p2_surf, self.p2_pos)

            # === STEP 管理 ===
            self.step_logic()

            # === 円 ===
            self.screen.blit(self.circle_left, (self.CENTER_L[0]-150, self.CENTER_L[1]-150))
            self.screen.blit(self.circle_right, (self.CENTER_R[0]-150, self.CENTER_R[1]-150))

            # === ラベル ===
            if self.step >= self.STEP_CHART_FRAME:
                for surf,ang in self.label_surfs:
                    rad = math.radians(ang)
                    for c in (self.CENTER_L, self.CENTER_R):
                        x = c[0] + self.LABEL_DIST * math.cos(rad)
                        y = c[1] + self.LABEL_DIST * math.sin(rad)
                        pos = surf.get_rect(center=(x,y))
                        self.screen.blit(surf, pos)

            # === 成長する三角形 ===
            if self.step >= self.STEP_CHART_SCORE:
                self.draw_score_triangle(self.CENTER_L, self.s1_dyn, self.s1_sta, self.s1_uni)
                self.draw_score_triangle(self.CENTER_R, self.s2_dyn, self.s2_sta, self.s2_uni)

            # === 下テキスト ===
            self.draw_bottom_text()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    # ==============================================================
    def step_logic(self):
        if self.step == self.STEP_BACKGROUND:
            if self.fade_in(self.background, 255):
                self.step = self.STEP_TITLE

        elif self.step == self.STEP_TITLE:
            if self.fade_in(self.title_surf, 255):
                self.step = self.STEP_LINE

        elif self.step == self.STEP_LINE:
            if self.fade_in(self.line_surf, 255):
                self.step = self.STEP_PLAYERS

        elif self.step == self.STEP_PLAYERS:
            l = self.fade_in(self.p1_surf, 255)
            r = self.fade_in(self.p2_surf, 255)
            if l and r:
                self.step = self.STEP_CHART_FRAME

        elif self.step == self.STEP_CHART_FRAME:
            l = self.fade_in(self.circle_left, 255)
            r = self.fade_in(self.circle_right, 255)
            if l and r:
                self.step = self.STEP_SCORE_LABELS

        elif self.step == self.STEP_SCORE_LABELS:
            done = True
            for side in self.bottom:
                for surf in self.bottom[side]["label_surfs"]:
                    if not self.fade_in(surf, 255):
                        done = False
            if done:
                self.step = self.STEP_SCORE_NUMBERS

        elif self.step == self.STEP_SCORE_NUMBERS:
            done = True
            for side in self.bottom:
                for surf in self.bottom[side]["scores"]:
                    if not self.fade_in(surf, 255):
                        done = False
            if done:
                self.step = self.STEP_CHART_SCORE

        elif self.step == self.STEP_CHART_SCORE:
            self.score_progress = min(self.score_progress + self.SCORE_GROW_SPEED, 1.0)
            if self.score_progress >= 1.0:
                self.step = self.STEP_TOTAL_SCORE

        elif self.step == self.STEP_TOTAL_SCORE:
            for side in self.bottom:
                if self.bottom[side]["total_now"] < self.bottom[side]["total_target"]:
                    self.bottom[side]["total_now"] += 1

    # ==============================================================
    def draw_bottom_text(self):
        for side in self.bottom:
            x0 = self.bottom[side]["x"]
            y0 = self.bottom[side]["y"]

            # ラベル
            for i,surf in enumerate(self.bottom[side]["label_surfs"]):
                self.screen.blit(surf, (x0, y0 + i*30))

            # スコア
            for i,surf in enumerate(self.bottom[side]["scores"]):
                self.screen.blit(surf, (x0+150, y0 + i*30))

            # 合計
            if self.step >= self.STEP_TOTAL_SCORE:
                t = self.bottom[side]["total_now"]
                t_str = f"{t:02d}"

                if side=="L":
                    surf = self.outline(t_str, self.font_total,
                                        (255,255,255),(255,80,80))
                else:
                    surf = self.outline(t_str, self.font_total,
                                        (255,255,255),(80,80,255))

                self.screen.blit(surf, (x0+220, y0))


# ==============================================================
# 実行（テスト用）
# ==============================================================
if __name__ == "__main__":
    rs = ResultScreen("scores.txt")
    rs.run()
