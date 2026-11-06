import cv2
from sys import path
import pygame

# Initialize Pygame
pygame.init()


screen_info = pygame.display.Info()
WINDOW_WIDTH = screen_info.current_w
WINDOW_HEIGHT = screen_info.current_h

# Pygame Window
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN) 
pygame.display.set_caption('Skribell')

path.append("..")
from cckk import cckkCameraX, cckkEdgeAI

# Initialize tracking modules
task = cckkEdgeAI.cckkMPHandLandmarker(task_path="../cckk/MediaPipe/", num_hands=2)
task.set_result_history(10)
cam = cckkCameraX.cckkCameraX()

# Read an initial frame to let the camera set its internal properties
cam.read_frame()

clock = pygame.time.Clock()
run = True

try:
    while run:
        # 60 fps
        clock.tick(60) 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            # 
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False

       
        if cam.read_frame() is None:
            continue

        # Process Computer Vision Analytics
        if task.run(cam.frame_rgb):
            task.result.scale_to = [cam.width, cam.height]
            
            # Overwrite the background with pure white after landmarks are found
            cam.frame_bgr[:] = 255
            
            # Draw Hand outlines
            for h in range(task.result.num_objects()):  
                wf = task.result.wireframe(h)
                cv2.polylines(
                    cam.frame_bgr,
                    wf,
                    isClosed=False,
                    color=(0, 0, 0),  
                    thickness=4,      
                )

            # Draw Index Finger Dot Trail (Blue Dots)
            hx = task.result.hx_pos_xy(0, 8)  
            for cx, cy in hx:
                cv2.circle(cam.frame_bgr, (cx, cy), 4, (255, 0, 0), -1)

            
            cam.mirror()  

            # Overlay Hand Tracker text descriptions 
            for h in range(task.result.num_objects()):
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
            cam.mirror()

        # Color Channel Correction & Transpose
        frame_rgb = cv2.cvtColor(cam.frame_bgr, cv2.COLOR_BGR2RGB)
        frame_swapped = cv2.transpose(frame_rgb)


        cam_surface = pygame.surfarray.make_surface(frame_swapped)

        # Scale the Surface to Fit the Fullscreen Window
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
