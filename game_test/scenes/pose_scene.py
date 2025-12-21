
# -*- coding: utf-8 -*-
import threading
import traceback
from typing import Optional, List, Tuple

import pygame
import numpy as np
import cv2
import os

from core.scene import Scene
from scenes.pose_estimate import PoseEstimator, PoseEstimatorConfig


class PoseEstimationScene(Scene):
    """
    複数画像に対して骨格推定を行うシーン。
    推定中は「estimating now...」を表示。完了後は結果画像を切り替えて表示。
    Sキーで現在表示中の結果画像を保存。
    """
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60

    CUSTOM_FONT_PATH = "title/Paintball_Beta_3.ttf"
    FONT_SIZE = 36
    TEXT_COLOR = (255, 196, 70)
    TEXT_SHADOW = (0, 0, 0)
    TEXT_DELAY_MS = 3000

    def load_font(self, path, size):
        if os.path.isfile(path):
            try:
                return pygame.font.Font(path, size)
            except:
                pass
        print("[WARN] font load failed, using default")
        return pygame.font.Font(None, size)

    def __init__(
        self,
        app=None,
        image_path: Optional[str] = None,            # ★ 単一画像（後方互換）
        image_paths: Optional[List[str]] = None,     # ★ 複数画像
        on_black: bool = False,
        save_dir: Optional[str] = None
    ):
        super().__init__(app)
        # ★ 引数の互換対応：image_paths 優先、無ければ image_path をリスト化
        if image_paths and len(image_paths) > 0:
            self.image_paths = image_paths
        elif image_path is not None:
            self.image_paths = [image_path]
        else:
            self.image_paths = []

        self.on_black = on_black
        self.save_dir = save_dir

        # Fonts
        self.font = self.load_font(self.CUSTOM_FONT_PATH, self.FONT_SIZE)

        # 推定器の準備（必要に応じて device="cuda" やしきい値の設定）
        cfg = PoseEstimatorConfig(
            model_path="yolo11n-pose.pt",
            device=None,          # "cuda" なら高速
            kpt_radius=5,
            line_width=2,
            draw_on_black_bg=on_black,
            score_threshold=None,
        )
        self.estimator = PoseEstimator(cfg)

        # スレッド関連
        self._thread: Optional[threading.Thread] = None
        self._done: bool = False
        self._error: Optional[str] = None

        # ★ 結果表示用（複数）
        self._surfaces: List[pygame.Surface] = []
        self._infos: List[dict] = []
        self._index: int = 0

    # -------------------------
    # ライフサイクル
    # -------------------------
    def on_enter(self):
        """シーン入場時に非同期で推論開始"""
        if not self.image_paths:
            self._error = "no image paths provided."
            self._done = True
            return

        def worker():
            try:
                self._surfaces.clear()
                self._infos.clear()
                for path in self.image_paths:
                    drawn_bgr, info = self.estimator.process_image(path, on_black=self.on_black)
                    # Pygame Surface へ変換
                    surf = self._bgr_to_surface(drawn_bgr)
                    self._surfaces.append(surf)
                    # 画像パスも持たせる（保存名に使用）
                    info = {**info, "image_path": path}
                    self._infos.append(info)
            except Exception as e:
                self._error = f"error in estimating: {e}\n{traceback.format_exc()}"
            finally:
                self._done = True

        self._done = False
        self._error = None
        self._surfaces.clear()
        self._infos.clear()
        self._index = 0
        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def on_exit(self):
        """必要に応じて後片付け"""
        self._thread = None

    # -------------------------
    # イベント処理
    # -------------------------
    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                self.request_quit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    # 任意の次シーン名に遷移（game_main.py の登録に合わせる）
                    self.request_next("ex_game")
                # ★ 画像の切替（←/→ または A/D）
                elif e.key in (pygame.K_LEFT, pygame.K_a):
                    self._move_index(-1)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self._move_index(+1)
                # ★ 保存（S）
                elif e.key == pygame.K_s:
                    self._save_current_result()

    def _move_index(self, delta: int):
        if not self._surfaces:
            return
        self._index = (self._index + delta) % len(self._surfaces)

    # -------------------------
    # 更新処理（今回は特に無し）
    # -------------------------
    def update(self, dt):
        pass

    # -------------------------
    # 描画処理
    # -------------------------
    def draw(self, surface):
        surface.fill((0, 0, 0))  # 背景

        if not self._done:
            # 推論中
            self.draw_text_center(
                surface, "estimating now...",
                self.font,
                surface.get_height() - 100,   # ★ surface の高さに合わせる
                self.TEXT_COLOR,
                self.TEXT_SHADOW
            )
            return

        if self._error is not None:
            # エラー表示
            self.draw_text_center(
                surface, "error occurred.",
                self.font,
                surface.get_height() - 100,   # ★ surface の高さに合わせる
                self.TEXT_COLOR,
                self.TEXT_SHADOW
            )
            if self.renderer:
                self._safe_draw_text(surface, self._error, (20, 20))
            return

        if not self._surfaces:
            self.draw_text_center(
                surface, "no result image.",
                self.font,
                surface.get_height() - 100,
                self.TEXT_COLOR,
                self.TEXT_SHADOW
            )
            return

        # 結果画像を中央に表示（現在インデックス）
        cur_surf = self._surfaces[self._index]
        cur_info = self._infos[self._index]
        self._blit_center(surface, cur_surf)

        # 補助情報を描く
        if self.renderer and cur_info:
            persons = cur_info.get("num_persons", 0)
            fname = os.path.basename(cur_info.get("image_path", ""))
            self._safe_draw_text(surface, f"file: {fname}", (20, 20))
            self._safe_draw_text(surface, f"person: {persons}", (20, 50))
            self._safe_draw_text(surface, "[←/→] switch  [S] save  [ESC] next", (20, 80))

    # -------------------------
    # 保存機能
    # -------------------------
    def _save_current_result(self):
        """現在表示中の結果画像を指定ディレクトリへ保存する。"""
        try:
            # 保存先ディレクトリが未指定ならデフォルトを使用
            save_dir = self.save_dir or "outputs_selected"
            os.makedirs(save_dir, exist_ok=True)

            info = self._infos[self._index]
            
            raw = info.get("raw")
            width = info.get("width")
            height = info.get("height")

            # ★ 黒背景キャンバスを作る（高さ×幅×3 の BGR）
            black_bg = np.zeros((height, width, 3), dtype=np.uint8)

            # ★ 黒背景に骨格のみを描画
            drawn_bgr = raw.plot(
                img=black_bg,   # ← base.copy() ではなく黒キャンバス
                kpt_radius=self.estimator.cfg.kpt_radius,
                line_width=self.estimator.cfg.line_width
            )

            #cv2.imwrite(save_path, drawn_bgr)


            original = os.path.basename(info.get("image_path", f"result_{self._index}.png"))
            stem, _ = os.path.splitext(original)
            save_name = f"{stem}_pose.png"
            save_path = os.path.join(save_dir, save_name)

            cv2.imwrite(save_path, drawn_bgr)

            # 画面下部に保存完了メッセージ（簡易）
            if self.screen is not None:
                self._safe_draw_text(
                    self.screen,
                    f"saved: {save_path}",
                    (20, self.screen.get_height() - 40),
                    color=(120, 220, 120)
                )
        except Exception as e:
            if self.screen is not None:
                self._safe_draw_text(self.screen, f"save failed: {e}", (20, 110), color=(255, 120, 120))

    # -------------------------
    # ヘルパー
    # -------------------------
    def _bgr_to_surface(self, img_bgr: np.ndarray) -> pygame.Surface:
        """OpenCV(BGR) を Pygame Surface へ変換する。"""
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]
        surf = pygame.image.frombuffer(img_rgb.tobytes(), (w, h), "RGB")
        return surf.convert()

    def _blit_center(self, surface: pygame.Surface, child: pygame.Surface):
        sw, sh = surface.get_size()
        cw, ch = child.get_size()
        x = (sw - cw) // 2
        y = (sh - ch) // 2
        surface.blit(child, (x, y))

    def draw_text_center(self, surface, text, font, y, color, shadow):
        # ★ 画面幅に合わせて中央寄せ（SCREEN_WIDTH 固定ではなく surface 実寸を使用）
        render = font.render(text, True, color)
        shadow_r = font.render(text, True, shadow)
        x = surface.get_width() // 2
        rect = render.get_rect(center=(x, y))
        shadow_rect = shadow_r.get_rect(center=(x + 1, y + 1))
        surface.blit(shadow_r, shadow_rect)
        surface.blit(render, rect)

    def _safe_draw_text(self, surface: pygame.Surface, text: str, pos: Tuple[int, int], color=(255, 255, 255), size: int = 28):
        """
        TextRenderer の API が不明でも安全にテキストを描画するフォールバック。
        - renderer があれば、よくあるメソッド名を順に試す
        - どれも無ければ pygame 標準フォントで描画
        """
        if self.renderer is not None:
            # よくある候補を順番に試す
            candidates_with_surface_first = ("draw_text", "draw", "blit_text", "write")
            for name in candidates_with_surface_first:
                if hasattr(self.renderer, name):
                    try:
                        getattr(self.renderer, name)(surface, text, pos, color=color)
                        return
                    except Exception:
                        pass
            # Surface を返すタイプ
            candidates_return_surface = ("render_text", "render", "text")
            for name in candidates_return_surface:
                if hasattr(self.renderer, name):
                    try:
                        font_surface = getattr(self.renderer, name)(text, color=color)
                        surface.blit(font_surface, pos)
                        return
                    except Exception:
                        pass
        # フォールバック：pygame 標準フォント
        font = pygame.font.Font(None, size)
        rend = font.render(text, True, color)
        surface.blit(rend, pos)
