import os
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import platform
import cv2
import numpy as np

# ---------------------------------------------------------
# Cross-Platform Camera Wrapper
# ---------------------------------------------------------
IS_RASPBERRY_PI = False

if platform.system() == "Linux":
    try:
        from picamera2 import Picamera2
        IS_RASPBERRY_PI = True
    except ImportError:
        IS_RASPBERRY_PI = False

class CrossPlatformCamera:
    def __init__(self):
        if IS_RASPBERRY_PI:
            print("Initializing Picamera2 (Raspberry Pi)...")
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            self.picam2.configure(config)
            self.picam2.start()
            self.picam2.set_controls({
                "AfMode": 2,  # Continuous Autofocus
                "AwbMode": 0  # Auto White Balance
            })
        else:
            print("Initializing OpenCV VideoCapture (Windows/Webcam)...")
            self.cap = cv2.VideoCapture(0)

    def read_frame(self):
        if IS_RASPBERRY_PI:
            frame_bgr = self.picam2.capture_array("main")
            if frame_bgr is None or frame_bgr.size == 0:
                return None
            return frame_bgr
        else:
            ret, frame_bgr = self.cap.read()
            if not ret:
                return None
            return frame_bgr

    def release(self):
        if IS_RASPBERRY_PI:
            self.picam2.stop()
        else:
            self.cap.release()


# ---------------------------------------------------------
# Main Execution Loop with Transparent Overlay
# ---------------------------------------------------------
cam = CrossPlatformCamera()

# Enable window thread for display compatibility
cv2.namedWindow("Persistent Transparent Overlay", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

print("Camera started. Press 'q' in the window to quit.")

# Persistent variables for overlay canvas
overlay = None

try:
    while True:
        frame_bgr = cam.read_frame()
        if frame_bgr is None or frame_bgr.size == 0:
            continue

        # Flip horizontally for natural mirror view
        display_frame = cv2.flip(frame_bgr, 1)
        h, w, _ = display_frame.shape

        # Initialize the transparent BGRA overlay layer ONCE
        if overlay is None:
            overlay = np.zeros((h, w, 4), dtype=np.uint8)
            
            # 1. Draw a Circle (Blue with opacity 255)
            cv2.circle(overlay, (150, 150), 50, (255, 0, 0, 255), thickness=3, lineType=cv2.LINE_AA)

            # 2. Draw a Polyline (Green polygon)
            pts = np.array([[300, 100], [450, 120], [400, 220], [320, 180]], dtype=np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(overlay, [pts], isClosed=True, color=(0, 255, 0, 255), thickness=3, lineType=cv2.LINE_AA)

            # 3. Draw Text (Red text)
            cv2.putText(
                overlay, 
                "Persistent Transparent Layer", 
                (50, 320), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.8, 
                (0, 0, 255, 255), 
                2, 
                cv2.LINE_AA
            )

        # Alpha blend the transparent overlay onto the camera frame
        alpha = overlay[:, :, 3] / 255.0
        alpha_3ch = np.dstack([alpha, alpha, alpha])
        overlay_bgr = overlay[:, :, :3]

        # FIXED: Use `1.0 - alpha_3ch` instead of `1 - alpha` to match dimensions (480, 640, 3)
        blended_frame = (overlay_bgr * alpha_3ch + display_frame * (1.0 - alpha_3ch)).astype(np.uint8)

        # Render final blended output
        cv2.imshow("Persistent Transparent Overlay", blended_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cam.release()
    cv2.destroyAllWindows()