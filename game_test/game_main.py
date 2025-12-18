import pygame
from core.manager import SceneManager
from scenes.title_scene_class import TitleScene
from scenes.ex_game_scene_class import ExGameScene      ##例（本番は使わない）
from scenes.ex_result_scene_class import ExResultScene  ##例（本番は使わない）
##ここに自分のクラス名とファイル名を追加してください！
from scenes.score_screen import ScoreScene



def create_scene(name: str):        
    ##ここに自分のクラス名とシーン名を追加してください！
    ##シーンの順番通りに並んでると、わかりやすくて嬉しいです！
    ##request_nextで指定する文字列はここを参照！
    """名前→シーンの生成（Factory）"""
    if name == "title":
        return TitleScene()
    elif name == "ex_game":        ##例（本番は使わない）
        return ExGameScene()
    elif name == "ex_result":      ##例（本番は使わない）
        return ExResultScene()
    elif name == "score":  
        return ScoreScene()
    else:
        raise ValueError(f"Unknown scene name: {name}")

def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    clock = pygame.time.Clock()

    manager = SceneManager(initial_scene=TitleScene(), scene_factory=create_scene)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        running = manager.run_frame(screen, dt)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
