# To Do
# - AI task .. boundary is hard-coded

import pygame
import random
from sys import path

path.append("..")
import cckk.game.cckkPyGameApp as cckkPyGameApp
import cckk.game.cckkUtils as cckkUtils
import cckk.game.cckkSprite as cckkSprite
import cckk.game.cckkSpriteManager as cckkSpriteManager
import cckk.game.cckkSpriteExtra as cckkSpriteExtra
import cckk.game.cckkApp as cckkApp
import cckk.game.cckkGameAI as cckkGameAI
import cckk.cckkCameraX as cckkCameraX
import cckk.cckkEdgeAI as cckkEdgeAI

# --------------------------------------------------

class Sprite_Ball(cckkSprite.Sprite):
    files = ["ball_red.png", "ball_yellow.png", "ball_green.png", "ball_blue.png"]

    def __init__(self, value, limits):
        super().__init__()
        self.value = value
        self.load_image_from_file(self.files[value - 1])
        self.rect.left = random.randint(
            int(limits.width * 0.2), int(limits.width * 0.8)
        )
        self.rect.top = 10
        speed = value * 3 + 5
        angle = random.randint(45, 135)
        self.rect.set_speed_angle(speed, angle)
        self.rect.bounce_cor = self.rect.perfect_bounce
        bounce_event = cckkUtils.EventManager.gc_event("Boundary", ball_id=self.uuid)
        self.rect.add_limit(
            cckkUtils.Physics_Limit(
                limits,
                cckkUtils.LIMIT_KEEP_INSIDE,
                cckkUtils.AT_LIMIT_BOUNCE,
                bounce_event,
            )
        )
        self.rect.go()

    def update(self):
        super().update()
        self.rect.move_physics()

# --------------------------------------------------

class Manager_Ball(cckkSpriteManager.SpriteManager):
    def __init__(self, limits, total, at_a_time, player_num):
        super().__init__("Ball Manager", player=player_num)
        self._limits = limits
        self._at_a_time = at_a_time
        self._total = total
        self.balls_left = total
        self.add_balls()

    def add_balls(self):
        if self.game_is_active:
            current_balls = len(self.sprites())
            new_balls = self._at_a_time - current_balls
            if new_balls > self.balls_left:
                new_balls = self.balls_left

            for i in range(new_balls):
                value = random.randint(1, len(Sprite_Ball.files))
                ball = Sprite_Ball(value, self._limits)
                self.add(ball)
                self.balls_left -= 1

    def start_game(self):
        super().start_game()
        self.balls_left = self._total
        self.add_balls()

    def end_game(self):
        self.balls_left = 0
        self.empty()
        super().end_game()

    def update(self):
        super().update()
        sprite_collisions = self.find_collisions()
        for sprite, rect in sprite_collisions:
            sprite.rect.dynamic_limit(
                cckkUtils.Physics_Limit(
                    rect, cckkUtils.LIMIT_COLLISION, cckkUtils.AT_LIMIT_BOUNCE
                )
            )

    def event(self, e):
        dealt_with = super().event(e)
        if not dealt_with and e.type == cckkUtils.EVENT_GAME_CONTROL:
            if e.action == "Boundary":
                if e.at_limit_y & cckkUtils.AT_LIMIT_BOTTOM:
                    self.kill_uuid(e.info["ball_id"])
                    self.add_balls()
        return dealt_with

    def check_bat_hits(self, bat):
        for ball in self.sprites():
            score_event = cckkUtils.EventManager.gc_event(
                "UpdateScore", score=ball.value, player=self.player
            )
            ball.rect.dynamic_limit(
                cckkUtils.Physics_Limit(
                    bat.rect,
                    cckkUtils.LIMIT_KEEP_OUTSIDE,
                    cckkUtils.AT_LIMIT_Y_BOUNCE_Y,
                    score_event,
                )
            )

# --------------------------------------------------

class Sprite_Bat(cckkSprite.Sprite):
    def __init__(self, limits):
        super().__init__("Bat")
        self.load_image_from_file("bat.png")
        self.rect.centerx = limits.width / 2
        self.rect.top = limits.height * 0.9
        self.rect.add_limit(
            cckkUtils.Physics_Limit(
                limits, cckkUtils.LIMIT_KEEP_INSIDE, cckkUtils.AT_LIMIT_X_HOLD_POS_X
            )
        )

# --------------------------------------------------

class Manager_Bat(cckkSpriteManager.SpriteManager):
    def __init__(self, limits, control_type, name="Bat Manager"):
        super().__init__(name, control_type=control_type)
        self._bat = Sprite_Bat(limits)
        self.add(self._bat)

    def event(self, e):
        dealt_with = False
        if e.type == cckkUtils.EVENT_GAME_CONTROL:
            if e.action == "MouseMotion" and self.use_mouse:
                x, y = e.info["pos"]
                self._bat.rect.move_to(x, None)
                dealt_with = True
            if e.action == "IndexFingerTipMotion":
                x, y = e.info["pos"]
                self._bat.rect.move_to(x, None)
                dealt_with = True
            if e.action == "BatLeft" and self.use_keyboard:
                self._bat.rect.move_physics(-25, 0)
                dealt_with = True
            if e.action == "BatRight" and self.use_keyboard:
                self._bat.rect.move_physics(25, 0)
                dealt_with = True
        return dealt_with

# --------------------------------------------------

