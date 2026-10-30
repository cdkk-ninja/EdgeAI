import pygame
from sys import path

path.append("..")
import cckk.game.cckkPyGameApp as cckkPyGameApp
import cckk.game.cckkUtils as cckkUtils
import cckk.game.cckkSprite as cckkSprite
import cckk.game.cckkSpriteManager as cckkSpriteManager
import cckk.game.cckkSpriteExtra as cckkSpriteExtra
import cckk.game.cckkGameAI as cckkGameAI
import cckk.cckkEdgeAI as cckkEdgeAI

# --------------------------------------------------


class Manager_Canvas(cckkSpriteManager.SpriteManager):
    def __init__(self, canvas_rect, canvas_style: dict = {}):
        super().__init__("Canvas Manager")
        self._canvas = cckkSpriteExtra.Sprite_Canvas(
            "Canvas", canvas_rect, canvas_style
        )
        self.add(self._canvas)

    def event(self, e):
        dealt_with = super().event(e)
        if e.type == cckkUtils.EVENT_GAME_CONTROL:
            # Consumes click and unclick even if not within the canvas
            if e.action == "MouseLeftClick" and self.use_mouse:
                dealt_with = self._canvas.start_painting(e.info["pos"])
            if e.action == "MouseUnclick" and self.use_mouse:
                dealt_with = self._canvas.end_painting()
            if e.action == "MouseMotion" and self.use_mouse:
                dealt_with = self._canvas.paint(e.info["pos"])
            if e.action == "UpdatePaint":
                if e.info["colour"] is not None:
                    self._canvas.paint_colour = e.info["colour"]
                dealt_with = True
        return dealt_with


# --------------------------------------------------


class Manager_PaintControls(cckkSpriteManager.SpriteManager):
    def __init__(self, palette_rect: cckkUtils.cckkRect, brushes_rect: cckkUtils.cckkRect):
        super().__init__("Palette Manager")
        palette_colours: list[list[str]] = [
            ["red", "blue"],
            ["green", "yellow"],
            ["orange", "magenta"],
            ["purple", "pink"],
            ["black", "snow"],
        ]
        self._palette = cckkSpriteExtra.Sprite_ColouredGrid("Palette", palette_colours)
        self._palette.setup_grid_fit(
            cols_rows=(2, 5),
            rect=palette_rect,
            event_on_click=cckkUtils.EventManager.gc_event("Palette"),
        )
        self.add(self._palette)

        shape_style = {
            "fillcolour": "black",
            "outlinecolour": None,
            "shape": "Ellipse",
        }
        # Creates 4x2 grid of styles, each with an independent copy of the brush style
        shape_styles: list[list[dict]] = [
            [shape_style.copy() for _ in range(2)] 
            for _ in range(4)
        ]
        brush_max_size = brushes_rect.width/2
        brush_iter = 1
        for i in range(0, 4):
            for j in range(0, 2):
                shape_styles[i][j]["width"] = brush_max_size * brush_iter/9
                shape_styles[i][j]["height"] = brush_max_size * brush_iter/9
                brush_iter += 1

        self._brushes = Sprite_Brushes(rect=brushes_rect, xcols=2, yrows=4, shape_styles=shape_styles)
        self.add(self._brushes)

    def event(self, e):
        dealt_with = super().event(e)
        if e.type == cckkUtils.EVENT_GAME_CONTROL:
            if e.action == "Palette" and self.use_mouse:
                colour_rgb = self._palette.get_pixel(x=e.pos[0], y=e.pos[1], inc_alpha=False)
                if colour_rgb is not None:
                    ev = cckkUtils.EventManager.gc_event(
                        "UpdatePaint", colour=colour_rgb, width=None
                    )
                    cckkUtils.EventManager.post(ev)

                dealt_with = True
        return dealt_with


# --------------------------------------------------

class Sprite_Brushes(cckkSprite.SpriteGridSet):
    def __init__(self, rect:cckkUtils.cckkRect, xcols:int, yrows:int, shape_styles: list[list[dict]] = [[]]):
        super().__init__(name="Brushes", rect=rect, xcols=xcols, yrows=yrows, margin=2)
        for i in range(xcols):
            for j in range(yrows):
                offset = i+j*xcols
                # ev_click = None if evl_click is None else evl_click[offset]
                brush = cckkSprite.Sprite_Shape(name=f"Shape[x={i}, y={j}]", rect=rect, style=shape_styles[j][i]) # Size will be corrected by add_shape_xy()
                self.add_shape_xy(brush, i, j)

# --------------------------------------------------

class MyAITask(cckkGameAI.cckkCameraAITask):
    def __init__(self):
        super().__init__()
        self.task = cckkEdgeAI.cckkMPGestureRecognizer(
            task_path="../cckk/MediaPipe/", num_hands=1
        )

    def run_task(self) -> bool:
        if (
            super().run_task()
            and self.task is not None
            and self.task.result is not None
        ):
            if self.task.result.num_landmarks(0) > 8:
                pos = self.task.result.landmark(0, 8, scale_to=[-800, 600])
                side = ""
                if (
                    isinstance(self.task.result, cckkEdgeAI.cckkMediaPipeResult)
                    and hasattr(self.task.result, "side")
                    and callable(self.task.result.side)
                ):
                    side = self.task.result.side(0)
                if pos is not None and side == "Right":
                    ev = cckkUtils.EventManager.gc_event(
                        "IndexFingerTipMotion", pos=(pos.x, pos.y)
                    )
                    cckkUtils.EventManager.post(ev)
        return self._task_success


# --------------------------------------------------


class MyGame(cckkPyGameApp.PyGameApp):
    def init(self) -> bool:
        self.add_ai_task(MyAITask())

        super().init()
        margin = 10
        pal_sq = 40
        canvas_rect = cckkUtils.cckkRect(self.boundary).size_delta(
            -3 * margin - 2 * pal_sq, -2 * margin
        )
        canvas_rect.left = margin
        canvas_style = {
            "fillcolour": "snow",
            "outlinecolour": "blue",
        }

        palette_rect = cckkUtils.cckkRect(
            self.boundary.right - 2 * pal_sq - margin, margin, 2 * pal_sq, 5 * pal_sq
        )
        brushes_rect = cckkUtils.cckkRect(
            palette_rect.left, palette_rect.bottom + 30, palette_rect.width, pal_sq * 4
        )

        # Palette must be first so that Canvas doesn't consume mouse clicks
        self.add_sprite_mgr(Manager_PaintControls(palette_rect, brushes_rect))
        self.add_sprite_mgr(Manager_Canvas(canvas_rect, canvas_style))

        self.event_mgr.event_map(
            {
                pygame.K_q: "Quit",
                pygame.K_s: "StartGame",
                pygame.K_e: "GameOver",
                pygame.K_UP: "MoveUp",
                pygame.K_DOWN: "MoveDown",
                pygame.K_LEFT: "MoveLeft",
                pygame.K_RIGHT: "MoveRight",
            }
        )
        return True

    def update(self):
        super().update()


# ---------------------------------------------------

app_config = {
    "width": 1000,
    "height": 600,
    "background_fill": "burlywood",
    "caption": "Test cckkPyGameApp Canvas",
    "auto_start": True,
}


MyGame(app_config).execute()
