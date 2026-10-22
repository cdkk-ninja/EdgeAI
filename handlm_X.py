import cv2
from sys import path

path.append("..")
from cckk import cckkCameraX, cckkEdgeAI

task = cckkEdgeAI.cckkMPHandLandmarker(task_path="../cckk/MediaPipe/", num_hands=2)
task.set_result_history(10)
cam = cckkCameraX.cckkCameraX()

cv2.namedWindow("Hand Landmarker", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

try:
    while True:
        if cam.read_frame() is None:
            continue

        task.scale_to = [cam.width, cam.height]
        if task.run(cam.frame_rgb):
            for h in range(task.result.num_objects()):  # Loop over the number of hands
                for i in range(
                    task.result.num_landmarks(h)
                ):  # For each hand, loop over the landmarks
                    cx, cy = task.result.pos_xy(h, i, [cam.width, cam.height])
                    cv2.circle(cam.frame_bgr, (cx, cy), 4, (0, 255, 0), -1)

            for h in range(task.result.num_objects()):  # Loop over the number of hands
                wf = task.result.wireframe(h, [cam.width, cam.height])
                cv2.polylines(
                    cam.frame_bgr,
                    wf,
                    isClosed=False,
                    color=(0, 0, 255),
                    thickness=2,
                )

            hx = task.result.hx_pos_xy(0, 8, [cam.width, cam.height])  # Index finger ... dot trail
            for cx, cy in hx:
                cv2.circle(cam.frame_bgr, (cx, cy), 4, (255, 0, 0), -1)

            hx_pl = task.result.hx_polyline(0, 4, [cam.width, cam.height])  # Thumb ... line trail
            cv2.polylines(
                cam.frame_bgr,
                [hx_pl],
                isClosed=False,
                color=(255, 0, 0),
                thickness=2,
            )

            cam.mirror()  # Mirror image after adding landmarks, and before adding text

            for h in range(task.result.num_objects()):
                cv2.putText(
                    cam.frame_bgr,
                    task.result.side(h),
                    (30, 40 + h * 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )
        else:
            cam.mirror()

        cv2.imshow("Hand Landmarker", cam.frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' in the window to quit
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
    task.close()
