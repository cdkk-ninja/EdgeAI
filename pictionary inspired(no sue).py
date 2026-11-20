import cv2
from sys import path
import pygame
import numpy as np
import math

pygame.init()

screen_info = pygame.display.Info()
WINDOW_WIDTH = screen_info.current_w
WINDOW_HEIGHT = screen_info.current_h

window = pygame.display.set_mode(
    (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN
)

pygame.display.set_caption('Skribell')

path.append("..")
from cckk import cckkCameraX, cckkEdgeAI

task = cckkEdgeAI.cckkMPHandLandmarker(
    task_path="../cckk/MediaPipe/",
    num_hands=1
)

cam = cckkCameraX.cckkCameraX()
cam.read_frame()

drawing_canvas = np.zeros(
    (cam.height, cam.width, 3), dtype=np.uint8
)

canvas_history = []
MAX_HISTORY = 15

prev_x, prev_y = None, None
smooth_x, smooth_y = None, None

SMOOTH_FACTOR = 0.4

current_color = (255, 50, 50)
current_thickness = 6

was_pinching = False
is_stroke_active = False



UI_WIDTH = int(cam.width * 0.13)

# Colour buttons
color_buttons = [
    {"name": "Blue", "color": (255, 50, 50),
     "rect": (cam.width - 75, 65, 55, 55)},

    {"name": "Red", "color": (50, 50, 255),
     "rect": (cam.width - 75, 135, 55, 55)},

    {"name": "Green", "color": (40, 200, 40),
     "rect": (cam.width - 75, 205, 55, 55)},

    {"name": "Yellow", "color": (0, 215, 255),
     "rect": (cam.width - 75, 275, 55, 55)},

    {"name": "Black", "color": (20, 20, 20),
     "rect": (cam.width - 75, 345, 55, 55)},
]

# Brush size buttons
size_buttons = [
    {"label": "S", "size": 4,
     "rect": (cam.width - 80, 455, 50, 50)},

    {"label": "M", "size": 10,
     "rect": (cam.width - 80, 515, 50, 50)},

    {"label": "L", "size": 18,
     "rect": (cam.width - 80, 575, 50, 50)},
]

# Undo button
undo_button = {
    "label": "UNDO",
    "rect": (cam.width - 100, 660, 80, 45)
}


def point_in_rect(px, py, rect):
    rx, ry, rw, rh = rect
    return rx <= px <= rx + rw and ry <= py <= ry + rh


def save_history():
    canvas_history.append(drawing_canvas.copy())

    if len(canvas_history) > MAX_HISTORY:
        canvas_history.pop(0)


clock = pygame.time.Clock()
run = True

try:
    while run:

        clock.tick(60)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                run = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    run = False

                elif event.key == pygame.K_SPACE:
                    save_history()

                    drawing_canvas = np.zeros(
                        (cam.height, cam.width, 3),
                        dtype=np.uint8
                    )

                    prev_x, prev_y = None, None
                    smooth_x, smooth_y = None, None

        if cam.read_frame() is None:
            continue

        cam.mirror()

        small_frame = cv2.resize(
            cam.frame_rgb, (320, 240)
        )

        current_mode = "No Hand Detected"

        if task.run(small_frame):

            task.result.scale_to = [cam.width, cam.height]
            cam.frame_bgr[:] = 255

            if task.result.num_objects() > 0:

                thumb_x, thumb_y = task.result.pos_xy(0, 4)
                index_x, index_y = task.result.pos_xy(0, 8)

                wrist_x, wrist_y = task.result.pos_xy(0, 0)
                mcp_x, mcp_y = task.result.pos_xy(0, 9)

                palm_size = math.hypot(
                    mcp_x - wrist_x,
                    mcp_y - wrist_y
                )

                pinch_dist = math.hypot(
                    index_x - thumb_x,
                    index_y - thumb_y
                )

                is_pinching = pinch_dist < (palm_size * 0.35)
                just_pinched = is_pinching and not was_pinching

                index_ext = math.hypot(
                    index_x - mcp_x,
                    index_y - mcp_y
                ) > palm_size * 0.9

                middle_x, middle_y = task.result.pos_xy(0, 12)
                ring_x, ring_y = task.result.pos_xy(0, 16)
                pinky_x, pinky_y = task.result.pos_xy(0, 20)

                middle_ext = math.hypot(
                    middle_x - mcp_x,
                    middle_y - mcp_y
                ) > palm_size * 0.9

                ring_ext = math.hypot(
                    ring_x - mcp_x,
                    ring_y - mcp_y
                ) > palm_size * 0.9

                pinky_ext = math.hypot(
                    pinky_x - mcp_x,
                    pinky_y - mcp_y
                ) > palm_size * 0.9

                if is_pinching:
                    raw_x = int((thumb_x + index_x) / 2)
                    raw_y = int((thumb_y + index_y) / 2)
                else:
                    raw_x, raw_y = index_x, index_y

                if smooth_x is None or smooth_y is None:
                    smooth_x, smooth_y = raw_x, raw_y
                else:
                    smooth_x = int(
                        smooth_x + SMOOTH_FACTOR * (raw_x - smooth_x)
                    )

                    smooth_y = int(
                        smooth_y + SMOOTH_FACTOR * (raw_y - smooth_y)
                    )

                

                if smooth_x > cam.width - UI_WIDTH:

                    current_mode = "Toolbar (Pinch to Select)"

                    prev_x, prev_y = None, None
                    is_stroke_active = False

                    if just_pinched:

                        for btn in color_buttons:
                            if point_in_rect(
                                smooth_x, smooth_y, btn["rect"]
                            ):
                                current_color = btn["color"]

                        for btn in size_buttons:
                            if point_in_rect(
                                smooth_x, smooth_y, btn["rect"]
                            ):
                                current_thickness = btn["size"]

                        if point_in_rect(
                            smooth_x, smooth_y, undo_button["rect"]
                        ):
                            if len(canvas_history) > 0:
                                drawing_canvas = canvas_history.pop()

               

                else:

                    if (
                        not is_pinching
                        and index_ext
                        and middle_ext
                        and ring_ext
                        and pinky_ext
                    ):

                        current_mode = "Eraser (Palm)"

                        if not is_stroke_active:
                            save_history()
                            is_stroke_active = True

                        cv2.circle(
                            drawing_canvas,
                            (smooth_x, smooth_y),
                            50,
                            (0, 0, 0),
                            -1
                        )

                        prev_x, prev_y = None, None

                    elif is_pinching:

                        current_mode = "Drawing (Pinch)"

                        if not is_stroke_active:
                            save_history()
                            is_stroke_active = True

                        if prev_x is not None and prev_y is not None:
                            cv2.line(
                                drawing_canvas,
                                (prev_x, prev_y),
                                (smooth_x, smooth_y),
                                current_color,
                                current_thickness
                            )

                        prev_x, prev_y = smooth_x, smooth_y

                    else:

                        current_mode = "Hovering (Release)"

                        prev_x, prev_y = None, None
                        is_stroke_active = False

                was_pinching = is_pinching

            else:

                prev_x, prev_y = None, None
                smooth_x, smooth_y = None, None

                was_pinching = False
                is_stroke_active = False

            # Draw hand wireframe
            for h in range(task.result.num_objects()):

                wf = task.result.wireframe(h)

                cv2.polylines(
                    cam.frame_bgr,
                    wf,
                    isClosed=False,
                    color=(0, 0, 0),
                    thickness=3
                )

        else:

            cam.frame_bgr[:] = 255

            prev_x, prev_y = None, None
            smooth_x, smooth_y = None, None

            was_pinching = False
            is_stroke_active = False


        stroke_indices = np.any(drawing_canvas > 0, axis=-1)

        cam.frame_bgr[stroke_indices] = drawing_canvas[stroke_indices]

   

        toolbar_x = cam.width - UI_WIDTH

        cv2.rectangle(
            cam.frame_bgr,
            (toolbar_x, 0),
            (cam.width, cam.height),
            (230, 235, 240),
            -1
        )

        cv2.line(
            cam.frame_bgr,
            (toolbar_x, 0),
            (toolbar_x, cam.height),
            (180, 180, 180),
            2
        )


        cv2.putText(
            cam.frame_bgr,
            "COLOURS",
            (toolbar_x + 8, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (30, 30, 30),
            2
        )

        cv2.putText(
            cam.frame_bgr,
            "BRUSH SIZE",
            (toolbar_x + 5, 435),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (30, 30, 30),
            2
        )

     

        for btn in color_buttons:

            x, y, w, h = btn["rect"]

            cv2.rectangle(
                cam.frame_bgr,
                (x, y),
                (x + w, y + h),
                btn["color"],
                -1
            )

            if current_color == btn["color"]:

                cv2.rectangle(
                    cam.frame_bgr,
                    (x - 4, y - 4),
                    (x + w + 4, y + h + 4),
                    (0, 0, 0),
                    3
                )

     
        for btn in size_buttons:

            x, y, w, h = btn["rect"]

            bg_col = (
                (190, 220, 255)
                if current_thickness == btn["size"]
                else (255, 255, 255)
            )

            cv2.rectangle(
                cam.frame_bgr,
                (x, y),
                (x + w, y + h),
                bg_col,
                -1
            )

            cv2.rectangle(
                cam.frame_bgr,
                (x, y),
                (x + w, y + h),
                (100, 100, 100),
                2
            )

            cv2.circle(
                cam.frame_bgr,
                (x + w // 2, y + h // 2),
                btn["size"] // 2 + 2,
                (40, 40, 40),
                -1
            )

            cv2.putText(
                cam.frame_bgr,
                btn["label"],
                (x + w + 2, y + h // 2 + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (30, 30, 30),
                1
            )

        ux, uy, uw, uh = undo_button["rect"]

        undo_bg = (
            (255, 255, 255)
            if len(canvas_history) > 0
            else (210, 210, 210)
        )

        cv2.rectangle(
            cam.frame_bgr,
            (ux, uy),
            (ux + uw, uy + uh),
            undo_bg,
            -1
        )

        cv2.rectangle(
            cam.frame_bgr,
            (ux, uy),
            (ux + uw, uy + uh),
            (80, 80, 80),
            2
        )

        cv2.putText(
            cam.frame_bgr,
            "UNDO",
            (ux + 12, uy + uh // 2 + 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (30, 30, 30),
            2,
            cv2.LINE_AA
        )

        if smooth_x is not None and smooth_y is not None:

            cursor_radius = 12 if was_pinching else 8

            cursor_color = (
                current_color if was_pinching else (0, 200, 0)
            )

            cv2.circle(
                cam.frame_bgr,
                (smooth_x, smooth_y),
                cursor_radius,
                cursor_color,
                -1
            )

            cv2.circle(
                cam.frame_bgr,
                (smooth_x, smooth_y),
                cursor_radius,
                (0, 0, 0),
                2
            )

        text_color = (
            (0, 0, 255) if "Eraser" in current_mode
            else (0, 180, 0) if "Hover" in current_mode
            else (128, 128, 128) if "No Hand" in current_mode
            else (255, 0, 0)
        )

        cv2.putText(
            cam.frame_bgr,
            f"Mode: {current_mode}",
            (30, cam.height - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            text_color,
            2,
            cv2.LINE_AA
        )

        frame_rgb = cv2.cvtColor(
            cam.frame_bgr,
            cv2.COLOR_BGR2RGB
        )

        frame_swapped = cv2.transpose(frame_rgb)

        cam_surface = pygame.surfarray.make_surface(
            frame_swapped
        )

        scaled_surface = pygame.transform.scale(
            cam_surface,
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )

        window.blit(scaled_surface, (0, 0))

        pygame.display.flip()

finally:

    cam.release()
    cv2.destroyAllWindows()
    task.close()
    pygame.quit()
