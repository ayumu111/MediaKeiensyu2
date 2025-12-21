import pygame
from core.scene import Scene

class ExResultScene(Scene):
    def __init__(self):
        super().__init__()
        self.font = pygame.font.SysFont(None, 64)

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                # 何かキーで終了（またはタイトルへ戻すなど）
                self.request_next("score")
                #self.request_quit()
                # あるいは self.request_next("title")

    def draw(self, surface):
        surface.fill((50, 0, 50))
        text = self.font.render("ex_result!", True, (255, 255, 255))
        rect = text.get_rect(center=surface.get_rect().center)
        surface.blit(text, rect)
