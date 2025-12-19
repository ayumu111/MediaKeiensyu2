import pygame
from core.manager import SceneManager
from scenes.title_scene_class import TitleScene
from scenes.ex_game_scene_class import ExGameScene      ##例（本番は使わない）
from scenes.ex_result_scene_class import ExResultScene  ##例（本番は使わない）
##ここに自分のクラス名とファイル名を追加してください！
from scenes.score_screen import ScoreScene
from common import AppContext

from scenes.howto_scene_class import HowToScene
from scenes.roulette_scene_class import RouletteScene
from scenes.camera_scene_class import CameraScene


def create_scene_factory(app):
    def create_scene(name: str):
        ##ここに自分のクラス名とシーン名を追加してください！
        ##シーンの順番通りに並んでると、わかりやすくて嬉しいです！
        ##request_nextで指定する文字列はここを参照！
        """名前→シーンの生成（Factory）"""
        if name == "title":
            return TitleScene()

        # 工藤が追加
        elif name == "howto":
            return HowToScene(app)
        elif name == "roulette":
            return RouletteScene(app)
        elif name == "camera":
            return CameraScene(app)

        elif name == "score":
            return ScoreScene()

        # 例（本番は使わない）
        elif name == "ex_game":
            return ExGameScene()
        elif name == "ex_result":
            return ExResultScene()

        else:
            raise ValueError(f"Unknown scene name: {name}")

    return create_scene

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    app = AppContext(screen)
    manager = SceneManager(
        initial_scene=TitleScene(),
        scene_factory=create_scene_factory(app),
    )

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        running = manager.run_frame(screen, dt)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
