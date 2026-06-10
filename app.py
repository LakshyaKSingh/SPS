import cv2
import mediapipe as mp
import random
import numpy as np
from flask import Flask, render_template, Response, jsonify

app = Flask(__name__)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Game state
game_state = {
    "user_score": 0,
    "computer_score": 0,
    "draws": 0,
    "current_gesture": "None"
}

def get_gesture(hand_landmarks):
    """
    Heuristic to detect Stone, Paper, or Scissors based on MediaPipe landmarks.
    Finger landmarks:
    - Thumb: 4
    - Index: 8
    - Middle: 12
    - Ring: 16
    - Pinky: 20
    """
    # Tips of the fingers
    tips = [8, 12, 16, 20]
    # PIP joints (second joint from tip)
    pips = [6, 10, 14, 18]

    # Check which fingers are extended
    # A finger is extended if the tip is higher than the pip joint (y-coordinate is smaller)
    extended = []
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            extended.append(True)
        else:
            extended.append(False)

    # Thumb is tricky, check x-coordinate relative to MCP
    # We'll simplify thumb: if tip is far from the base
    thumb_extended = hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x if hand_landmarks.landmark[5].x < hand_landmarks.landmark[17].x else hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x

    # Logic:
    # Scissors: Index and Middle extended, others folded
    if extended[0] and extended[1] and not extended[2] and not extended[3]:
        return "Scissors"

    # Paper: All fingers extended
    if all(extended):
        return "Paper"

    # Stone: All fingers folded
    if not any(extended):
        return "Stone"

    return "None"

def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # Flip frame for mirror effect
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process frame with MediaPipe
            results = hands.process(rgb_frame)

            gesture = "None"
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Detect gesture
                    gesture = get_gesture(hand_landmarks)
                    game_state["current_gesture"] = gesture

            # Overlay the detected gesture on the frame
            cv2.putText(frame, f"Gesture: {gesture}", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_computer_move')
def get_computer_move():
    moves = ["Stone", "Paper", "Scissors"]
    return jsonify({"move": random.choice(moves)})

@app.route('/get_current_gesture')
def get_current_gesture():
    return jsonify({"gesture": game_state["current_gesture"]})

@app.route('/update_score')
def update_score():
    # This could be expanded to track history in a DB
    return jsonify(game_state)

@app.route('/reset')
def reset():
    game_state["user_score"] = 0
    game_state["computer_score"] = 0
    game_state["draws"] = 0
    return jsonify({"status": "success"})

@app.route('/add_score/<result>')
def add_score(result):
    if result == "user":
        game_state["user_score"] += 1
    elif result == "computer":
        game_state["computer_score"] += 1
    else:
        game_state["draws"] += 1
    return jsonify(game_state)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
