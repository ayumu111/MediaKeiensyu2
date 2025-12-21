import pygame

class Scene:
    def __init__(self, app=None):
        self.app = app
        self.screen = app.screen if app else None
        self.renderer = app.text_renderer if app else None
        # 次に遷移したいシーン名（文字列）を入れる。Noneなら継続。
        self.next_scene_name = None
        self.quit_requested = False

    def handle_events(self, events):
        """イベント処理"""
        pass

    def update(self, dt):
        """更新処理（dt: 経過時間秒）"""
        pass

    def draw(self, surface):
        """描画処理"""
        pass

    def request_quit(self):
        self.quit_requested = True

    def request_next(self, scene_name: str):
        ##次のシーン名に移るときの関数
        ##()に次のシーン名（文字列）を入れる
        ##次のシーン名はgame_main.pyを参照
        ##次のシーン名が分からないうちはex_gameって入れてくれると動きます！
        self.next_scene_name = scene_name
