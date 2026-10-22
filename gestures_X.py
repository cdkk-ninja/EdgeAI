import cv2
from sys import path

path.append("..")
from cckk import cckkCameraX
from cckk import cckkEdgeAI

task = cckkEdgeAI.cckkMPGestureRecognizer(task_path="../cckk/MediaPipe/", num_hands=2)
cam = cckkCameraX.cckkCameraX()

cv2.namedWindow("Gesture Recognition", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

try:
    while True:
        if cam.read_frame() is None:
            continue

        if task.run(cam.frame_rgb):
            for h in range(task.result.num_objects()):  # Loop over the number of hands
                cx, cy = task.result.pos_xy(h, 8, [cam.width, cam.height])
                cv2.circle(cam.frame_bgr, (cx, cy), 4, (0, 255, 0), -1)

            cam.mirror()  # Mirror image after adding landmarks, and before adding text

            for h in range(task.result.num_objects()):  # Loop over the number of hands
                label = f"{task.result.get_obj_attribute(h, 'label')} ({task.result.get_obj_attribute(h, 'side')})"
                cv2.putText(
                    cam.frame_bgr,
                    label,
                    (30, 40 + h * 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )
        else:
            cam.mirror()

        cv2.imshow("Gesture Recognition", cam.frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' in the window to quit
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
    task.close()
