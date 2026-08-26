import cv2
import mediapipe as mp
import random
import pygame
import sys

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

def get_gesture(hand_landmarks):
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]

    extended = []
    for tip, pip in zip(tips, pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            extended.append(True)
        else:
            extended.append(False)

    thumb_extended = hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x if hand_landmarks.landmark[5].x < hand_landmarks.landmark[17].x else hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x

    if extended[0] and extended[1] and not extended[2] and not extended[3]:
        return "Scissors"
    if all(extended):
        return "Paper"
    if not any(extended):
        return "Stone"

    return "None"

def determine_winner(user_move, comp_move):
    if user_move == comp_move:
        return "Draw"
    elif (user_move == "Stone" and comp_move == "Scissors") or \
         (user_move == "Paper" and comp_move == "Stone") or \
         (user_move == "Scissors" and comp_move == "Paper"):
        return "User"
    else:
        return "Computer"

def main():
    pygame.init()
    
    window_width = 800
    window_height = 600
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Stone Paper Scissors - Timer Edition")
    
    font = pygame.font.SysFont("Arial", 28, bold=True)
    big_font = pygame.font.SysFont("Arial", 40, bold=True)
    
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 120, 255)
    YELLOW = (255, 215, 0)

    cap = cv2.VideoCapture(0)
    
    # Match State Variables
    user_score = 0
    computer_score = 0
    draws = 0
    round_number = 1
    target_wins = 3 
    
    # Timer & Flow Variables
    state = "IDLE"  # Can be: "IDLE", "COUNTDOWN", "RESULT", "GAME_OVER"
    start_ticks = 0
    result_ticks = 0
    countdown_seconds = 3
    
    comp_move = "None"
    current_gesture = "None"
    result_text = "Press SPACE to Start Round 1!"

    clock = pygame.time.Clock()

    while True:
        current_ticks = pygame.time.get_ticks()
        
        # 1. Handle Keyboard Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if state == "IDLE":
                        # Start the countdown
                        state = "COUNTDOWN"
                        start_ticks = pygame.time.get_ticks()
                        comp_move = "None"
                    
                    elif state == "GAME_OVER":
                        # Reset for a whole new match
                        user_score = 0
                        computer_score = 0
                        draws = 0
                        round_number = 1
                        state = "IDLE"
                        comp_move = "None"
                        result_text = "Press SPACE to Start Round 1!"

                if event.key == pygame.K_r:
                    user_score = 0
                    computer_score = 0
                    draws = 0
                    round_number = 1
                    state = "IDLE"
                    comp_move = "None"
                    result_text = "Scores Reset. Press SPACE to Play!"

        # 2. Update Game State Logic based on Timer
        if state == "COUNTDOWN":
            elapsed_seconds = (current_ticks - start_ticks) // 1000
            remaining = countdown_seconds - elapsed_seconds
            
            if remaining > 0:
                result_text = f"Rock... Paper... Scissors... {remaining}"
            else:
                # Timer hit 0! Lock in the move.
                if current_gesture != "None":
                    moves = ["Stone", "Paper", "Scissors"]
                    comp_move = random.choice(moves)
                    winner = determine_winner(current_gesture, comp_move)
                    
                    if winner == "User":
                        user_score += 1
                        result_text = f"Round {round_number}: You Win!"
                    elif winner == "Computer":
                        computer_score += 1
                        result_text = f"Round {round_number}: Computer Wins!"
                    else:
                        draws += 1
                        result_text = f"Round {round_number}: It's a Draw!"
                        
                    round_number += 1
                    state = "RESULT"
                    result_ticks = pygame.time.get_ticks()
                else:
                    result_text = "No hand detected! Press SPACE to try again."
                    state = "IDLE"

        elif state == "RESULT":
            # Keep the result on screen for 2.5 seconds before moving on
            if (current_ticks - result_ticks) > 2500:
                if user_score == target_wins:
                    result_text = "MATCH WON! Press SPACE for Next Match."
                    state = "GAME_OVER"
                elif computer_score == target_wins:
                    result_text = "MATCH LOST! Press SPACE for Next Match."
                    state = "GAME_OVER"
                else:
                    result_text = f"Press SPACE to Start Round {round_number}!"
                    state = "IDLE"

        # 3. Capture and Process Webcam
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = hands.process(rgb_frame)
        current_gesture = "None"
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                current_gesture = get_gesture(hand_landmarks)

        # 4. Render Pygame UI
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        shape = frame_rgb.shape[1::-1]
        frame_surface = pygame.image.frombuffer(frame_rgb.tobytes(), shape, "RGB")

        screen.fill(BLACK)
        
        cam_x = (window_width - shape[0]) // 2
        cam_y = 120
        screen.blit(frame_surface, (cam_x, cam_y))
        
        # Display Match Status
        match_surf = font.render(f"First to {target_wins} Wins", True, YELLOW)
        screen.blit(match_surf, (10, 20))
        
        round_str = f"Round: {round_number}" if state != "GAME_OVER" else "Match Over"
        round_surf = font.render(round_str, True, YELLOW)
        screen.blit(round_surf, (window_width - round_surf.get_width() - 10, 20))

        # Center Score Board
        score_str = f"User: {user_score}   |   Computer: {computer_score}"
        score_surf = big_font.render(score_str, True, WHITE)
        screen.blit(score_surf, (window_width//2 - score_surf.get_width()//2, 20))

        # Show Current Gestures
        user_gest_surf = font.render(f"You: {current_gesture}", True, GREEN)
        comp_gest_surf = font.render(f"Comp: {comp_move}", True, RED)
        
        screen.blit(user_gest_surf, (cam_x, cam_y - 40))
        screen.blit(comp_gest_surf, (cam_x + shape[0] - comp_gest_surf.get_width(), cam_y - 40))

        # Main Feedback Text
        if state == "COUNTDOWN":
            result_color = YELLOW
        elif "WON" in result_text or "Win" in result_text:
            result_color = GREEN
        elif "LOST" in result_text or "Computer Wins" in result_text:
            result_color = RED
        else:
            result_color = BLUE

        result_surf = big_font.render(result_text, True, result_color)
        screen.blit(result_surf, (window_width//2 - result_surf.get_width()//2, window_height - 60))

        reset_surf = font.render("Press 'R' to reset", True, WHITE)
        screen.blit(reset_surf, (10, window_height - 40))

        pygame.display.flip()
        clock.tick(30)

if __name__ == '__main__':
    main()