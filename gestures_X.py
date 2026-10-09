import cv2
from sys import path
path.append('..')
from cckk import cckkCameraX
from cckk import cckkEdgeAI

task =  cckkEdgeAI.cckkMPGestureRecognizer(task_path="../cckk/MediaPipe/")
cam = cckkCameraX.cckkCameraX()

cv2.namedWindow("Gesture Recognition", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

print("Camera started. Press 'q' in the window to quit.")

try:
    while True:
        if cam.read_frame() is None:
            continue

        if task.run(cam.frame_rgb):
            label = f"{task.result.label(0)} ({task.result.score(0):.2f})"
            cv2.putText(cam.frame_bgr, label, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)

            cx, cy, cz =  task.result.pos_xyz(0, 8, [cam.width, cam.height])
            cv2.circle(cam.frame_bgr, (cx, cy), 4, (0, 255, 0), -1)

        cv2.imshow("Gesture Recognition", cam.frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
    task.close()
