import os
import librosa
import numpy as np
import pandas as pd
import joblib
import soundfile as sf
import datetime

# --- Configuration Paths ---
TEST_DATA_PATH = "./dev_data_pump/pump/source_test/" 
MODEL_PATH = "pump_anomaly_model_robust.pkl"  # Make sure this points to the new model
ANOMALY_AUDIO_DIR = "./anomaly_snippets/"
CSV_LOG_PATH = "maintenance_alert_log.csv"

os.makedirs(ANOMALY_AUDIO_DIR, exist_ok=True)

model = joblib.load(MODEL_PATH)
print("Robust model loaded successfully.")

def get_robust_audio_features(audio_chunk, sample_rate=16000):
    """Must match the training feature extraction exactly."""
    mel_spec = librosa.feature.melspectrogram(y=audio_chunk, sr=sample_rate, n_mels=128)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    
    feature_mean = np.mean(mel_spec_db, axis=1)
    feature_std = np.std(mel_spec_db, axis=1)
    feature_max = np.max(mel_spec_db, axis=1)
    
    robust_features = np.concatenate([feature_mean, feature_std, feature_max])
    return robust_features

def process_test_data():
    alert_logs = []
    
    all_files = [f for f in os.listdir(TEST_DATA_PATH) if f.endswith(".wav")]
    anomaly_files = [f for f in all_files if "anomaly" in f]
    normal_files = [f for f in all_files if "normal" in f]
    
    # Let's test a larger batch this time
    test_batch = normal_files[:20] + anomaly_files[:20]
    
    print(f"Testing batch of {len(test_batch)} files ({len(anomaly_files[:20])} known anomaly files included)...\n")

    for filename in test_batch:
        full_path = os.path.join(TEST_DATA_PATH, filename)
        audio, sr = librosa.load(full_path, sr=16000)
        
        samples_per_chunk = 5 * sr
        for i in range(0, len(audio), samples_per_chunk):
            chunk = audio[i:i + samples_per_chunk]
            
            if len(chunk) == samples_per_chunk:
                features = get_robust_audio_features(chunk).reshape(1, -1)
                
                # We will go back to the default prediction method first
                prediction = model.predict(features)[0]
                
                if prediction == -1:
                    print(f"⚠️  ANOMALY DETECTED in file: {filename}")
                    
                    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
                    snippet_filename = f"anomaly_{filename}"
                    snippet_path = os.path.join(ANOMALY_AUDIO_DIR, snippet_filename)
                    sf.write(snippet_path, chunk, sr)
                    
                    # Calculate a simple failure probability for logging
                    anomaly_score = model.decision_function(features)[0] 
                    failure_prob = round(min(100.0, max(0.0, abs(anomaly_score) * 1000)), 2)
                    
                    alert_logs.append({
                        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Source_File": filename,
                        "Failure_Probability_Rating (%)": failure_prob,
                        "Saved_Audio_Snippet": snippet_filename
                    })

    if alert_logs:
        df = pd.DataFrame(alert_logs)
        df.to_csv(CSV_LOG_PATH, index=False)
        print("\n" + "="*50)
        print(f"✅ SUCCESS: Log created at '{CSV_LOG_PATH}'")
        print("="*50 + "\n")
        print("LOG SUMMARY PREVIEW:")
        print(df.head())
    else:
        print("\nNo anomalies detected in this batch.")

if __name__ == "__main__":
    process_test_data()