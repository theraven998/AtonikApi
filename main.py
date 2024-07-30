from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from flask_cors import CORS
from bson import json_util


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'Cxv24KPcpogXnqgpDAXF'
jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Permitir todas las solicitudes desde cualquier origen para las rutas bajo /api

client = MongoClient("127.0.0.1:27017")
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
    usuario= data.get("username")

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

    return jsonify({"msg": "User created successfully"}), 201

from bson import ObjectId

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
            # Convertir el ObjectId a una cadena
            user['_id'] = str(user['_id'])
            access_token = create_access_token(identity=user)
            print("Inicio de sesión correcto")  
            return jsonify({"message": "Logged in successfully", "access_token": access_token}), 200
    except Exception as e:
        print(f"Error: {str(e)}")  # Agregaste este mensaje
        return jsonify({"msg": "Bad username or password"}), 401

    return jsonify({"msg": "Bad username or password"}), 401

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/api/main', methods=['GET'])
@jwt_required()
def main():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"usuario": user}, {"_id": 0})
    if user:
        return json_util.dumps(user), 200
    else:
        return jsonify({"msg": "User not found"}), 404

@app.route('/api/events/', methods=['GET'])
def events():
    date = request.args.get('date')
    eventos_lista = []
 
    for evento in events_collection.find({"date":date}):
        eventos_lista.append(evento)
    eventos_json = json_util.dumps(eventos_lista, default=str)

    return eventos_json
@app.route('/api/users', methods=['GET'])
def get_users():
    # Obtener todos los usuarios de la colección 'users'
    all_users = list(users_collection.find({}, {'_id': 0}))

    # Si hay usuarios encontrados, devolverlos como JSON
    if all_users:
        return json_util.dumps(all_users), 200
    else:
        return jsonify({"msg": "No users found"}), 404

@app.route('/api/delete_users', methods=['DELETE'])
def delete_users():
    result = users_collection.delete_many({})
    if result.deleted_count > 0:
        return jsonify({"msg": "All users deleted successfully"}), 200
    else:
        return jsonify({"msg": "No users found"}), 404
            
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
