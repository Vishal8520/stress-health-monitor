import pandas as pd
import numpy as np

def generate_stress_data(num_samples=10000):
    np.random.seed(42)

    # Demographic & Basic Lifestyle
    age = np.random.randint(15, 60, num_samples)
    weight = np.random.normal(70, 15, num_samples).clip(40, 150)
    sleep_hours = np.random.normal(7, 1.5, num_samples).clip(3, 12)
    sleep_timing = np.random.choice(["Early", "Normal", "Late"], num_samples, p=[0.2, 0.5, 0.3])
    working_hours = np.random.normal(8, 2, num_samples).clip(0, 14)
    study_hours = np.random.normal(3, 2, num_samples).clip(0, 10)
    exercise_hours = np.random.normal(1, 1, num_samples).clip(0, 4)
    water_intake = np.random.normal(6, 2, num_samples).clip(0, 15) # Glasses of water
    
    # Binary Features (0 or 1)
    exam_preparation = np.random.choice([0, 1], num_samples, p=[0.7, 0.3])
    family_issues = np.random.choice([0, 1], num_samples, p=[0.8, 0.2])
    social_media_usage = np.random.choice([0, 1], num_samples, p=[0.1, 0.9])
    
    # Social Media specific hours (conditional on general usage)
    instagram_hours = np.where(social_media_usage == 1, np.random.normal(2, 1.5, num_samples).clip(0, 8), 0)
    facebook_hours = np.where(social_media_usage == 1, np.random.normal(1, 1, num_samples).clip(0, 5), 0)

    # Calculate an underlying "Stress Score"
    # Base stress + positive/negative impacts of lifestyle choices
    stress_score = (
        (working_hours * 0.5) +
        (study_hours * 0.4) +
        (exam_preparation * 2.5) +
        (family_issues * 3.0) +
        (instagram_hours * 0.3) +
        (facebook_hours * 0.2) +
        ((8 - sleep_hours) * 0.6) # Less sleep = higher stress
    )

    # Modify stress score based on sleep timing and exercise/weight
    stress_score += np.where(sleep_timing == "Late", 1.5, 0)
    stress_score += np.where(sleep_timing == "Early", -0.5, 0)
    stress_score += np.where(weight > 100, 1.0, 0) # High weight slight stress factor
    stress_score -= (exercise_hours * 1.5) # Exercise strongly reduces stress
    stress_score -= (water_intake * 0.2) # Hydration slightly reduces stress

    # Normalize roughly and categorize
    # Let's say: 
    # score < 5: Low Stress
    # 5 <= score < 9: Medium Stress
    # score >= 9: High Stress
    stress_level = []
    for s in stress_score:
        if s < 6:
            stress_level.append("Low")
        elif s < 10.5:
            stress_level.append("Medium")
        else:
            stress_level.append("High")

    # Create DataFrame
    df = pd.DataFrame({
        "Age": age,
        "Weight": np.round(weight, 1),
        "Sleep_Hours": np.round(sleep_hours, 1),
        "Sleep_Timing": sleep_timing,
        "Working_Hours": np.round(working_hours, 1),
        "Study_Hours": np.round(study_hours, 1),
        "Exercise_Hours": np.round(exercise_hours, 1),
        "Water_Intake": np.round(water_intake, 1),
        "Exam_Preparation": exam_preparation, # 0 No, 1 Yes
        "Family_Issues": family_issues,       # 0 No, 1 Yes
        "Social_Media_Usage": social_media_usage, # 0 No, 1 Yes
        "Instagram_Hours": np.round(instagram_hours, 1),
        "Facebook_Hours": np.round(facebook_hours, 1),
        "Stress_Level": stress_level
    })

    return df

if __name__ == "__main__":
    print("Generating simulated dataset with 15k samples...")
    dataset = generate_stress_data(15000)
    
    filename = "stress_dataset.csv"
    dataset.to_csv(filename, index=False)
    
    print(f"Dataset generated and saved to {filename}")
    print(dataset.head())
    print("\nValue Counts for Target Variable:")
    print(dataset['Stress_Level'].value_counts())
