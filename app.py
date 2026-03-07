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
        return jsonify({"success": True, "message": "Mock Registration (MongoDB Offline)", "user_id": "mock_offline_user", "token": "mock_token"})
        
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
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    
    if users_collection is None:
        return jsonify({"success": True, "message": "Mock Login (MongoDB Offline)", "token": "mock_token"})
        
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
        return jsonify({"success": False, "error": str(e)}), 500

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
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Get port from environment variable for cloud hosting, fallback to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    
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
