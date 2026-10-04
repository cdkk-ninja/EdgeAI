import cv2
from sys import path
path.append('..')

from cckk import cckkCameraX

cam = cckkCameraX.cckkCameraX()

# Enable window thread for Wayland display compatibility on Raspberry Pi OS
cv2.namedWindow("Cross-Platform Camera Stream", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

try:
    while True:
        frame = cam.read_frame()
        if frame is None:
            continue

        cv2.imshow("Cross-Platform Camera Stream", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cam.release()
    cv2.destroyAllWindows()