from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from flask_cors import CORS
import requests
import json
import random
from bson import json_util, ObjectId
import pytz
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'Cxv24KPcpogXnqgpDAXF'
jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Permitir todas las solicitudes desde cualquier origen para las rutas bajo /api

# Configurar la conexión a la base de datos
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client['atonik']
users_collection = db['users']
events_collection = db['events']

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')
    phone = data.get('phone')
    birthdate = data.get('birthdate')
    usuario = data.get("username")

    if users_collection.find_one({"username": usuario}):
        return jsonify({"msg": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({
        "usuario": usuario,
        "name": name,
        "password": hashed_password,
        "phone": phone,
        "birthdate": birthdate,
    })
    user = users_collection.find_one({"usuario": usuario})
    access_token = create_access_token(identity={"usuario": usuario, "name": name})

    return jsonify({"msg": "User created successfully", "access_token": access_token}), 201

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'OPTIONS received'}), 200
    data = request.get_json()
    usuario = data.get('usuario')
    password = data.get('password')

    try:
        user = users_collection.find_one({"usuario": usuario})
        if user and check_password_hash(user['password'], password):
            user['_id'] = str(user['_id'])
            access_token = create_access_token(identity=user)
            return jsonify({"message": "Logged in successfully", "access_token": access_token}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"msg": "Bad username or password"}), 401

    return jsonify({"msg": "Bad username or password"}), 401

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/api/add_profile_photo', methods=['POST'])
def add_profile_photo():
    data = request.json
    username = data.get('username')
    photo_url = data.get('photo_url')
    
    if not username or not photo_url:
        return jsonify({"msg": "Username and photo_url are required"}), 400

    user = users_collection.find_one({"usuario": username})
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user['profile_photo'] = photo_url
    users_collection.update_one({"usuario": username}, {"$set": user})

    return jsonify({"msg": "Profile photo added successfully"}), 200

@app.route('/api/main', methods=['GET'])
@jwt_required()
def main():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"usuario": current_user['usuario']}, {"_id": 0})
    if user:
        return json_util.dumps(user), 200
    else:
        return jsonify({"msg": "User not found"}), 404

@app.route('/api/events', methods=['GET'])
def events():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error": "Date parameter is missing"}), 400

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        start_of_day = datetime(date_obj.year, date_obj.month, date_obj.day, tzinfo=pytz.UTC)
        end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    eventos_lista = []

    for evento in events_collection.find({
        "date": {
            "$gte": start_of_day,
            "$lt": end_of_day
        }
    }):
        evento['_id'] = str(evento['_id'])
        eventos_lista.append(evento)

    eventos_json = json_util.dumps(eventos_lista, default=str)
    return eventos_json

@app.route('/api/events', methods=['POST'])
def add_event():
    data = request.json

    event = {
        "date": data.get("date"),
        "place": data.get("place"),
        "name": data.get("name"),
        "description": data.get("description"),
        "image": data.get("image"),
        "price": data.get("price"),
        "min_age": data.get("min_age"),
        "organizer": data.get("organizer"),
        "color": data.get("color"),
        "relevance": data.get("relevance")
    }

    result = events_collection.insert_one(event)
    return jsonify({"message": "Event added successfully", "event_id": str(result.inserted_id)}), 201

@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.json

    updated_event = {
        "date": data.get("date"),
        "place": data.get("place"),
        "name": data.get("name"),
        "description": data.get("description"),
        "image": data.get("image"),
        "price": data.get("price"),
        "min_age": data.get("min_age"),
        "organizer": data.get("organizer"),
        "color": data.get("color"),
        "relevance": data.get("relevance")
    }

    result = events_collection.update_one(
        {"_id": ObjectId(event_id)},
        {"$set": updated_event}
    )

    if result.matched_count > 0:
        return jsonify({"message": "Event updated successfully"}), 200
    else:
        return jsonify({"message": "Event not found"}), 404

@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    result = events_collection.delete_one({"_id": ObjectId(event_id)})

    if result.deleted_count > 0:
        return jsonify({"message": "Event deleted successfully"}), 200
    else:
        return jsonify({"message": "Event not found"}), 404

@app.route('/api/send_verification_code', methods=['POST'])
def send_verification_code():
    data = request.get_json()
    phone = data.get('phone')

    if not phone:
        return jsonify({"msg": "Phone number is required"}), 400

    codigo = str(random.randint(100000, 999999))

    url = "https://graph.facebook.com/v20.0/379440005253161/messages"
    access_token = "EAAVnZB6scnn0BO66aZCZBcZAtJFnTmuIcBj1A4d46DAM4Ce5lcNJI0TjCVrCpVMIMNoAQOFZBTyXzQWBOPXHcf4ejNcdgOu7pP3QZBcxEIFZAZB0HDZCOwRBBTZBFSKYjennFQ4pquxZBZAwdcXtUhCpQmbvmElIl4xHrpbxlTd3SVvrwlA7xqcOV07A8qIM6P5kUK7R8gZDZD"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    message_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone, 
        "type": "template",
        "template": {
            "name": "verification", 
            "language": {
                "code": "es"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": codigo
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {
                            "type": "text",
                            "text": codigo
                        }
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(message_data))
        response.raise_for_status()
        return jsonify({"msg": "Verification code sent successfully"}), 200

    except requests.exceptions.RequestException as e:
        print(f"Error sending verification code: {e}")
        if e.response:
            error_response = e.response.json()
            print(f"Error details: {error_response}")
        else:
            print("No response received.")
        return jsonify({"msg": "Failed to send verification code"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
