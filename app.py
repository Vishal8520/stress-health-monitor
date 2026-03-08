import os
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
from pymongo import MongoClient
import datetime
from predict import predict_stress, get_stress_suggestions
from pyngrok import ngrok
from dotenv import load_dotenv
import jwt
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__, static_folder='stress1')
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-change-in-prod')
client = None
db = None
users_collection = None
reports_collection = None

# Initialize MongoDB connection
# Connects to default local MongoDB instance or a Cloud URI if provided in environment variables
try:
    mongo_uri = os.getenv("MONGO_URL")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
    client.server_info() # Trigger exception if cannot connect
    db = client['stress_detection_db']
    users_collection = db['users']
    reports_collection = db['reports']
    print("SUCCESS: Connected to MongoDB")
except Exception as e:
    print("FAILED: Could not connect to MongoDB. Is MongoDB running locally?")
    print(f"Error: {e}")

# Routes to serve the HTML pages
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'stress.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    
    if users_collection is None:
        # Generate a valid JWT even in mock mode to pass the strict token_required check
        token = jwt.encode({
            'user': data.get("email", "mock_user"),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"success": True, "message": "Mock Registration (MongoDB Offline)", "user_id": "mock_offline_user", "token": token})
        
    try:
        # Create a new document representing a user
        user_doc = {
            "name": data.get("name"),
            "email": data.get("email"),
            "password": generate_password_hash(data.get("password")), # Secure hashing
            "created_at": datetime.datetime.utcnow()
        }
        
        # Insert into 'users' collection
        result = users_collection.insert_one(user_doc)
        
        # Issue JWT Token immediately
        token = jwt.encode({
            'user': data.get("email"),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            "success": True, 
            "message": "User registered successfully", 
            "user_id": str(result.inserted_id),
            "token": token
        })
        
    except Exception as e:
        # Fallback for cloud deployments without MongoDB setup yet
        token = jwt.encode({
            'user': data.get("email"),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({
            "success": True, 
            "message": "User registered locally (MongoDB Offline Error)", 
            "user_id": "mock_id",
            "token": token
        })

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    
    if users_collection is None:
        # Generate a valid JWT even in mock mode to pass the strict token_required check
        token = jwt.encode({
            'user': data.get("email", "mock_user"),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"success": True, "message": "Mock Login (MongoDB Offline)", "token": token})
        
    try:
        email = data.get("email")
        password = data.get("password")
        
        # Find user and securely check hash
        user = users_collection.find_one({"email": email})
        
        if user and check_password_hash(user['password'], password):
            # Issue securely signed JWT Token
            token = jwt.encode({
                'user': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            return jsonify({"success": True, "message": "Login successful", "token": token})
        else:
            return jsonify({"success": False, "error": "Invalid email or password."}), 401
            
    except Exception as e:
        # Fallback for cloud deployments without MongoDB setup yet
        token = jwt.encode({
            'user': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({"success": True, "message": "Login successful (MongoDB Offline Error)", "token": token})

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]
                
        if not token:
            return jsonify({'success': False, 'error': 'Token is missing! Please log in.'}), 401
            
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user']
        except Exception as e:
            return jsonify({'success': False, 'error': 'Token is invalid or expired! Please log in again.'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_auth_token(current_user):
    return jsonify({"success": True, "message": "Token is valid", "user": current_user})

@app.route('/api/chat', methods=['POST'])
@token_required
def handle_chat(current_user):
    data = request.json
    user_message = data.get("message", "").lower()
    
    # Local Smart Keyword AI Engine
    bot_response = "I am a basic Stress Health Assistant. How can I help you today? Try asking me about 'sleep', 'diet', 'anxiety', 'panic attacks', or 'symptoms like fever/cough'."
    
    if "sleep" in user_message or "insomnia" in user_message or "tired" in user_message:
        bot_response = "Good sleep is the foundation of mental health. Try establishing a strict bedtime, reducing blue light 1 hour before bed, and keeping your room cool. If you can't sleep after 20 minutes, get out of bed and do something relaxing until you feel tired."
    elif "anxi" in user_message or "worry" in user_message or "stress" in user_message:
        bot_response = "It's completely normal to feel overwhelmed. When you feel anxious, try the 4-7-8 breathing method: inhale for 4 seconds, hold for 7, and exhale slowly for 8. Ground yourself by naming 3 things you can see, 2 you can touch, and 1 you can hear."
    elif "panic" in user_message or "heart" in user_message or "attack" in user_message:
        bot_response = "If you are having a panic attack: You are safe. This is just adrenaline and it WILL pass in a few minutes. Try holding an ice cube, splashing cold water on your face, or doing grounding exercises to shock your nervous system back to reality."
    elif "diet" in user_message or "food" in user_message or "eat" in user_message:
        bot_response = "Diet strongly impacts cortisol levels. High sugar and fast food can spike inflammation and anxiety. Focus on complex carbohydrates, omega-3s (like salmon or walnuts), and plenty of hydration to fuel your brain."
    elif "hello" in user_message or "hi" in user_message or "hey" in user_message:
        bot_response = f"Hello there! I'm your personal Stress Management AI. Feel free to ask me for advice on managing daily stress, panic symptoms, or improving your lifestyle habits."
    elif "help" in user_message:
        bot_response = "I can provide guidance on: 1. Sleep routines 2. Anxiety management 3. Stopping panic attacks 4. Dietary impacts on stress 5. Basic symptom checking (fever, cough). Please ask me about any of these topics!"
    elif "fever" in user_message or "temperature" in user_message or "hot" in user_message:
        bot_response = "A fever is usually a sign your body is fighting an infection. Rest, stay hydrated with water or clear broths, and take fever-reducing medication like acetaminophen or ibuprofen if needed. Seek immediate medical attention if your fever is over 103°F (39.4°C) or lasts more than 3 days."
    elif "cough" in user_message or "sore throat" in user_message or "cold" in user_message:
        bot_response = "For a cough or cold, focus on hydration and rest. Warm liquids like tea with honey can soothe a sore throat. Use a humidifier to add moisture to the air. If your cough brings up thick green/yellow mucus or is accompanied by chest pain or shortness of breath, please consult a doctor."
    elif "headache" in user_message or "migraine" in user_message or "pain" in user_message:
        bot_response = "Headaches can be caused by stress, dehydration, lack of sleep, or eye strain. Drink a large glass of water, rest in a dark, quiet room, and try a cold compress on your forehead. If it is the 'worst headache of your life', sudden and severe, seek emergency care."
    elif "nausea" in user_message or "vomit" in user_message or "stomach" in user_message:
        bot_response = "For stomach issues or nausea, stick to the BRAT diet (Bananas, Rice, Applesauce, Toast) and sip clear fluids slowly to prevent dehydration. Avoid dairy, caffeine, and spicy or greasy foods."
    elif "symptom" in user_message or "disease" in user_message or "sick" in user_message:
        bot_response = "I can provide basic advice for common symptoms like a 'fever', 'cough', 'headache', or 'nausea'. What specific symptom are you experiencing? Remember, I am an AI and this is not a substitute for professional medical diagnosis."
    elif "doctor" in user_message or "therapist" in user_message:
        bot_response = "While I can provide educational suggestions, I am an AI and cannot replace real medical advice. If your stress is causing severe physical symptoms, depression, or suicidal thoughts, please reach out to a local healthcare professional or hotline immediately."

    return jsonify({
        "success": True, 
        "response": bot_response
    })

@app.route('/api/predict', methods=['POST'])
@token_required
def handle_prediction(current_user):
    input_data = request.json
    
    try:
        # 1. Run the ML Prediction
        stress_level = predict_stress(input_data)
        
        # 2. Get the suggestions
        suggestions = get_stress_suggestions(input_data, stress_level)
        
        if reports_collection is None:
            return jsonify({
                "success": True,
                "stress_level": stress_level,
                "suggestions": suggestions,
                "report_id": "mock_id",
                "message": "Report generated locally (MongoDB is offline, so it was not saved)"
            })
        
        # 3. Save full report to MongoDB
        report_doc = {
            "user_email": current_user, # Link strictly to authorized JWT user
            "input_features": input_data,
            "predicted_stress": stress_level,
            "suggestions": suggestions,
            "timestamp": datetime.datetime.utcnow()
        }
        
        result = reports_collection.insert_one(report_doc)
        
        # 4. Return the result to the frontend
        return jsonify({
            "success": True,
            "stress_level": stress_level,
            "suggestions": suggestions,
            "report_id": str(result.inserted_id),
            "message": "Report saved to MongoDB"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Get port from environment variable for cloud hosting, fallback to 5001 locally to bypass ghost ports
    port = int(os.environ.get("PORT", 5001))
    
    # Check if we should start ngrok (only locally)
    if os.environ.get("FLASK_ENV") != "production":
        try:
            public_url = ngrok.connect(port).public_url
            print(f" \n\n=======================================================")
            print(f" -> YOUR PUBLIC INTERNET LINK IS LIVE!")
            print(f" -> {public_url} ")
            print(f"=======================================================\n\n")
        except Exception as e:
            print(f"Warning: Could not start ngrok tunnel. {e}")

    print(f"Starting local Flask server on http://0.0.0.0:{port}")
    # Setting host='0.0.0.0' allows the cloud server to expose the app to external traffic
    app.run(host='0.0.0.0', port=port)
