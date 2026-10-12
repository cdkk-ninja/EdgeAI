import cv2
from sys import path
path.append('..')
from cckk import cckkCameraX
from cckk import cckkEdgeAI

task =  cckkEdgeAI.cckkMPHandLandmarker(task_path="../cckk/MediaPipe/")
cam = cckkCameraX.cckkCameraX()

cv2.namedWindow("Hand Landmarker", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

try:
    while True:
        if cam.read_frame() is None:
            continue

        if task.run(cam.frame_rgb):
            for i in range(task.result.num_positions(0)):
                cx, cy, cz =  task.result.pos_xyz(0, i, [cam.width, cam.height])
                cv2.circle(cam.frame_bgr, (cx, cy), 4, (0, 255, 0), -1)

            for i in range(task.result.num_polylines(0)):
                pl = task.result.polyline(0, i)
                cv2.polylines(cam.frame_bgr, [pl], isClosed=False, color=(0, 0, 255), thickness=2)

            cam.mirror()  # Mirror image after adding landmarks, and before adding text

            cv2.putText(cam.frame_bgr, task.result.side(0), (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)


        cv2.imshow("Hand Landmarker", cam.frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' in the window to quit
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
    task.close()
