import pygame           ##必須
from core.scene import Scene                ##必須

class ExGameScene(Scene):
    def __init__(self):
        super().__init__()
        self.font = pygame.font.SysFont(None, 48)
        self.timer = 0.0

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                # Escでタイトルへ戻る例
                self.request_next("title")

    def update(self, dt):
        self.timer += dt
        # 例えば 5秒たったら結果画面へ
        if self.timer >= 5.0:
            self.request_next("ex_result")

    def draw(self, surface):
        surface.fill((0, 60, 120))
        msg = f"ex_game... {self.timer:.1f}s"
        text = self.font.render(msg, True, (255, 255, 255))
        rect = text.get_rect(center=surface.get_rect().center)
        surface.blit(text, rect)
