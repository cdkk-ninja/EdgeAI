import cv2
from sys import path
import pygame

# Initialize Pygame
pygame.init()

# Initial display window (will be adjusted dynamically to match camera dimensions)
window = pygame.display.set_mode((640, 480)) 
pygame.display.set_caption('Skribell')

# Append local pathing for MediaPipe extensions
path.append("..")
from cckk import cckkCameraX, cckkEdgeAI

# Initialize tracking modules
task = cckkEdgeAI.cckkMPHandLandmarker(task_path="../cckk/MediaPipe/", num_hands=2)
task.set_result_history(10)
cam = cckkCameraX.cckkCameraX()

# Read an initial frame to scale the Pygame window dynamically to your exact camera dimensions
if cam.read_frame() is not None:
    window = pygame.display.set_mode((cam.width, cam.height))

clock = pygame.time.Clock()
run = True

try:
    while run:
        # 1. Maintain Pygame Event Loop & Framerate Cap (60 FPS)
        clock.tick(60) 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        # 2. Read Raw Camera Frame
        if cam.read_frame() is None:
            continue

        # 3. Process Computer Vision Analytics 
        # (We run this BEFORE whitening the frame so MediaPipe can actually see your hand!)
        if task.run(cam.frame_rgb):
            task.result.scale_to = [cam.width, cam.height]
            
            # =====================================================================
            # NOW OVERWRITE THE BACKGROUND WITH PURE WHITE
            # MediaPipe already found your landmarks, so it is safe to erase the room now!
            # =====================================================================
            cam.frame_bgr[:] = 255
            
            # Draw Hand Wireframes (Thick Black Connective Lines)
            for h in range(task.result.num_objects()):  
                wf = task.result.wireframe(h)
                cv2.polylines(
                    cam.frame_bgr,
                    wf,
                    isClosed=False,
                    color=(0, 0, 0),  # Pure Black Outline
                    thickness=4,      # Thicker lines for a clean line-art look
                )

            # Draw Index Finger Dot Trail (Blue Dots)
            hx = task.result.hx_pos_xy(0, 8)  
            for cx, cy in hx:
                cv2.circle(cam.frame_bgr, (cx, cy), 4, (255, 0, 0), -1)

            # Draw Thumb Line Trail (Blue Line)
            hx_pl = task.result.hx_polyline(0, 4)  
            cv2.polylines(
                cam.frame_bgr,
                [hx_pl],
                isClosed=False,
                color=(255, 0, 0),
                thickness=2,
            )

            cam.mirror()  

            # Overlay Hand Tracker text descriptions (Drawn in Black)
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
            # If no hand is found, we still want the screen to be white!
            cam.frame_bgr[:] = 255
            cam.mirror()

        # 4. Color Channel Correction
        frame_rgb = cv2.cvtColor(cam.frame_bgr, cv2.COLOR_BGR2RGB)
        frame_swapped = cv2.transpose(frame_rgb)

        # 6. Convert NumPy Array directly to a Pygame Surface
        cam_surface = pygame.surfarray.make_surface(frame_swapped)

        window.blit(cam_surface, (0, 0))
        pygame.display.flip()

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    # Cleanup resource frameworks
    cam.release()
    cv2.destroyAllWindows()
    task.close()
    pygame.quit()
