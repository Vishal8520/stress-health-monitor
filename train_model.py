import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

def train():
    print("Loading dataset...")
    try:
        df = pd.read_csv("stress_dataset.csv")
    except FileNotFoundError:
        print("Dataset not found! Please run generate_dataset.py first.")
        return

    # Separate features (X) and target (y)
    X = df.drop("Stress_Level", axis=1)
    y = df["Stress_Level"]

    # Preprocessing
    # 1. Encode Categorical Features
    # 'Sleep_Timing' is categorical
    le_sleep = LabelEncoder()
    X['Sleep_Timing'] = le_sleep.fit_transform(X['Sleep_Timing'])

    # Encode Target
    le_target = LabelEncoder()
    y_encoded = le_target.fit_transform(y)
    
    # 2. Scale Numerical Features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Test Split
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # Train Model
    print("Training Random Forest Classifier model...")
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # Evaluate Model
    print("Evaluating model...")
    y_pred = rf_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"\nModel Accuracy: {acc * 100:.2f}%\n")
    print("Classification Report:")
    # Using inverse_transform to show original category names in the report
    target_names = le_target.classes_
    print(classification_report(y_test, y_pred, target_names=target_names))

    # Save components for prediction later
    print("Saving model and preprocessors to disk...")
    model_data = {
        "model": rf_model,
        "scaler": scaler,
        "le_sleep": le_sleep,
        "le_target": le_target,
        "feature_names": X.columns.tolist()
    }
    joblib.dump(model_data, "stress_detection_model.joblib")
    print("Saved successfully to stress_detection_model.joblib")

if __name__ == "__main__":
    train()
