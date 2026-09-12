import os
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

# Make sure this path still points to your train folder
TRAIN_DATA_PATH = "./dev_data_pump/pump/train/" 

def load_and_chunk_audio(file_path, chunk_duration_sec=5, sample_rate=16000):
    """Loads a wav file and splits it into smaller chunks."""
    audio, sr = librosa.load(file_path, sr=sample_rate)
    samples_per_chunk = chunk_duration_sec * sr
    
    chunks = []
    for i in range(0, len(audio), samples_per_chunk):
        chunk = audio[i:i + samples_per_chunk]
        if len(chunk) == samples_per_chunk:
            chunks.append(chunk)
            
    return chunks

def extract_mel_spectrogram(audio_chunk, sample_rate=16000):
    """Converts a raw audio chunk into a Mel-spectrogram in decibels."""
    # Generate the Mel-spectrogram
    # n_mels=128 is a standard number of frequency bands
    mel_spec = librosa.feature.melspectrogram(y=audio_chunk, sr=sample_rate, n_mels=128)
    
    # Convert power (amplitude squared) to Decibels (dB)
    # ML models process logarithmic scales much better
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    
    return mel_spec_db

def plot_spectrogram(mel_spec_db, sample_rate=16000, title="Healthy Pump Mel-Spectrogram"):
    """Visualizes the spectrogram."""
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mel_spec_db, sr=sample_rate, x_axis='time', y_axis='mel')
    plt.colorbar(format='%+2.0f dB')
    plt.title(title)
    plt.tight_layout()
    
    # This will open a window showing the plot
    plt.show() 

# --- Main Execution ---
for filename in os.listdir(TRAIN_DATA_PATH):
    if filename.endswith(".wav"):
        full_path = os.path.join(TRAIN_DATA_PATH, filename)
        
        # 1. Load and chunk the audio
        audio_chunks = load_and_chunk_audio(full_path, chunk_duration_sec=5)
        print(f"Loaded {filename} - Split into {len(audio_chunks)} chunks.")
        
        # 2. Extract features for the first chunk
        first_chunk = audio_chunks[0]
        mel_spectrogram_data = extract_mel_spectrogram(first_chunk)
        print(f"Mel-spectrogram shape: {mel_spectrogram_data.shape}")
        
        # 3. Plot the spectrogram to verify it visually
        plot_spectrogram(mel_spectrogram_data)
        
        # Stop after the first file so we just test one plot
        break