class Manager_Scoreboard(cckkSpriteManager.SpriteManager):
    def __init__(self, limits, game_time, player_num):
        super().__init__("Scoreboard Manager", player=player_num)
        self._game_time = game_time

        text_style = {
            "fillcolour": None,
            "outlinecolour": None,
            "align_horiz": "L",
            "width": 200,
            "height": 35,
        }

        tb_score = cckkSprite.Sprite_TextBox("Score", style=text_style)
        tb_score.set_text_format("Score: {0}", 0)
        tb_score.rect.topleft = (limits.left + 10, limits.top + 5)
        self.add(tb_score)
        self.score = 0

        self._timer = cckkUtils.Timer(
            self._game_time,
            cckkUtils.EVENT_GAME_TIMER_1,
            auto_start=self.game_is_active,
        )
        tb_time_left = cckkSprite.Sprite_TextBox("Time Left", style=text_style)
        tb_time_left.set_text_format("Time Left: {0:0.1f}", 0)
        tb_time_left.rect.midtop = (limits.left + limits.width * 0.5, limits.top + 5)
        self.add(tb_time_left)

        tb_balls_left = cckkSprite.Sprite_TextBox("Balls Left", style=text_style)
        tb_balls_left.set_text_format("Balls Left: {0}", 0)
        tb_balls_left.rect.topright = (limits.right - 10, limits.top + 5)
        self.add(tb_balls_left)
        self.balls_left = 0

        self._game_over = cckkSpriteExtra.Sprite_GameOver(limits)
        self._game_over.rect.center = (
            limits.left + limits.width * 0.5,
            limits.top + limits.height * 0.5,
        )

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, new_score):
        self._score = new_score
        ss = self.sprite("Score")
        if ss is not None:
            ss.set_text(self.score)

    @property
    def balls_left(self):
        return self._balls_left

    @balls_left.setter
    def balls_left(self, new_balls_left):
        self._balls_left = new_balls_left
        bl = self.sprite("Balls Left")
        if bl is not None:
            bl.set_text(self.balls_left)

    def update(self):
        super().update()
        tl = self.sprite("Time Left")
        if tl is not None:
            tl.set_text(self._timer.time_left)

    def start_game(self):
        super().start_game()
        self.score = 0
        self._timer.start()
        self.remove(self._game_over)  # Hide Game Over

    def end_game(self):
        self.add(self._game_over)  # Display Game Over
        super().end_game()

    def event(self, e):
        dealt_with = False
        if e.type == cckkUtils.EVENT_GAME_CONTROL:
            if e.action == "UpdateScore":
                if e.info["player"] == self.player:
                    self.score += e.info["score"]
                    dealt_with = True
        return dealt_with

# --------------------------------------------------

class Manager_Court(cckkSpriteManager.SpriteManager):
    def __init__(self, limits):
        super().__init__("Court")

        court_style = {"fillcolour": "cadetblue3", "outlinecolour": "black"}
        court = cckkSprite.Sprite_Shape("Court", limits, court_style)
        self.add(court)

# --------------------------------------------------

class MyAITask (cckkGameAI.cckkCameraAITask):
    def __init__(self):
        super().__init__()
        # self.task  = cckkEdgeAI.cckkMPHandLandmarker(task_path="../cckk/MediaPipe/", num_hands=1)
        self.task = cckkEdgeAI.cckkMPGestureRecognizer(task_path="../cckk/MediaPipe/", num_hands=1)

    def run_task(self) -> bool:
        if super().run_task() and self.task is not None and self.task.result is not None:
            if self.task.result.num_landmarks(0) > 8:
                pos = self.task.result.landmark(0, 8, scale_to=[-800, 600])
                side = ""
                if hasattr( self.task.result, 'side' ) and callable( self.task.result.side):
                    side = self.task.result.side(0)
                if pos is not None and side == "Right":
                    ev = cckkUtils.EventManager.gc_event("IndexFingerTipMotion", pos=(pos.x, pos.y))
                    cckkUtils.EventManager.post(ev)
        return self._task_success

# --------------------------------------------------

class MyGame(cckkPyGameApp.PyGameApp):
    def init(self) -> bool:
        self._ai_task = MyAITask()
        self.add_ai_task(self._ai_task)

        super().init()
        court = cckkUtils.cckkRect(
            10, 10, (self.boundary.width - 20), self.boundary.height - 20
        )

        self._court_mgr = Manager_Court(court)
        self.add_sprite_mgr(self._court_mgr)

        self._ball_mgr = Manager_Ball(court, 10, 3, 1)
        self.add_sprite_mgr(self._ball_mgr)

        self._bat_mgr = Manager_Bat(court, cckkUtils.CONTROL_KEYBOARD)
        self._bat_mgr.set_config("player", 1)
        self.add_sprite_mgr(self._bat_mgr)

        self._scoreboard_mgr = Manager_Scoreboard(court, 15, 1)
        self.add_sprite_mgr(self._scoreboard_mgr)

        key_map = {
            pygame.K_q: "Quit",
            pygame.K_s: "StartGame",
            pygame.K_LEFT: "BatLeft",
            pygame.K_RIGHT: "BatRight",
        }
        self.event_mgr.event_map(key_event_map=key_map)
        self.event_mgr.user_event(cckkUtils.EVENT_GAME_TIMER_1, "GameOver")

        return True

    def update(self):
        super().update()
        bat1 = self.sprite("Bat Manager", "Bat", player=1)
        self._ball_mgr.check_bat_hits(bat1)
        self._scoreboard_mgr.balls_left = self._ball_mgr.balls_left
        self._scoreboard_mgr.balls_left = self.loops_per_sec

app_config = {
    "width": 800,
    "height": 600,
    "background_fill": "burlywood",
    "caption": "Test cckkPyGameApp using Bouncing Ball",
    "image_path": "./Sandbox/Images/",
    "auto_start": False,
    "key_repeat_time": 30,  # msecs (lower=faster)
}

MyGame(app_config).execute()
