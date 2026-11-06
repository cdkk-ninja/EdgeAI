import cv2
from sys import path
import pygame
import numpy as np
import math

pygame.init()

screen_info = pygame.display.Info()
WINDOW_WIDTH = screen_info.current_w
WINDOW_HEIGHT = screen_info.current_h

window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN) 
pygame.display.set_caption('Skribell')

path.append("..")
from cckk import cckkCameraX, cckkEdgeAI

task = cckkEdgeAI.cckkMPHandLandmarker(task_path="../cckk/MediaPipe/", num_hands=2)
task.set_result_history(10)
cam = cckkCameraX.cckkCameraX()

cam.read_frame()

drawing_canvas = np.zeros((cam.height, cam.width, 3), dtype=np.uint8)
prev_x, prev_y = None, None

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
                    drawing_canvas.fill(0)

        if cam.read_frame() is None:
            continue

        current_mode = "No Hand Detected"

        if task.run(cam.frame_rgb):
            task.result.scale_to = [cam.width, cam.height]
            cam.frame_bgr[:] = 255
            
            if task.result.num_objects() > 0:
                ix, iy = task.result.pos_xy(0, 8)
                
                wrist_x, wrist_y = task.result.pos_xy(0, 0)
                mcp_x, mcp_y = task.result.pos_xy(0, 9)
                palm_size = math.hypot(mcp_x - wrist_x, mcp_y - wrist_y)
                
                extended_fingers = 0
                tip_ids = [4, 8, 12, 16, 20]
                for tip_id in tip_ids:
                    tx, ty = task.result.pos_xy(0, tip_id)
                    dist = math.hypot(tx - mcp_x, ty - mcp_y)
                    if dist > palm_size * 0.9:
                        extended_fingers += 1

                if extended_fingers >= 4:
                    current_mode = "Eraser Mode (Palm)"
                    if prev_x is not None and prev_y is not None:
                        cv2.circle(drawing_canvas, (ix, iy), 30, (0, 0, 0), -1)
                    prev_x, prev_y = ix, iy
                elif extended_fingers <= 1:
                    current_mode = "Fist (Not Drawing)"
                    prev_x, prev_y = None, None
                else:
                    current_mode = "Drawing Mode (Index)"
                    if prev_x is not None and prev_y is not None:
                        cv2.line(drawing_canvas, (prev_x, prev_y), (ix, iy), (255, 0, 0), 6)
                    prev_x, prev_y = ix, iy
            else:
                prev_x, prev_y = None, None

            for h in range(task.result.num_objects()):  
                wf = task.result.wireframe(h)
                cv2.polylines(
                    cam.frame_bgr,
                    wf,
                    isClosed=False,
                    color=(0, 0, 0),  
                    thickness=4,      
                )
                
                cv2.putText(
                    cam.frame_bgr,
                    task.result.side(h),
                    (30, 40 + h * 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 0),
                    2,
                    cv2.LINE_AA,
                )
        else:
            cam.frame_bgr[:] = 255
            prev_x, prev_y = None, None

        cam.mirror()  
        
        # Super-fast direct array mapping to copy blue strokes over white canvas
        drawing_mask = cv2.cvtColor(drawing_canvas, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(drawing_mask, 1, 255, cv2.THRESH_BINARY)
        cam.frame_bgr[alpha > 0] = drawing_canvas[alpha > 0]

        text_color = (0, 0, 255) if "Eraser" in current_mode else ((128, 128, 128) if "No Hand" in current_mode else (255, 0, 0))
        cv2.putText(
            cam.frame_bgr,
            f"Mode: {current_mode}",
            (30, cam.height - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            text_color,
            2,
            cv2.LINE_AA,
        )

        frame_rgb = cv2.cvtColor(cam.frame_bgr, cv2.COLOR_BGR2RGB)
        frame_swapped = cv2.transpose(frame_rgb)

        cam_surface = pygame.surfarray.make_surface(frame_swapped)
        scaled_surface = pygame.transform.scale(cam_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))

        window.blit(scaled_surface, (0, 0))
        pygame.display.flip()

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
    task.close()
    pygame.quit()
