import cv2
from sys import path
path.append("..")
from cckk.cckkCameraX import *
from cckk.cckkEdgeAI import *

task = cckkMPHandLandmarker(task_path="../cckk/MediaPipe/", num_hands=1)
# task = cckkMPGestureRecognizer(task_path="../cckk/MediaPipe/", num_hands=1)

cam = cckkCameraX()

try:
    while True:
        if cam.read_frame() is None:
            continue

        if task.run(cam.frame_rgb) and task.result.num_objects() > 0 and task.result.num_landmarks(0) > 8:
            pos = task.result.landmark(0, 8)
            side = task.result.side(0)
            if pos is not None and side is not None:
                print(f"Index finger tip position: ({pos.x}, {pos.y}), Side: {side}")

finally:
    cam.release()
    task.close()
