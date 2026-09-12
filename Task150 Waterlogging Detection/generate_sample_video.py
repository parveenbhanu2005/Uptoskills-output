"""
Sample Video Generator for HydroVision AI
------------------------------------------
Generates a synthetic test video (sample_flooded_road.mp4) simulating a flooded road
with moving vehicles and pedestrians to test detection pipeline out of the box.
"""

import os
import cv2
import numpy as np

def create_sample_video(output_path="sample_flooded_road.mp4", duration_sec=5, fps=25):
    width, height = 800, 450
    total_frames = duration_sec * fps
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Generating synthetic test video: {output_path} ({total_frames} frames)...")

    for i in range(total_frames):
        # Create road frame background (Dark Asphalt)
        frame = np.full((height, width, 3), (40, 45, 50), dtype=np.uint8)

        # Upper region: Buildings / Sky
        cv2.rectangle(frame, (0, 0), (width, 150), (90, 75, 60), -1)
        cv2.putText(frame, "CITY CORRIDOR - CAMERA 04", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Lower region: Flooded Road Surface (Dark blue-grey water with ripples)
        water_y = 180
        cv2.rectangle(frame, (0, water_y), (width, height), (95, 75, 55), -1)

        # Animated water ripple effect
        ripple_offset = (i * 4) % 40
        for r_y in range(water_y + 20, height, 35):
            cv2.line(frame, (0, r_y + ripple_offset // 2), (width, r_y + ripple_offset // 2), (120, 100, 75), 1)

        # Moving Vehicle (Car box moving left to right)
        car_x = int((i * 12) % (width + 150)) - 100
        car_y = 260
        # Car body
        cv2.rectangle(frame, (car_x, car_y), (car_x + 120, car_y + 50), (30, 30, 200), -1)
        cv2.rectangle(frame, (car_x + 20, car_y - 20), (car_x + 90, car_y), (40, 40, 220), -1)
        # Car wheels submerged
        cv2.circle(frame, (car_x + 30, car_y + 50), 12, (20, 20, 20), -1)
        cv2.circle(frame, (car_x + 90, car_y + 50), 12, (20, 20, 20), -1)
        cv2.putText(frame, "SEDAN", (car_x + 30, car_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Moving Pedestrian (Person moving right to left)
        person_x = width - int((i * 6) % (width + 100))
        person_y = 230
        # Head
        cv2.circle(frame, (person_x, person_y), 10, (220, 180, 150), -1)
        # Body
        cv2.rectangle(frame, (person_x - 8, person_y + 10), (person_x + 8, person_y + 45), (180, 50, 50), -1)
        # Umbrella
        cv2.ellipse(frame, (person_x, person_y - 12), (22, 10), 0, 180, 360, (20, 150, 220), -1)

        out.write(frame)

    out.release()
    print(f"Sample video created successfully at: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_sample_video()
