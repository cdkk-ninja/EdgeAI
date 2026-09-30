import os
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import numpy as np
from picamera2 import Picamera2 
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 1. Initialize MediaPipe Gesture Recognizer
path_MediaPipe_models = "MediaPipe/"
base_options = python.BaseOptions(model_asset_path=path_MediaPipe_models+'gesture_recognizer.task')
options = vision.GestureRecognizerOptions(base_options=base_options)
recognizer = vision.GestureRecognizer.create_from_options(options)

# 2. Configure Picamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

# Enable Auto White Balance with continuous autofocus
picam2.set_controls({
    "AfMode": 2,          # Continuous Autofocus
    "AwbMode": 0          # 0 = Auto AWB
})

# Enable window thread for Wayland display compatibility
cv2.namedWindow("Pi 5 Gesture Recognition", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

print("Camera started. Press 'q' in the window to quit.")

try:
    while True:
        frame_bgr = picam2.capture_array("main")
        
        if frame_bgr is None or frame_bgr.size == 0:
            continue

        # Flip horizontally for natural mirror view
        display_frame = cv2.flip(frame_bgr, 1)

        # 1. Convert BGR array to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # 2. Perform gesture recognition
        recognition_result = recognizer.recognize(mp_image)

        # 3. Draw gesture overlays directly onto the correctly-colored display frame
        if recognition_result.gestures and len(recognition_result.gestures[0]) > 0:
            top_gesture = recognition_result.gestures[0][0]
            label = f"{top_gesture.category_name} ({top_gesture.score:.2f})"
            cv2.putText(
                display_frame, 
                label, 
                (30, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1.0, 
                (0, 255, 0), 
                2, 
                cv2.LINE_AA
            )

        # 4. Render display frame (Colors will now be 100% accurate)
        cv2.imshow("Pi 5 Gesture Recognition", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    recognizer.close()
    