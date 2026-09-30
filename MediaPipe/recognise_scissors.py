import os
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import numpy as np
from picamera2 import Picamera2 
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 1. Initialize MediaPipe Hand Landmarker
path_MediaPipe_models = "MediaPipe/"
base_options = python.BaseOptions(model_asset_path=path_MediaPipe_models+'hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1
)
landmarker = vision.HandLandmarker.create_from_options(options)

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
    "AwbMode": 0          # Auto White Balance
})

# Enable window thread for Wayland display compatibility
cv2.namedWindow("Pi 5 Scissors Gesture Recognition", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

def is_scissors_gesture(landmarks):
    """
    Landmark Indices:
    - Index Finger: Tip = 8, PIP joint = 6
    - Middle Finger: Tip = 12, PIP joint = 10
    - Ring Finger: Tip = 16, PIP joint = 14
    - Pinky Finger: Tip = 20, PIP joint = 18
    """
    # 1. Index and Middle fingers must be EXTENDED (Tip higher/y-less than PIP joint)
    index_extended = landmarks[8].y < landmarks[6].y
    middle_extended = landmarks[12].y < landmarks[10].y
    
    # 2. Ring and Pinky fingers must be FOLDED (Tip lower/y-greater than PIP joint)
    ring_folded = landmarks[16].y > landmarks[14].y
    pinky_folded = landmarks[20].y > landmarks[18].y
    
    return index_extended and middle_extended and ring_folded and pinky_folded

print("Camera started. Make a scissors gesture (✌️). Press 'q' to quit.")

try:
    while True:
        frame_bgr = picam2.capture_array("main")
        
        if frame_bgr is None or frame_bgr.size == 0:
            continue

        # Flip horizontally for natural mirror view
        display_frame = cv2.flip(frame_bgr, 1)

        # Convert BGR array to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Perform hand landmarker detection
        result = landmarker.detect(mp_image)

        # Check detected hand landmarks
        if result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                # Draw keypoints on screen
                for lm in hand_landmarks:
                    h, w, _ = display_frame.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(display_frame, (cx, cy), 4, (0, 255, 0), -1)

                # Check if gesture matches Scissors
                if is_scissors_gesture(hand_landmarks):
                    cv2.putText(
                        display_frame, 
                        "Gesture: SCISSORS", 
                        (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        1.0, 
                        (0, 255, 0), 
                        2, 
                        cv2.LINE_AA
                    )

        # Render display frame
        cv2.imshow("Pi 5 Scissors Gesture Recognition", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    landmarker.close()
    