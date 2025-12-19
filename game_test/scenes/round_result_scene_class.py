import pygame
import math
import os
from core.scene import Scene


class RoundResultScene(Scene):
    """ResultScreen の演出を Scene 版として忠実移植したもの"""

    def __init__(self, score_file="scores.txt"):
        super().__init__()

        # =========================
        # 画面サイズ
        # =========================
        self.W, self.H = 800, 600

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
        cur = os.path.dirname(__file__)
        main = os.path.join(cur, "../font/Paintball_Beta_3.ttf")
        title = os.path.join(cur, "../font/IoEI.ttf")

        self.font_title = pygame.font.Font(title, 80)
        self.font_players = pygame.font.Font(main, 50)
        self.font_labels = pygame.font.Font(title, 30)
        self.font_score = pygame.font.Font(main, 30)
        self.font_total = pygame.font.Font(main, 90)

        # =========================
        # スコア
        # =========================
        self.load_scores(score_file)

        # =========================
        # STEP 管理（元コード完全一致）
        # =========================
        self.STEP_BG = 0
        self.STEP_TITLE = 1
        self.STEP_LINE = 2
        self.STEP_PLAYERS = 3
        self.STEP_CHART_FRAME = 4
        self.STEP_SCORE_LABELS = 5
        self.STEP_SCORE_NUMBERS = 6
        self.STEP_CHART_SCORE = 7
        self.STEP_TOTAL = 8

        self.step = self.STEP_BG
        self.score_progress = 0.0
        self.SCORE_GROW_SPEED = 0.015

        # =========================
        # 描画準備
        # =========================
        self.prepare_assets()

        self.saved = False

    # ==================================================
    # 入力
    # ==================================================
    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    self.request_next("score")
                elif e.key == pygame.K_ESCAPE:
                    self.request_next("final_result")

    # ==================================================
    # 更新
    # ==================================================
    def update(self, dt):
        if self.step == self.STEP_BG:
            if self.fade_in(self.bg, 255):
                self.step = self.STEP_TITLE

        elif self.step == self.STEP_TITLE:
            if self.fade_in(self.title_surf, 255):
                self.step = self.STEP_LINE

        elif self.step == self.STEP_LINE:
            if self.fade_in(self.line_surf, 255):
                self.step = self.STEP_PLAYERS

        elif self.step == self.STEP_PLAYERS:
            done1 = self.fade_in(self.p1_surf, 255)
            done2 = self.fade_in(self.p2_surf, 255)
            if done1 and done2:
                self.step = self.STEP_CHART_FRAME

        elif self.step == self.STEP_CHART_FRAME:
            doneL = self.fade_in(self.circle_left, 255)
            doneR = self.fade_in(self.circle_right, 255)
            if doneL and doneR:
                self.step = self.STEP_SCORE_LABELS


        elif self.step == self.STEP_SCORE_LABELS:
            done = True
            for side in self.bottom.values():
                for s in side["label_surfs"]:
                    if not self.fade_in(s, 255):
                        done = False
            if done:
                self.step = self.STEP_SCORE_NUMBERS

        elif self.step == self.STEP_SCORE_NUMBERS:
            done = True
            for side in self.bottom.values():
                for s in side["scores_surfs"]:
                    if not self.fade_in(s, 255):
                        done = False
            if done:
                self.step = self.STEP_CHART_SCORE

        elif self.step == self.STEP_CHART_SCORE:
            self.score_progress = min(self.score_progress + self.SCORE_GROW_SPEED, 1.0)
            if self.score_progress >= 1.0:
                self.step = self.STEP_TOTAL

        elif self.step == self.STEP_TOTAL:
            for side in self.bottom.values():
                if side["total_now"] < side["total_target"]:
                    side["total_now"] += 1
        
        # ★ ここで1回だけ保存
        if not self.saved:
            self.append_score("1Pscores.txt", self.total_1)
            self.append_score("2Pscores.txt", self.total_2)
            self.saved = True
    
    def append_score(self, filename, score):
        ##score をカンマ区切りで追記保存
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if text:
                text += f",{score}"
            else:
                text = str(score)
        else:
            text = str(score)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)


    # ==================================================
    # 描画
    # ==================================================
    def draw(self, surface):
        surface.blit(self.bg, (0, 0))

        if self.step >= self.STEP_TITLE:
            surface.blit(self.title_surf, self.title_pos)
        if self.step >= self.STEP_LINE:
            surface.blit(self.line_surf, self.line_pos)
        if self.step >= self.STEP_PLAYERS:
            surface.blit(self.p1_surf, self.p1_pos)
            surface.blit(self.p2_surf, self.p2_pos)

        surface.blit(self.circle_left, (50, 200))
        surface.blit(self.circle_right, (450, 200))

        if self.step >= self.STEP_CHART_FRAME:
            for surf, ang in self.label_surfs:
                rad = math.radians(ang)
                for cx in (200, 600):
                    x = cx + 150 * math.cos(rad)
                    y = 350 + 150 * math.sin(rad)
                    surface.blit(surf, surf.get_rect(center=(x, y)))

        if self.step >= self.STEP_CHART_SCORE:
            self.draw_score_triangle(surface, (200, 350), self.s1)
            self.draw_score_triangle(surface, (600, 350), self.s2)

        self.draw_bottom(surface)

    # ==================================================
    # 内部
    # ==================================================
    def load_scores(self, score_file):
        v = list(map(int, open(score_file, encoding="utf-8").read().split(",")))
        self.s1 = v[:3]
        self.s2 = v[3:]
        self.total_1 = sum(self.s1)
        self.total_2 = sum(self.s2)

    def outline(self, text, font, color, outline, w=2):
        base = font.render(text, True, color)
        surf = pygame.Surface((base.get_width()+w*2, base.get_height()+w*2), pygame.SRCALPHA)
        for dx in (-w, w):
            for dy in (-w, w):
                surf.blit(font.render(text, True, outline), (dx+w, dy+w))
        surf.blit(base, (w, w))
        return surf

    def prepare_assets(self):
        self.bg = pygame.Surface((self.W, self.H))
        self.bg.fill(self.BG_COLOR)
        self.bg.set_alpha(0)

        self.title_surf = self.outline("とくてん", self.font_title, (255,255,255), (0,0,0))
        self.title_surf.set_alpha(0)
        self.title_pos = self.title_surf.get_rect(center=(400, 80))

        self.line_surf = pygame.Surface((4, 450))
        self.line_surf.fill((0, 0, 0))
        self.line_surf.set_alpha(0)
        self.line_pos = self.line_surf.get_rect(center=(400, 350))

        self.p1_surf = self.outline("1P", self.font_players, (255,255,255), (255,80,80))
        self.p2_surf = self.outline("2P", self.font_players, (255,255,255), (80,80,255))
        self.p1_surf.set_alpha(0)
        self.p2_surf.set_alpha(0)
        self.p1_pos = self.p1_surf.get_rect(center=(200,150))
        self.p2_pos = self.p2_surf.get_rect(center=(600,150))

        self.circle_left = pygame.Surface((300,300), pygame.SRCALPHA)
        self.circle_right = pygame.Surface((300,300), pygame.SRCALPHA)
        self.circle_left.set_alpha(0)
        self.circle_right.set_alpha(0)

        pygame.draw.circle(self.circle_left, self.CIRCLE_COLOR, (150,150), 120)
        pygame.draw.circle(self.circle_right, self.CIRCLE_COLOR, (150,150), 120)
        self.draw_base_triangle(self.circle_left)
        self.draw_base_triangle(self.circle_right)

        labels = [("ダイナミック",-90),("あんてい",30),("こせい",150)]
        self.label_surfs = [(self.font_labels.render(t, True, self.LABEL_COLOR), a) for t,a in labels]

        self.bottom = {
            "L": {"x":50, "y":480, "scores":self.s1, "total_target":self.total_1},
            "R": {"x":430, "y":480, "scores":self.s2, "total_target":self.total_2},
        }
        for side in self.bottom.values():
            side["label_surfs"] = [self.font_labels.render(t, True, (0,0,0)) for t,_ in labels]
            side["scores_surfs"] = [self.outline(str(s), self.font_score, (255,255,255), (255,80,80)) for s in side["scores"]]
            for s in side["label_surfs"] + side["scores_surfs"]:
                s.set_alpha(0)
            side["total_now"] = 0

    def fade_in(self, surf, target, step=5):
        a = surf.get_alpha() or 0
        a = min(a+step, target)
        surf.set_alpha(a)
        return a == target

    def draw_base_triangle(self, surface):
        pts = []
        for i in range(3):
            ang = math.radians(-90+i*120)
            pts.append((150+120*math.cos(ang),150+120*math.sin(ang)))
        pygame.draw.polygon(surface, self.BASE_TRI_COLOR, pts, 3)

    def draw_score_triangle(self, surface, center, scores):
        surf = pygame.Surface((300,300), pygame.SRCALPHA)
        pts = []
        for i,sc in enumerate(scores):
            ang = math.radians(-90+i*120)
            r = (sc/10)*120*self.score_progress
            pts.append((150+r*math.cos(ang),150+r*math.sin(ang)))
        pygame.draw.polygon(surf, self.SCORE_COLOR, pts)
        pygame.draw.polygon(surf, self.SCORE_EDGE_COLOR, pts, 2)
        surface.blit(surf, (center[0]-150, center[1]-150))

    def draw_bottom(self, surface):
        for side in self.bottom.values():
            for i,s in enumerate(side["label_surfs"]):
                surface.blit(s, (side["x"], side["y"]+i*30))
            for i,s in enumerate(side["scores_surfs"]):
                surface.blit(s, (side["x"]+150, side["y"]+i*30))
            if self.step >= self.STEP_TOTAL:
                t = f"{side['total_now']:02d}"
                col = (255,80,80) if side is self.bottom["L"] else (80,80,255)
                surface.blit(self.outline(t, self.font_total, (255,255,255), col), (side["x"]+220, side["y"]))
