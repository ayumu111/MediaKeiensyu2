import pygame
import sys
import os
import math
import random
from core.scene import Scene


class TitleScene(Scene):

    # ---------------------------------------
    # 定数まとめ
    # ---------------------------------------
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60

    CUSTOM_FONT_PATH = "title/Paintball_Beta_3.ttf"
    FONT_SIZE = 36
    TEXT_COLOR = (255, 196, 70)
    TEXT_SHADOW = (0, 0, 0)
    TEXT_DELAY_MS = 3000

    LOGO_DELAY_MS = 1000
    CHARS_DELAY_MS = 2000
    FADE_MS = 800

    ATTACK_CYCLE_MS = 1200
    ATTACK_PEAK_MS = 600
    DASH_AMPLITUDE = 24
    SHAKE_DURATION_MS = 180
    SHAKE_INTENSITY = 4

    BACKGROUND_IMG = "title/background.PNG"
    TITLE_LOGO_IMG = "title/logo.PNG"
    CHAR1_IMG = "title/chara1_shadow.PNG"
    CHAR2_IMG = "title/chara2_shadow.PNG"

    HIT_SPARK_IMG = "title/spark.png"
    HIT_SPARK_SCALE = 0.5
    HIT_SPARK_DURATION_MS = 120
    HIT_SPARK_ALPHA = 220

    # ---------------------------------------
    # Utility
    # ---------------------------------------
    def load_font(self, path, size):
        if os.path.isfile(path):
            try:
                return pygame.font.Font(path, size)
            except:
                pass
        print("[WARN] font load failed, using default")
        return pygame.font.Font(None, size)

  

    def load_scaled_image(self, path, max_w=None, max_h=None):
        img = pygame.image.load(path).convert_alpha()
        if max_w is None and max_h is None:
            return img
        w, h = img.get_size()
        scale = 1.0
        if max_w:
            scale = min(scale, max_w / w)
        if max_h:
            scale = min(scale, max_h / h)
        if scale < 1.0:
            img = pygame.transform.smoothscale(
                img, (int(w * scale), int(h * scale)))
        return img


        
    

    def blit_fade(self, surface, img, pos, start_ms, now_ms, fade_ms):
        if now_ms < start_ms:
            return
        alpha = 255
        elapsed = now_ms - start_ms
        if elapsed < fade_ms:
            alpha = int(255 * (elapsed / fade_ms))
        temp = img.copy()
        temp.set_alpha(alpha)
        surface.blit(temp, pos)

    def draw_text_center(self, surface, text, font, y, color, shadow):
        render = font.render(text, True, color)
        shadow_r = font.render(text, True, shadow)
        x = self.SCREEN_WIDTH // 2
        rect = render.get_rect(center=(x, y))
        shadow_rect = shadow_r.get_rect(center=(x + 1, y + 1))
        surface.blit(shadow_r, shadow_rect)
        surface.blit(render, rect)

    

    # ---------------------------------------
    # constructor （SceneManagerに合わせる）
    # ---------------------------------------
    def __init__(self):
        super().__init__()

        # Fonts
        self.font = self.load_font(self.CUSTOM_FONT_PATH, self.FONT_SIZE)

        # Images
        self.bg_img = self.load_scaled_image(
            self.BACKGROUND_IMG, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.logo_img = self.load_scaled_image(
            self.TITLE_LOGO_IMG, max_w=self.SCREEN_WIDTH, max_h=self.SCREEN_HEIGHT//1.05)
        self.char1_img = self.load_scaled_image(
            self.CHAR1_IMG, max_w=self.SCREEN_WIDTH, max_h=self.SCREEN_HEIGHT//1.1)
        self.char2_img = self.load_scaled_image(
            self.CHAR2_IMG, max_w=self.SCREEN_WIDTH, max_h=self.SCREEN_HEIGHT//1.1)

        # spark
        try:
            self.spark_img = pygame.image.load(
                self.HIT_SPARK_IMG).convert_alpha()
            if self.HIT_SPARK_SCALE != 1.0:
                w, h = self.spark_img.get_size()
                self.spark_img = pygame.transform.smoothscale(
                    self.spark_img,
                    (int(w * self.HIT_SPARK_SCALE),
                     int(h * self.HIT_SPARK_SCALE))
                )
        except:
            print("[WARN] No spark image")
            self.spark_img = None

        self.bg_img = pygame.transform.smoothscale(self.bg_img, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

        # rects
        self.logo_rect = self.logo_img.get_rect(
            midtop=(self.SCREEN_WIDTH//2, 20))

        floor = self.SCREEN_HEIGHT - 60
        self.char1_rect = self.char1_img.get_rect(
            midbottom=(self.SCREEN_WIDTH*3//7, floor+40))
        self.char2_rect = self.char2_img.get_rect(
            midbottom=(self.SCREEN_WIDTH*4//7, floor+40))

        # animation
        self.start_time = pygame.time.get_ticks()
        self.shake_until = 0

        # spark
        self.spark_until = 0
        self.spark_pos = (0, 0)

    # ---------------------------------------
    # SceneManager に合わせた API
    # ---------------------------------------
    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                ##次のシーン名が決まったら、"ex_game" の部分を書き換えてください！！！
                self.request_next("ex_game")

    def update(self, dt):
        pass

    def draw(self, surface):
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time

        # shake
        ox = oy = 0
        if now < self.shake_until:
            ox = random.randint(-self.SHAKE_INTENSITY,
                                self.SHAKE_INTENSITY)
            oy = random.randint(-self.SHAKE_INTENSITY,
                                self.SHAKE_INTENSITY)

        # background
        surface.blit(self.bg_img, (ox, oy))

        # logo
        self.blit_fade(surface, self.logo_img,
                       self.logo_rect.topleft,
                       self.LOGO_DELAY_MS, elapsed, self.FADE_MS)

        # characters
        if elapsed >= self.CHARS_DELAY_MS:
            self.draw_characters(surface, now, elapsed, ox, oy)

        # press-space
        if elapsed >= self.TEXT_DELAY_MS:
            if (now // 400) % 2 == 0:
                self.draw_text_center(
                    surface, "Press SPACE to Start",
                    self.font,
                    self.SCREEN_HEIGHT - 100,
                    self.TEXT_COLOR,
                    self.TEXT_SHADOW
                )

    # ---------------------------------------
    # character animation
    # ---------------------------------------
    def draw_characters(self, surface, now, elapsed, ox, oy):

        cycle_t = (elapsed - self.CHARS_DELAY_MS) % self.ATTACK_CYCLE_MS
        progress = cycle_t / self.ATTACK_CYCLE_MS

        dash = int(self.DASH_AMPLITUDE * math.sin(2 * math.pi * progress))

        c1_pos = (self.char1_rect.x + dash, self.char1_rect.y)
        c2_pos = (self.char2_rect.x - dash, self.char2_rect.y)

        # fade-in
        chars_elapsed = elapsed - self.CHARS_DELAY_MS
        alpha = min(255, int(255 * (chars_elapsed / self.FADE_MS)))

        img1 = self.char1_img.copy()
        img2 = self.char2_img.copy()
        img1.set_alpha(alpha)
        img2.set_alpha(alpha)

        surface.blit(img1, (c1_pos[0]+ox, c1_pos[1]+oy))
        surface.blit(img2, (c2_pos[0]+ox, c2_pos[1]+oy))

        # peak hit flash
        if abs(cycle_t - self.ATTACK_PEAK_MS) < 80:

            h1 = c1_pos[0] + self.char1_rect.width
            h2 = c2_pos[0]
            hx = (h1 + h2)//2
            hy = c1_pos[1] + self.char1_rect.height//2

            if self.spark_img:
                self.spark_until = now + self.HIT_SPARK_DURATION_MS
                self.spark_pos = (hx+ox, hy+oy)

            flash = pygame.Surface(
                (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 120))
            surface.blit(flash, (0, 0))

            self.shake_until = now + self.SHAKE_DURATION_MS

        if self.spark_img and now < self.spark_until:
            s = self.spark_img.copy()
            s.set_alpha(self.HIT_SPARK_ALPHA)
            rect = s.get_rect(center=self.spark_pos)
            surface.blit(s, rect)
