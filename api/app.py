from flask import Flask, request, jsonify
from schemes import schemes_bp
from scan import scans_bp
from flask_cors import CORS
from pymongo import MongoClient, ReturnDocument
import os
from dotenv import load_dotenv
import datetime # Import datetime to track user activity
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
CORS(app)
app.register_blueprint(schemes_bp)
app.register_blueprint(scans_bp)

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = 'cattle-app-db'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db['users']

# --- GET USER BY FIREBASE UID AND ROLE ---
@app.route('/api/get-user', methods=['GET'])
def get_user():
    firebase_uid = request.args.get('firebase_uid')
    role = request.args.get('role')
    if not firebase_uid or not role:
        return jsonify({'message': 'firebase_uid and role required'}), 400
    user = users.find_one({'firebase_uid': firebase_uid, 'role': role})
    if not user:
        return jsonify({'message': 'User not found'}), 404
    user['_id'] = str(user['_id'])
    return jsonify({'user': user}), 200

# --- HYBRID: SYNC USER FROM FIREBASE AUTH ---
@app.route('/api/sync-user', methods=['POST'])
def sync_user():
    data = request.get_json(force=True)
    firebase_uid = data.get('firebase_uid')
    email = data.get('email')
    role = data.get('role')
    name = data.get('name')
    if not firebase_uid or not email or not role:
        return jsonify({'message': 'firebase_uid, email, and role are required.'}), 400
    # Allow same email for different roles, but unique on (firebase_uid, role)
    user_doc = {
        'firebase_uid': firebase_uid,
        'email': email,
        'role': role,
        'name': name,
        'lastLoginAt': datetime.datetime.utcnow(),
    }
    updated_user = users.find_one_and_update(
        {'firebase_uid': firebase_uid, 'role': role},
        {
            '$set': user_doc,
            '$setOnInsert': {'createdAt': datetime.datetime.utcnow()}
        },
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    updated_user['_id'] = str(updated_user['_id'])
    return jsonify({'message': 'User synced', 'user': updated_user}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({ 'status': 'ok' })




if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port)


