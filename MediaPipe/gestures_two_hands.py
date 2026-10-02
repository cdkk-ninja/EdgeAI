import os
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
from picamera2 import Picamera2 
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from collections import deque
import numpy as np

# --- Global Fan State Variables ---
fan_speed = 0  # Percentage from 0 to 100

# --- Circular Motion Tracking Configuration ---
HISTORY_LENGTH = 15
hand_histories = {0: deque(maxlen=HISTORY_LENGTH), 1: deque(maxlen=HISTORY_LENGTH)}

def is_index_extended_only(hand_landmarks):
    """Returns True ONLY if the index finger is extended and others are curled."""
    index_extended = hand_landmarks[8].y < hand_landmarks[6].y
    middle_folded  = hand_landmarks[12].y > hand_landmarks[10].y
    ring_folded    = hand_landmarks[16].y > hand_landmarks[14].y
    pinky_folded   = hand_landmarks[20].y > hand_landmarks[18].y
    return index_extended and middle_folded and ring_folded and pinky_folded

def analyze_spinning_motion(points_history, width, height):
    """
    Analyzes the coordinates history. 
    Returns: 'CW' (Clockwise), 'CCW' (Anticlockwise), or None if it's not a circle.
    """
    if len(points_history) < HISTORY_LENGTH:
        return None
        
    pts = np.array([(p[0] * width, p[1] * height) for p in points_history], dtype=np.float32)
    
    x_min, y_min = np.min(pts, axis=0)
    x_max, y_max = np.max(pts, axis=0)
    box_w = x_max - x_min
    box_h = y_max - y_min
    
    # 1. Filter out tiny tremors
    if box_w < 35 or box_h < 35:
        return None
        
    # 2. Check for circular aspect ratio
    aspect_ratio = box_w / box_h if box_h != 0 else 0
    if not (0.5 < aspect_ratio < 2.0):
        return None
        
    # 3. Determine Rotation Direction using Cross Products of consecutive segments
    # In OpenCV/MediaPipe, Y increases downwards, which makes standard cross-product signs flip.
    cross_products = []
    for i in range(1, len(pts) - 1):
        v1 = pts[i] - pts[i-1]   # Vector from point i-1 to i
        v2 = pts[i+1] - pts[i]   # Vector from point i to i+1
        
        # 2D cross product: x1*y2 - y1*x2
        cp = v1[0] * v2[1] - v1[1] * v2[0]
        cross_products.append(cp)
        
    avg_cp = np.mean(cross_products)
    
    # Require a clear sign dominance to filter out chaotic weaving motions
    # Because Y-axis points downward: Positive cross product = Clockwise
    if avg_cp > 5.0:  
        return 'CW'
    elif avg_cp < -5.0:
        return 'CCW'
        
    return None

# 1. Initialize Gesture Recognizer
path_MediaPipe_models = "MediaPipe/"
base_options = python.BaseOptions(model_asset_path=path_MediaPipe_models+'gesture_recognizer.task')
options = vision.GestureRecognizerOptions(
    base_options=base_options,
    num_hands=2
)
recognizer = vision.GestureRecognizer.create_from_options(options)

# 2. Configure Picamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()
picam2.set_controls({"AfMode": 2, "AwbMode": 0})

cv2.namedWindow("Pi 5 Fan Speed Controller", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

print("Camera active. CW = Speed UP, CCW = Speed DOWN. Press 'q' to quit.")

try:
    while True:
        frame_bgr = picam2.capture_array("main")
        if frame_bgr is None or frame_bgr.size == 0:
            continue

        display_frame = cv2.flip(frame_bgr, 1)
        h, w, _ = display_frame.shape

        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = recognizer.recognize(mp_image)

        # Clear histories for missing hands
        visible_hands = len(result.gestures) if result.gestures else 0
        for idx in list(hand_histories.keys()):
            if idx >= visible_hands:
                hand_histories[idx].clear()

        if result.gestures:
            for idx, hand_gestures in enumerate(result.gestures):
                if not hand_gestures:
                    continue

                top_gesture = hand_gestures[0]
                gesture_name = top_gesture.category_name
                score = top_gesture.score

                if result.hand_landmarks and len(result.hand_landmarks) > idx:
                    hand_landmarks = result.hand_landmarks[idx]
                    
                    if is_index_extended_only(hand_landmarks):
                        index_tip = hand_landmarks[8]
                        hand_histories[idx].append((index_tip.x, index_tip.y))
                        
                        # Detect rotation direction
                        motion_dir = analyze_spinning_motion(hand_histories[idx], w, h)
                        if motion_dir == 'CW':
                            gesture_name = "Spinning Clockwise (+)"
                            fan_speed = min(100, fan_speed + 5)  # Cap at 100%
                        elif motion_dir == 'CCW':
                            gesture_name = "Spinning Anti-Clockwise (-)"
                            fan_speed = max(0, fan_speed - 5)    # Floor at 0%
                    else:
                        hand_histories[idx].clear()

                    # Draw hand skeletons
                    for lm in hand_landmarks:
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(display_frame, (cx, cy), 4, (0, 255, 0), -1)

                    # Draw trail lines (Blue for CCW/neutral, Red for active inputs)
                    if len(hand_histories[idx]) > 1:
                        for i in range(1, len(hand_histories[idx])):
                            pt1 = (int(hand_histories[idx][i-1][0] * w), int(hand_histories[idx][i-1][1] * h))
                            pt2 = (int(hand_histories[idx][0] * w), int(hand_histories[idx][1] * h))
                            cv2.line(display_frame, pt1, pt2, (255, 0, 0), 2)

                    wrist_x = int(hand_landmarks[0].x * w)
                    wrist_y = int(hand_landmarks[0].y * h) - 20
                else:
                    wrist_x, wrist_y = 30, 50 + (idx * 40)

                label = f"Hand {idx+1}: {gesture_name}"
                cv2.putText(display_frame, label, (max(10, wrist_x - 50), max(30, wrist_y)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

        # HUD Overlay to show global Fan Speed status
        cv2.rectangle(display_frame, (10, 10), (280, 50), (0, 0, 0), -1)
        cv2.putText(display_frame, f"FAN SPEED: {fan_speed}%", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0) if fan_speed > 0 else (0, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow("Pi 5 Fan Speed Controller", display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    recognizer.close()
