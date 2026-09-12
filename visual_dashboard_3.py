import cv2
import numpy as np
import time

width, height = 850, 500
GREEN = (0, 255, 0)
RED = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREY = (30, 30, 30)

def draw_dashboard(frame, status, color, risk, frame_count):
    frame[:] = DARK_GREY
    
    cv2.putText(frame, "AI PREDICTIVE MAINTENANCE SYSTEM - LIVE FEED", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2)
    cv2.putText(frame, "TARGET: PUMP_088 | SENSOR: ACOUSTIC_MIC_12", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 1)
    
    cv2.rectangle(frame, (30, 100), (530, 450), WHITE, 2)
    cv2.putText(frame, "LIVE WAVEFORM ANALYSIS", (40, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)
    
    center_y = 275
    for x in range(40, 520, 12):
        noise = np.random.randint(2, 15) if status == "SYSTEM NORMAL" else np.random.randint(100, 200)
        cv2.line(frame, (x, center_y - noise), (x, center_y + noise), color, 2)
        
        if status != "SYSTEM NORMAL" and noise > 150:
            cv2.rectangle(frame, (x-5, center_y - noise - 5), (x+5, center_y + noise + 5), RED, 2)
            cv2.putText(frame, "CRITICAL", (x-15, center_y - noise - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, RED, 2)
    
    cv2.rectangle(frame, (560, 100), (820, 200), color, -1)
    cv2.putText(frame, "STATUS:", (575, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, BLACK, 2)
    cv2.putText(frame, status, (575, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 2)
    
    cv2.putText(frame, f"FAILURE RISK: {risk}%", (560, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2)
    cv2.putText(frame, "MODEL: Isolation Forest", (560, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)
    cv2.putText(frame, "FEATURES: Mel-Spectrogram", (560, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)
    cv2.putText(frame, f"TIMESTAMP: {time.strftime('%H:%M:%S')}", (560, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)

    return frame

dashboard_frame = np.zeros((height, width, 3), dtype=np.uint8)

for i in range(200): 
    # This one flips suddenly at frame 70
    if i < 70:
        current_status = "SYSTEM NORMAL"
        current_color = GREEN
        current_risk = np.random.randint(1, 3) 
    else:
        current_status = "CRITICAL FAILURE IMMINENT"
        current_color = RED
        current_risk = 98 + np.random.randint(-1, 2) 
        
    final_ui = draw_dashboard(dashboard_frame, current_status, current_color, current_risk, i)
    cv2.imshow("Acoustic Monitoring Feed - Pump 088", final_ui)
    
    if cv2.waitKey(50) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()