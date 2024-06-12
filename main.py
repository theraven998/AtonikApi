from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from flask_cors import CORS
from bson import json_util

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'Cxv24KPcpogXnqgpDAXF'
jwt = JWTManager(app)
CORS(app)

client = MongoClient("127.0.0.1:6043")
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
    document_number = data.get('document_number')
    usuario= data.get("username")

    if users_collection.find_one({"document_number": document_number}):
        return jsonify({"msg": "Document number already exists"}), 400

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({
        "usuario": usuario,
        "name": name,
        "password": hashed_password,
        "phone": phone,
        "birthdate": birthdate,
        "document_number": document_number
    })

    return jsonify({"msg": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
@jwt_required()
def login():
    data = request.get_json()
    document_number = data.get('document_number')
    password = data.get('password')

    user = users_collection.find_one({"document_number": document_number})

    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=document_number)
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Bad document number or password"}), 401

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/api/main', methods=['GET'])
@jwt_required()
def main():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"document_number": current_user}, {"_id": 0})
    if user:
        return json_util.dumps(user), 200
    else:
        return jsonify({"msg": "User not found"}), 404
@app.route('/api/events/', methods=['GET'])
def events():
   date = request.args.get('date')
   eventos_lista=[]
 
   for evento in events_collection.find({"date":date}):
        eventos_lista.append(evento)
   eventos_json = json_util.dumps(eventos_lista, default=str)

   return eventos_json

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
