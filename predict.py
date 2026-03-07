import joblib
import pandas as pd
import numpy as np

def load_prediction_pipeline(model_path="stress_detection_model.joblib"):
    """Loads the model and all associated preprocessors."""
    try:
        pipeline = joblib.load(model_path)
        return pipeline
    except FileNotFoundError:
        print(f"Error: Model file '{model_path}' not found.")
        print("Please train the model first by running train_model.py")
        return None

def get_stress_suggestions(input_data, stress_level):
    """Generates actionable suggestions based on input features and predicted stress."""
    suggestions = []
    
    # If stress is Medium or High, provide mitigation strategies
    if stress_level in ["Medium", "High"]:
        if input_data.get("Sleep_Hours", 8) < 7:
            suggestions.append("- Sleep: You are getting less than 7 hours of sleep. Try to prioritize sleeping earlier to hit 7-8 hours.")
            
        if input_data.get("Sleep_Timing") == "Late":
            suggestions.append("- Sleep Timing: Sleeping late disrupts your circadian rhythm. Try shifting your bedtime gradually to an earlier hour.")
            
        if input_data.get("Exercise_Hours", 1) < 1.0:
            suggestions.append("- Exercise & Yoga: Your physical activity is quite low. Even 15-30 minutes of daily exercise or yoga can significantly release endorphins and reduce stress hormones.")
            
        social_hours = input_data.get("Instagram_Hours", 0) + input_data.get("Facebook_Hours", 0)
        if social_hours > 2:
            suggestions.append(f"- Social Media: You spend around {social_hours} hours on social media. Reducing this screen time, especially before bed, can help lower anxiety.")
            
        if input_data.get("Water_Intake", 8) < 5:
            suggestions.append("- Hydration: You are drinking very little water. Dehydration can increase cortisol levels. Aim for at least 6-8 glasses a day.")
            
        work_study_hours = input_data.get("Working_Hours", 0) + input_data.get("Study_Hours", 0)
        if work_study_hours > 9:
            suggestions.append(f"- Work/Study Balance: You are working/studying for {work_study_hours} hours. Ensure you are taking short regular breaks (like the Pomodoro technique) to avoid mental burnout.")
            
        if input_data.get("Family_Issues") == 1:
            suggestions.append("- Well-being: Family/Relationship issues are a major stressor. Consider talking to a trusted friend or counselor to process these feelings.")
            
    if not suggestions:
        if stress_level == "Low":
            suggestions.append("- Keep up the balanced lifestyle! Your routine looks good.")
        else:
            suggestions.append("- Try general relaxation techniques like deep breathing, meditation, or spending time in nature.")
            
    return suggestions

def predict_stress(input_data):
    """
    Predicts the stress level based on input features.
    
    Args:
        input_data (dict): Dictionary containing the required predictive features.
        
    Returns:
        str: Predicted stress level (Low, Medium, or High)
    """
    pipeline = load_prediction_pipeline()
    if not pipeline:
        return "Model not found"
        
    model = pipeline["model"]
    scaler = pipeline["scaler"]
    le_sleep = pipeline["le_sleep"]
    le_target = pipeline["le_target"]
    feature_names = pipeline["feature_names"]

    # Create a DataFrame from the input features in the correct order
    df = pd.DataFrame([input_data])
    
    # Ensure all columns are present
    for col in feature_names:
        if col not in df.columns:
            raise ValueError(f"Missing required feature: {col}")
            
    # Reorder columns to match training exactly
    df = df[feature_names]

    # Preprocessing
    # 1. Encode Categorical Features
    df['Sleep_Timing'] = le_sleep.transform(df['Sleep_Timing'])

    # 2. Scale Numerical Features
    df_scaled = scaler.transform(df)

    # Predict
    pred_encoded = model.predict(df_scaled)
    
    # Decode target label back to original string
    prediction_label = le_target.inverse_transform(pred_encoded)[0]
    
    return prediction_label


if __name__ == "__main__":
    # Example Usage
    sample_person_1 = {
        "Age": 22,
        "Weight": 75,
        "Sleep_Hours": 5,
        "Sleep_Timing": "Late",
        "Working_Hours": 4,
        "Study_Hours": 6,
        "Exercise_Hours": 0.5,
        "Water_Intake": 3,
        "Exam_Preparation": 1, 
        "Family_Issues": 0,       
        "Social_Media_Usage": 1, 
        "Instagram_Hours": 3.5,
        "Facebook_Hours": 1.0
    }
    
    sample_person_2 = {
        "Age": 45,
        "Weight": 82,
        "Sleep_Hours": 8,
        "Sleep_Timing": "Normal",
        "Working_Hours": 8,
        "Study_Hours": 0,
        "Exercise_Hours": 2.5,
        "Water_Intake": 8,
        "Exam_Preparation": 0, 
        "Family_Issues": 0,       
        "Social_Media_Usage": 1, 
        "Instagram_Hours": 0.5,
        "Facebook_Hours": 1.0
    }

    print("--- Person 1 ---")
    person_1_pred = predict_stress(sample_person_1)
    print(f"Sample Person 1 (College student under exam pressure/late nights): Predicted Stress = {person_1_pred}")
    print("Suggestions:")
    for sug in get_stress_suggestions(sample_person_1, person_1_pred):
        print(sug)
        
    print("\n--- Person 2 ---")
    person_2_pred = predict_stress(sample_person_2)
    print(f"Sample Person 2 (Adult, healthy sleep, daily exercise, no extra stress factors): Predicted Stress = {person_2_pred}")
    print("Suggestions:")
    for sug in get_stress_suggestions(sample_person_2, person_2_pred):
        print(sug)
