import os
import librosa
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib 

TRAIN_DATA_PATH = "./dev_data_pump/pump/train/" 
MODEL_SAVE_PATH = "pump_anomaly_model_robust.pkl"

def get_robust_audio_features(file_path, sample_rate=16000):
    """Extracts mean, std, and max from the Mel-spectrogram."""
    audio, sr = librosa.load(file_path, sr=sample_rate)
    mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    
    # Calculate statistics across the time axis (axis=1)
    feature_mean = np.mean(mel_spec_db, axis=1)
    feature_std = np.std(mel_spec_db, axis=1)
    feature_max = np.max(mel_spec_db, axis=1)
    
    # Concatenate these into a single 384-length feature vector (128 * 3)
    robust_features = np.concatenate([feature_mean, feature_std, feature_max])
    return robust_features

def train_robust_model():
    print("Extracting robust features from healthy pump audio...")
    X_train = []
    
    count = 0
    for filename in os.listdir(TRAIN_DATA_PATH):
        if filename.endswith(".wav"):
            full_path = os.path.join(TRAIN_DATA_PATH, filename)
            features = get_robust_audio_features(full_path)
            X_train.append(features)
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} files...")
            
    X_train = np.array(X_train)
    print(f"New feature matrix shape: {X_train.shape} (Files, Features)")
    
    print("Training improved Isolation Forest model...")
    # We increase contamination slightly to allow for minor noise in the training set
    model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    model.fit(X_train)
    
    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"Robust model successfully saved to {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_robust_model()