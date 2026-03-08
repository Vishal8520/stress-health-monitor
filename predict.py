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
    
    # Foundational Level-Specific Advice
    if stress_level == "Minimal":
        suggestions.append("Base Status (Minimal): Outstanding baseline health! Your routine and environment are incredibly well optimized for mental resilience.")
    elif stress_level == "Mild":
        suggestions.append("Base Status (Mild): You are operating functionally and healthy, though you experience standard day-to-day pressures. Maintain your current coping habits.")
    elif stress_level == "Moderate":
        suggestions.append("Base Status (Moderate): Warning sign. You are carrying a noticeable load of persistent stress. Fatigue may be setting in; it's time to intentionally schedule daily decompression blocks.")
    elif stress_level == "High":
        suggestions.append("Base Status (High): Red Alert. Your nervous system is under severe, compounding pressure. Physical symptoms (tension, poor sleep) are highly likely. Immediate intervention in your routine is required.")
    elif stress_level == "Critical":
        suggestions.append("Base Status (Critical): Severe Burnout Threshold. You are operating at an unsustainable level of chronic stress. Please pause, re-evaluate your commitments immediately, and strongly consider consulting a medical or mental health professional for support.")

    # Feature-Specific Mitigation (Applied to Moderate, High, and Critical levels)
    if stress_level in ["Moderate", "High", "Critical"]:
        if input_data.get("Sleep_Hours", 8) < 7:
            suggestions.append("Sleep: You are getting less than 7 hours of sleep. Try to prioritize sleeping earlier to hit 7-8 hours.")
            
        if input_data.get("Sleep_Timing") == "Late":
            suggestions.append("Sleep Timing: Sleeping late disrupts your circadian rhythm. Try shifting your bedtime gradually to an earlier hour.")
            
        if input_data.get("Exercise_Hours", 1) < 1.0:
            suggestions.append("Exercise & Yoga: Your physical activity is low. Even 15-30 minutes of daily exercise or yoga can significantly release endorphins and reduce stress hormones.")
            
        social_hours = input_data.get("Instagram_Hours", 0) + input_data.get("Facebook_Hours", 0)
        if social_hours > 2:
            suggestions.append(f"Social Media: You spend around {social_hours} hours on social media. Reducing screen time before bed can help lower anxiety.")
            
        if input_data.get("Water_Intake", 8) < 5:
            suggestions.append("Hydration: You are drinking very little water. Dehydration increases cortisol levels. Aim for at least 6-8 glasses a day.")
            
        work_study_hours = input_data.get("Working_Hours", 0) + input_data.get("Study_Hours", 0)
        if work_study_hours > 9:
            suggestions.append(f"Work/Study Balance: You are working/studying for {work_study_hours} hours. Use techniques like the Pomodoro method to take regular breaks and avoid mental burnout.")
            
        if input_data.get("Family_Issues") == 1:
            suggestions.append("Well-being: Family or relationship issues are a major stressor right now. Consider talking to a trusted friend or counselor to process these feelings healthily.")
            
        if input_data.get("Exam_Preparation") == 1:
            suggestions.append("Exams: Exam preparation is highly stressful. Make sure to break your syllabus into small achievable chunks and reward yourself for completing them.")
            
        if input_data.get("Weight", 70) > 90 and input_data.get("Exercise_Hours", 1) < 2:
            suggestions.append("Diet & Movement: A healthy diet combined with light daily walks can improve your physical health, which directly supports your mental resilience against stress.")
            
        if input_data.get("Healthy_Diet", 5) < 4:
            suggestions.append("Nutrition: Your diet lacks essential nutrients. Focus on eating more whole foods, vegetables, and proteins to fuel your brain properly and reduce physical stress.")
            
        if input_data.get("Fast_Food_Weekly", 0) >= 3:
            suggestions.append(f"Fast Food: Eating fast food {input_data.get('Fast_Food_Weekly')} times a week can cause lethargy and inflammation. Cutting back will improve your energy levels remarkably.")
            
        if input_data.get("Health_Issues") == 1:
            suggestions.append("General Health: Coping with health issues is inherently stressful. Please ensure you are regularly consulting your doctor and not ignoring your bodily symptoms. Self-care is paramount.")
            
        if input_data.get("Location_Type") == "Urban":
            suggestions.append("Environment (Urban): City living inherently introduces background stressors like noise, traffic, and high-paced lifestyles. Try to plan weekend getaways to nature or quiet parks to decompress your nervous system.")
            
        if input_data.get("Location_Type") == "Rural" and input_data.get("Family_Issues") == 1:
             suggestions.append("Community (Rural): While rural areas are peaceful, isolation can worsen family stress. Consider finding a local community group or online counseling to find social support.")
            
    if len(suggestions) <= 1: # Only has the base status
        if stress_level in ["Minimal", "Mild"]:
            suggestions.append("Continue prioritizing your excellent sleep hydration routines.")
        else:
            suggestions.append("Try general relaxation techniques like deep breathing, meditation, or spending time in nature to center yourself.")
            
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
    le_location = pipeline.get("le_location") # Get new encoder safely
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
    
    if le_location is not None and 'Location_Type' in df.columns:
        df['Location_Type'] = le_location.transform(df['Location_Type'])

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
        "Healthy_Diet": 3,
        "Fast_Food_Weekly": 4,
        "Health_Issues": 1,
        "Exam_Preparation": 1, 
        "Family_Issues": 0, 
        "Location_Type": "Urban",
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
        "Healthy_Diet": 9,
        "Fast_Food_Weekly": 0,
        "Health_Issues": 0,
        "Exam_Preparation": 0, 
        "Family_Issues": 0,       
        "Location_Type": "Rural",
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
