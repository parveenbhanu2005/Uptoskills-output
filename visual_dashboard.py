import cv2
import numpy as np
import time

# Initialize the dashboard dimensions
width, height = 850, 500

# Define Interface Colors (BGR format in OpenCV)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREY = (30, 30, 30)

def draw_dashboard(frame, status, color, risk, frame_count):
    # Clear frame with dark grey background
    frame[:] = DARK_GREY
    
    # --- HEADER ---
    cv2.putText(frame, "AI PREDICTIVE MAINTENANCE SYSTEM - LIVE FEED", (30, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2)
    cv2.putText(frame, "TARGET: PUMP_016 | SENSOR: ACOUSTIC_MIC_01", (30, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 1)
    
    # --- ACOUSTIC SENSOR WINDOW ---
    # Draw the boundary box (Mimicking CCTV frame)
    cv2.rectangle(frame, (30, 100), (530, 450), WHITE, 2)
    cv2.putText(frame, "LIVE WAVEFORM ANALYSIS", (40, 130), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)
    
    # Simulate fluctuating audio wave
    center_y = 275
    for x in range(40, 520, 12):
        # Generate larger spikes if an anomaly is detected
        noise = np.random.randint(5, 25) if status == "SYSTEM NORMAL" else np.random.randint(60, 160)
        cv2.line(frame, (x, center_y - noise), (x, center_y + noise), color, 2)
        
        # Add "Targeting" boxes on anomalous spikes to look like object detection
        if status != "SYSTEM NORMAL" and noise > 120:
            cv2.rectangle(frame, (x-5, center_y - noise - 5), (x+5, center_y + noise + 5), RED, 1)
            cv2.putText(frame, "SPIKE", (x-10, center_y - noise - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, RED, 1)
    
    # --- SYSTEM STATUS PANEL ---
    # Status Box
    cv2.rectangle(frame, (560, 100), (820, 200), color, -1)
    cv2.putText(frame, "STATUS:", (575, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, BLACK, 2)
    cv2.putText(frame, status, (575, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.7, BLACK, 2)
    
    # Risk Metric
    cv2.putText(frame, f"FAILURE RISK: {risk}%", (560, 240), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 2)
    
    # Static Data Panel
    cv2.putText(frame, "MODEL: Isolation Forest", (560, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)
    cv2.putText(frame, "FEATURES: Mel-Spectrogram", (560, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)
    cv2.putText(frame, f"TIMESTAMP: {time.strftime('%H:%M:%S')}", (560, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)

    return frame

# --- MAIN EXECUTION LOOP ---
dashboard_frame = np.zeros((height, width, 3), dtype=np.uint8)

# Run for approximately 250 frames
for i in range(250): 
    # Simulate time passing (Normal for first half, Anomaly for second half)
    if i < 100:
        current_status = "SYSTEM NORMAL"
        current_color = GREEN
        current_risk = np.random.randint(1, 6) # Low risk
    else:
        current_status = "ANOMALY DETECTED"
        current_color = RED
        current_risk = 84 + np.random.randint(-2, 3) # High risk fluctuating around 84%
        
    # Generate the frame
    final_ui = draw_dashboard(dashboard_frame, current_status, current_color, current_risk, i)
    
    # Display the dashboard
    cv2.imshow("Acoustic Monitoring Feed", final_ui)
    
    # Frame rate control (Wait 50ms between frames)
    if cv2.waitKey(50) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()