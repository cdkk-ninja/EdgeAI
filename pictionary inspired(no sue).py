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

task = cckkEdgeAI.cckkMPHandLandmarker(task_path="../cckk/MediaPipe/", num_hands=1) 
cam = cckkCameraX.cckkCameraX()

cam.read_frame()

drawing_canvas = np.zeros((cam.height, cam.width, 3), dtype=np.uint8)
prev_x, prev_y = None, None

# Variables for smoothing coordinates (
smooth_x, smooth_y = None, None
SMOOTH_FACTOR = 0.75  

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
                    drawing_canvas = np.zeros((cam.height, cam.width, 3), dtype=np.uint8)
                    prev_x, prev_y = None, None
                    smooth_x, smooth_y = None, None

        if cam.read_frame() is None:
            continue

        cam.mirror()  

        small_frame = cv2.resize(cam.frame_rgb, (320, 240))
        current_mode = "No Hand Detected"

        if task.run(small_frame):
            task.result.scale_to = [cam.width, cam.height]
            cam.frame_bgr[:] = 255  
            
            if task.result.num_objects() > 0:
                # Raw coordinates of the index tip
                raw_x, raw_y = task.result.pos_xy(0, 8)
                
                # Apply smoothing filter to the raw coordinates
                if smooth_x is None or smooth_y is None:
                    smooth_x, smooth_y = raw_x, raw_y
                else:
                    smooth_x = int(smooth_x + SMOOTH_FACTOR * (raw_x - smooth_x))
                    smooth_y = int(smooth_y + SMOOTH_FACTOR * (raw_y - smooth_y))
                
                # Calculate palm size baseline using MCP and Wrist
                wrist_x, wrist_y = task.result.pos_xy(0, 0)
                mcp_x, mcp_y = task.result.pos_xy(0, 9)
                palm_size = math.hypot(mcp_x - wrist_x, mcp_y - wrist_y)
                
                # Track finger extension status
                # Index (8), Middle (12), Ring (16), Pinky (20) compared to MCP joint (9)
                # Thumb (4) compared to CMC joint (2)
                thumb_ext = math.hypot(task.result.pos_xy(0, 4)[0] - task.result.pos_xy(0, 2)[0], task.result.pos_xy(0, 4)[1] - task.result.pos_xy(0, 2)[1]) > palm_size * 0.75
                index_ext = math.hypot(task.result.pos_xy(0, 8)[0] - mcp_x, task.result.pos_xy(0, 8)[1] - mcp_y) > palm_size * 0.9
                middle_ext = math.hypot(task.result.pos_xy(0, 12)[0] - mcp_x, task.result.pos_xy(0, 12)[1] - mcp_y) > palm_size * 0.9
                ring_ext = math.hypot(task.result.pos_xy(0, 16)[0] - mcp_x, task.result.pos_xy(0, 16)[1] - mcp_y) > palm_size * 0.9
                pinky_ext = math.hypot(task.result.pos_xy(0, 20)[0] - mcp_x, task.result.pos_xy(0, 20)[1] - mcp_y) > palm_size * 0.9

                # Check strict gestures
                if index_ext and not middle_ext and not ring_ext and not pinky_ext:
                    current_mode = "Drawing Mode (Index)"
                    if prev_x is not None and prev_y is not None:
                        cv2.line(drawing_canvas, (prev_x, prev_y), (smooth_x, smooth_y), (255, 0, 0), 6)
                    prev_x, prev_y = smooth_x, smooth_y
                elif index_ext and middle_ext and ring_ext and pinky_ext:
                    current_mode = "Eraser Mode (Palm)"
                    cv2.circle(drawing_canvas, (smooth_x, smooth_y), 50, (0, 0, 0), -1)
                    prev_x, prev_y = None, None 
                else:
                    current_mode = "Fist / Invalid Gesture"
                    prev_x, prev_y = None, None
            else:
                prev_x, prev_y = None, None
                smooth_x, smooth_y = None, None

            for h in range(task.result.num_objects()):  
                wf = task.result.wireframe(h)
                cv2.polylines(
                    cam.frame_bgr,
                    wf,
                    isClosed=False,
                    color=(0, 0, 0),  
                    thickness=4,      
                )
        else:
            cam.frame_bgr[:] = 255
            prev_x, prev_y = None, None
            smooth_x, smooth_y = None, None

        stroke_indices = np.any(drawing_canvas > 0, axis=-1)
        cam.frame_bgr[stroke_indices] = drawing_canvas[stroke_indices]

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

finally:
    cam.release()
    cv2.destroyAllWindows()
    task.close()
    pygame.quit()
