import os
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from datetime import datetime
from bson import ObjectId
import uuid

scans_bp = Blueprint('scans', __name__)

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = 'cattle-app-db'
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
scans_collection = db['scans']

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# POST /api/scan/process-image
@scans_bp.route('/api/scan/process-image', methods=['POST'])
def process_image():
    user_id = request.form.get('user_id')
    if 'image' not in request.files or not user_id:
        return jsonify({'error': 'Image and user_id required'}), 400
    image = request.files['image']
    filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    image.save(filepath)
    # Placeholder for AI/ML result
    identification_result = 'pending'  # Replace with actual result later
    scan_doc = {
        'user_id': user_id,
        'image_url': filepath,
        'result': identification_result,
        'timestamp': datetime.utcnow()
    }
    scans_collection.insert_one(scan_doc)
    return jsonify({'message': 'Image processed', 'scan': scan_doc}), 200

# GET /api/scans/history?user_id=xxx
@scans_bp.route('/api/scans/history', methods=['GET'])
def scan_history():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    scans = list(scans_collection.find({'user_id': user_id}).sort('timestamp', -1))
    for s in scans:
        s['_id'] = str(s['_id'])
        s['timestamp'] = s['timestamp'].isoformat()
    return jsonify({'scans': scans})
