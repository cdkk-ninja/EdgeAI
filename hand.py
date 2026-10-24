import cv2
from sys import path
path.append('../cckk')
from cckkCameraX import *
from cckkEdgeAI import *

task_lm = cckkMPHandLandmarker(task_path="../cckk/MediaPipe/", num_hands=2)
task_lm.set_result_history(10)

task_g = cckkMPGestureRecognizer(task_path="../cckk/MediaPipe/", num_hands=2)

cam = cckkCameraX()

cv2.namedWindow("Hand Landmarker", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

try:
    while True:
        if cam.read_frame() is None:
            continue

        cam.clear_overlays()
        overlay_hand = cam.create_overlay()  # Overlay for hand lanndmrks and wireframes
        overlay_text = cam.create_overlay()  # Overlay for text

        if task_lm.run(cam.frame_rgb):
            task_lm.result.scale_to = [cam.width, cam.height]
            for h in range(task_lm.result.num_objects()):  # Loop over the number of hands
                for i in range(
                    task_lm.result.num_landmarks(h)
                ):  # For each hand, loop over the landmarks
                    cx, cy = task_lm.result.pos_xy(h, i)
                    cv2.circle(overlay_hand, (cx, cy), 4, (0, 255, 0, 255), -1)

            for h in range(task_lm.result.num_objects()):  # Loop over the number of hands
                wf = task_lm.result.wireframe(h)
                cv2.polylines(
                    overlay_hand,
                    wf,
                    isClosed=False,
                    color=(0, 0, 255, 255),
                    thickness=2,
                )

            hx = task_lm.result.hx_pos_xy(0, 8)  # Index finger ... dot trail
            for cx, cy in hx:
                cv2.circle(overlay_hand, (cx, cy), 4, (255, 0, 0, 255), -1)

            hx_pl = task_lm.result.hx_polyline(0, 4)  # Thumb ... line trail
            cv2.polylines(
                overlay_hand,
                [hx_pl],
                isClosed=False,
                color=(255, 0, 0, 255),
                thickness=2,
            )

            for h in range(task_lm.result.num_objects()):
                cam.putText(task_lm.result.side(h), (30, 40 + h * 40), (0, 255, 0, 255))

        if task_g.run(cam.frame_rgb):
            for h in range(task_g.result.num_objects()):  # Loop over the number of hands
                label = f"{task_g.result.get_obj_attribute(h, 'label')} ({task_g.result.get_obj_attribute(h, 'side')})"
                cam.putText(label, (30, 140 + h * 40), (0, 0, 255, 255))

        final_img = cam.frame_overlays(
            [(overlay_hand, True), (overlay_text, False)], mirror=True
        )
        cv2.imshow("Hand Landmarker", final_img)

        if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' in the window to quit
            break

finally:
    cam.release()
    cv2.destroyAllWindows()
    task_lm.close()
