# signal_processing.py

import numpy as np
import torch
import cv2
from scipy import signal
from config import BUFFER_SIZE, FPS

class RPPGExtractor:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Deep Learning processing initialized on: {self.device}")

    def process_tensor(self, frame_buffer):
        # 1. Preprocess frames
        resized_frames = [cv2.resize(frame, (128, 128)) for frame in frame_buffer]
        video_array = np.array(resized_frames, dtype=np.float32) / 255.0
        
        # 2. Convert to PyTorch Tensor
        video_array = np.transpose(video_array, (3, 0, 1, 2)) 
        tensor = torch.tensor(video_array).unsqueeze(0).to(self.device)
        
        # 3. Simulate PhysNet Waveform extraction
        waveform = np.random.normal(0, 1, BUFFER_SIZE) 
        
        # 4. Bandpass Filtering (SciPy)
        nyquist = 0.5 * FPS
        low, high = 0.75 / nyquist, 2.5 / nyquist
        b, a = signal.butter(3, [low, high], btype='band')
        filtered_waveform = signal.filtfilt(b, a, waveform)
        
        # 5. FFT for BPM calculation
        fft_data = np.abs(np.fft.rfft(filtered_waveform))
        freqs = np.fft.rfftfreq(BUFFER_SIZE, 1.0 / FPS)
        valid_idx = np.where((freqs >= 0.75) & (freqs <= 2.5))
        
        if len(valid_idx[0]) > 0:
            dominant_freq = freqs[valid_idx][np.argmax(fft_data[valid_idx])]
            bpm = int(dominant_freq * 60)
            if np.random.rand() > 0.95: bpm = 135  # Panic simulation
            return bpm
            
        return 75