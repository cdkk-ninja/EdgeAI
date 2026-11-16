import pygame
from sys import path

path.append("..")
import cckk.game.cckkPyGameApp as cckkPyGameApp
import cckk.game.cckkUtils as cckkUtils
import cckk.game.cckkSprite as cckkSprite
import cckk.game.cckkSpriteManager as cckkSpriteManager
import cckk.game.cckkSpriteExtra as cckkSpriteExtra
import cckk.game.cckkColours as cckkColours
import cckk.game.cckkGameAI as cckkGameAI
import cckk.cckkEdgeAI as cckkEdgeAI

# --------------------------------------------------


class MySpriteManager(cckkSpriteManager.SpriteManager):
    def __init__(self, **sm_config):
        super().__init__(name="My Sprite Manager", **sm_config)
        self._hand = Sprite_HandWireframe(
            wf_style={
                "width": self.get_config("width"),
                "height": self.get_config("height"),
            }
        )
        self.add(self._hand)

    def event(self, e):
        dealt_with = super().event(e)
        if e.type == cckkUtils.EVENT_GAME_CONTROL:
            wf0 = getattr(e, "wireframe", None)
            wf: list[list[tuple[int, int]]] = [[]]
            if wf0 is not None and getattr(e, "pos_01_scale", False):
                wf = [
                    [
                        cckkEdgeAI.cckkPosition.scale_xy(
                            pos_xy=pt,
                            scale_to=(self.width, self.height),
                            mirror=True,
                            pos_min=(0.0, 0.0),
                            pos_max=(1.0, 1.0),
                        )
                        for pt in sublist
                    ]
                    for sublist in wf0
                ]

            if e.action == "RightHandMotion":
                self._hand.invisible = False
                self._hand.setup_wireframe(wireframe=wf)

            if e.action == "RightHandAbsent":
                self._hand.invisible = True

        return dealt_with


# --------------------------------------------------


class Sprite_HandWireframe(cckkSprite.Sprite_Shape):
    def __init__(self, name="HandWireframe", wf_style={}):
        default_style = {
            "shape": "Wireframe",
            "outlinecolour": "red",
            "outlinewidth": 3,
        }
        wf_style = cckkUtils.merge_dicts(default_style, wf_style)
        super().__init__(name=name, rect=None, style=wf_style)


# --------------------------------------------------


class MyAITask(cckkGameAI.cckkCameraAITask):
    def __init__(self):
        super().__init__()
        self.task = cckkEdgeAI.cckkMPGestureRecognizer(
            task_path="../cckk/MediaPipe/", num_hands=1
        )
        self._last_event_sent: str = ""

    def run_task(self) -> bool:
        if (
            super().run_task()
            and self.task is not None
            and self.task.result is not None
            and isinstance(self.task.result, cckkEdgeAI.cckkMediaPipeResult)
            and hasattr(self.task.result, "side")
            and callable(self.task.result.side)
        ):
            if self.task.result.side(0) == "Right":
                wf = self.task.result.wireframe(scale_to=None)
                wireframe_tuples: list[list[tuple[float, float]]] = [
                    [(float(pt[0]), float(pt[1])) for pt in arr.reshape(-1, 2)]
                    for arr in wf
                ]
                ev = cckkUtils.EventManager.gc_event(
                    "RightHandMotion",
                    wireframe=wireframe_tuples,
                    pos_01_scale=True,
                )
                cckkUtils.EventManager.post(ev)
                self._last_event_sent = "RightHandMotion"
        elif self._last_event_sent != "RightHandAbsent":
            ev = cckkUtils.EventManager.gc_event("RightHandAbsent")
            cckkUtils.EventManager.post(ev)
            self._last_event_sent = "RightHandAbsent"

        return self._task_success


# --------------------------------------------------


class MyGame(cckkPyGameApp.PyGameApp):
    def init(self) -> bool:
        self.add_ai_task(MyAITask())
        super().init()
        self.add_sprite_mgr(MySpriteManager(width=self.width, height=self.height))
        self.event_mgr.event_map(
            {
                pygame.K_q: "Quit",
            }
        )
        return True


# ---------------------------------------------------

app_config = {
    # "width": 1000,
    # "height": 600,
    "full_screen": True,
    "background_fill": "burlywood",
    "caption": "Test AI Controls",
    "auto_start": True,
}

MyGame(app_config).execute()
