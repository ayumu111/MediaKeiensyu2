import pygame
from core.scene import Scene

class SceneManager:
    def __init__(self, initial_scene: Scene, scene_factory):
        """
        initial_scene: 最初に表示するシーンインスタンス
        scene_factory: 名前からシーンを生成する関数 例) lambda name: ...
        """
        self.current_scene = initial_scene
        self.scene_factory = scene_factory

    def switch_if_needed(self):
        """シーン側が next_scene_name をセットしていたら切替"""
        if self.current_scene.quit_requested:
            return False  # メインループ終了

        if self.current_scene.next_scene_name:
            next_name = self.current_scene.next_scene_name
            self.current_scene = self.scene_factory(next_name)
        return True

    def run_frame(self, surface, dt):
        """1フレーム分のイベント処理→更新→描画"""
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                self.current_scene.request_quit()

        self.current_scene.handle_events(events)
        self.current_scene.update(dt)
        self.current_scene.draw(surface)

        return self.switch_if_needed()
