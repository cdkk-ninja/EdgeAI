import os
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import numpy as np
import math
from picamera2 import Picamera2 
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 1. Initialize Hand Landmarker with multi-hand support
path_MediaPipe_models = "MediaPipe/"
base_options = python.BaseOptions(model_asset_path=path_MediaPipe_models+'hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2  # <--- Set to 2 to track both hands simultaneously
)
landmarker = vision.HandLandmarker.create_from_options(options)

# 2. Configure Picamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

# Enable continuous autofocus and auto white balance
picam2.set_controls({
    "AfMode": 2,
    "AwbMode": 0
})

cv2.namedWindow("Pi 5 Dual Hand Recognition", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

def distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

def classify_hand_gesture(landmarks):
    """Evaluates 3D landmarks for a single hand and returns the gesture label."""
    wrist = landmarks[0]

    # Calculate distances from wrist to finger tips and joints
    index_dist = distance(landmarks[8], wrist)
    middle_dist = distance(landmarks[12], wrist)
    ring_dist = distance(landmarks[16], wrist)
    pinky_dist = distance(landmarks[20], wrist)

    index_mcp_dist = distance(landmarks[5], wrist)
    middle_mcp_dist = distance(landmarks[9], wrist)
    ring_mcp_dist = distance(landmarks[13], wrist)
    pinky_mcp_dist = distance(landmarks[17], wrist)

    # Extension states
    index_ext = index_dist > 1.2 * index_mcp_dist
    middle_ext = middle_dist > 1.2 * middle_mcp_dist
    ring_ext = ring_dist > 1.2 * ring_mcp_dist
    pinky_ext = pinky_dist > 1.2 * pinky_mcp_dist

    # Gesture Logic
    if index_ext and middle_ext and not ring_ext and not pinky_ext:
        return "Scissors ✂️️"
    elif index_ext and middle_ext and ring_ext and pinky_ext:
        return "Open Palm 🖐️"
    elif not index_ext and not middle_ext and not ring_ext and not pinky_ext:
        return "Fist ✊"
    elif index_ext and not middle_ext and not ring_ext and not pinky_ext:
        return "Pointing ☝️"
    
    return "Unknown"

print("Camera active. Show up to 2 hands! Press 'q' to quit.")

try:
    while True:
        frame_bgr = picam2.capture_array("main")
        
        if frame_bgr is None or frame_bgr.size == 0:
            continue

        display_frame = cv2.flip(frame_bgr, 1)

        # Prepare frame for MediaPipe
        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Run detection
        result = landmarker.detect(mp_image)

        # Process each detected hand independently
        if result.hand_landmarks:
            for idx, hand_landmarks in enumerate(result.hand_landmarks):
                # Draw landmark points for this hand
                for lm in hand_landmarks:
                    h, w, _ = display_frame.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(display_frame, (cx, cy), 4, (0, 255, 0), -1)

                # Classify the gesture for this specific hand
                gesture_name = classify_hand_gesture(hand_landmarks)

                # Get the wrist coordinate to position the label near the hand
                h, w, _ = display_frame.shape
                wrist_x = int(hand_landmarks[0].x * w)
                wrist_y = int(hand_landmarks[0].y * h) - 20

                # Render label above each individual hand
                cv2.putText(
                    display_frame, 
                    f"Hand {idx+1}: {gesture_name}", 
                    (max(10, wrist_x - 50), max(30, wrist_y)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, 
                    (0, 255, 255), 
                    2, 
                    cv2.LINE_AA
                )

        cv2.imshow("Pi 5 Dual Hand Recognition", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    landmarker.close()