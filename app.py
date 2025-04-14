# app.py
import uuid 
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import os
from werkzeug.utils import secure_filename
import random
from bson.objectid import ObjectId
import uuid
import json
import cv2
import supervision as sv
from roboflow import Roboflow
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)

rf = Roboflow(api_key="ZYZiqRfxocCQlUyr6YW9")
project = rf.workspace().project("pothole-detection-i00zy")
model = project.version(2).model

client = MongoClient('mongodb://localhost:27017/')

db = client['pothole_app']
users_collection = db['users']
resolved_complaints_collection = db['resolved_complaints']


complaints_collection = db['complaints']
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif', 'webp','avif'}



complaints=[]

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('home.html', user=session.get('user'),first_name=session.get('first_name'))

@app.route('/file_complaint')
@login_required
def file_complaint():
    return render_template('file_complaint.html')


@app.route('/view_complaints')
@login_required
def view_complaints():
    all_complaints = list(complaints_collection.find({}))
    current_user = session['user']
    
    for complaint in all_complaints:
        if current_user in complaint.get('upvoted_by', []):
            complaint['user_vote'] = 'up'
        elif current_user in complaint.get('downvoted_by', []):
            complaint['user_vote'] = 'down'
        else:
            complaint['user_vote'] = None
            
    return render_template('view_complaints.html', complaints=all_complaints)


# @app.route('/your_complaint_status', methods=['GET', 'POST'])
# @login_required
# def your_complaint_status():
#     user_email = session['user']
#     complaint_statuses = list(complaints_collection.find({'user_email': user_email}))
#     return render_template('your_complaint_status.html', complaint_statuses=complaint_statuses)
@app.route('/your_complaint_status')
@login_required
def your_complaint_status():
    # Get the current user's email from the session
    user_email = session.get('user')
    user = users_collection.find_one({"email": user_email})
    
    if not user:
        return redirect(url_for('home'))
    # Get active complaints for the current user
    active_complaints = list(complaints_collection.find({"user_email": user_email}))
    # Get resolved complaints for the current user
    resolved_complaints = list(resolved_complaints_collection.find({"user_email": user_email}))
    
    complaints_count = len(active_complaints) + len(resolved_complaints)
    resolved_count = len(resolved_complaints)
    pending_count = 0
    for complaint in active_complaints:
        if complaint.get('complaint_approved_by_admin', False):
            pending_count += 1
    
    return render_template(
        'your_complaint_status.html',
        user=user,
        active_complaints=active_complaints,
        resolved_complaints=resolved_complaints,
        complaints_count=complaints_count,
        resolved_count=resolved_count,
        pending_count=pending_count
    )

@app.route('/upvote/<complaint_id>', methods=['POST'])
@login_required
def upvote_complaint(complaint_id):
    current_user = session['user']
    complaint = complaints_collection.find_one({'_id': ObjectId(complaint_id)})

    if complaint:
        upvoted_by = complaint.get('upvoted_by', [])
        downvoted_by = complaint.get('downvoted_by', [])
        
        if current_user in upvoted_by:
            complaints_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$inc': {'upvotes': -1},
                    '$pull': {'upvoted_by': current_user}
                }
            )

        elif current_user in downvoted_by:
            complaints_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$inc': {'upvotes': 1, 'downvotes': -1},
                    '$pull': {'downvoted_by': current_user},
                    '$push': {'upvoted_by': current_user}
                }
            )

        else:
            complaints_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$inc': {'upvotes': 1},
                    '$push': {'upvoted_by': current_user}
                }
            )
        
        updated_complaint = complaints_collection.find_one({'_id': ObjectId(complaint_id)})
        
        pothole_count = updated_complaint.get('pothole_count', 0)
        normalized_area = updated_complaint.get('normalized_area', 0)
        upvotes = updated_complaint.get('upvotes', 0)
        downvotes = updated_complaint.get('downvotes', 0)
        
        priority=10*pothole_count+3*normalized_area+5*upvotes-5*downvotes
        
        complaints_collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$set': {'priority': priority}}
        )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        updated_complaint = complaints_collection.find_one({'_id': ObjectId(complaint_id)})
        return jsonify({
            'upvotes': updated_complaint.get('upvotes', 0),
            'downvotes': updated_complaint.get('downvotes', 0),
            'priority': updated_complaint.get('priority', 0),
            'user_vote': 'up' if current_user in updated_complaint.get('upvoted_by', []) else None
        })
    else:
        return redirect(url_for('view_complaints'))


@app.route('/downvote/<complaint_id>', methods=['POST'])
@login_required
def downvote_complaint(complaint_id):
    current_user = session['user']
    complaint = complaints_collection.find_one({'_id': ObjectId(complaint_id)})

    if complaint:
        upvoted_by = complaint.get('upvoted_by', [])
        downvoted_by = complaint.get('downvoted_by', [])
        
        if current_user in downvoted_by:
            complaints_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$inc': {'downvotes': -1},
                    '$pull': {'downvoted_by': current_user}
                }
            )
        elif current_user in upvoted_by:
            complaints_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$inc': {'downvotes': 1, 'upvotes': -1},
                    '$pull': {'upvoted_by': current_user},
                    '$push': {'downvoted_by': current_user}
                }
            )
        else:
            complaints_collection.update_one(
                {'_id': ObjectId(complaint_id)},
                {
                    '$inc': {'downvotes': 1},
                    '$push': {'downvoted_by': current_user}
                }
            )
        
        updated_complaint = complaints_collection.find_one({'_id': ObjectId(complaint_id)})
        pothole_count = updated_complaint.get('pothole_count', 0)
        normalized_area = updated_complaint.get('normalized_area', 0)
        upvotes = updated_complaint.get('upvotes', 0)
        downvotes = updated_complaint.get('downvotes', 0)
        
        priority = 10 * pothole_count + 3 * normalized_area + 5 * upvotes - 5 * downvotes
        complaints_collection.update_one(
            {'_id': ObjectId(complaint_id)},
            {'$set': {'priority': priority}}
        )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        updated_complaint = complaints_collection.find_one({'_id': ObjectId(complaint_id)})
        return jsonify({
            'upvotes': updated_complaint.get('upvotes', 0),
            'downvotes': updated_complaint.get('downvotes', 0),
            'priority': updated_complaint.get('priority', 0),
            'user_vote': 'down' if current_user in updated_complaint.get('downvoted_by', []) else None
        })
    else:
        return redirect(url_for('view_complaints'))

# @app.route('/submit_complaint', methods=['POST'])
# @login_required
# def submit_complaint():
#     image = request.files.get('image')
#     description = request.form.get('description')
#     contact = request.form.get('contact')
#     latitude = request.form.get('latitude')
#     longitude = request.form.get('longitude')
#     image_filename = "no_image.jpg"
    
#     if image and image.filename != '' and allowed_file(image.filename):
#         try:
#             upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
#             os.makedirs(upload_folder, exist_ok=True)
#             unique_filename = f"{uuid.uuid4()}_{secure_filename(image.filename)}"
#             filepath = os.path.join(upload_folder, unique_filename)
#             image.save(filepath)
            
#             image_filename = f"images/{unique_filename}"
#             print(f"Image saved to: {filepath}")
#         except Exception as e:
#             print(f"Error saving image: {e}")
#     else:
#         print("No valid image uploaded or image format not allowed")
#     complaint = {
#         'user_email': session['user'],
#         'image': image_filename,  
#         'description': description,
#         'contact': contact,
#         'latitude': latitude,
#         'longitude': longitude,
#         'status': "Complaint Registered (Unverified)",
#         'priority': random.randint(1, 100),
#         'upvotes': 0,
#         'downvotes': 0,  
#         'upvoted_by': [],
#         'downvoted_by': []  
#     }
#     complaints_collection.insert_one(complaint)
#     print("Complaint Added:", complaint)
#     return redirect(url_for('home'))

@app.route('/submit_complaint', methods=['POST'])
@login_required
def submit_complaint():
    image = request.files.get('image')
    description = request.form.get('description')
    contact = request.form.get('contact')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    image_filename = "no_image.jpg"
    validated_by_model = 0
    pothole_count = 0
    normalized_area = 0
    
    if image and image.filename != '' and allowed_file(image.filename):
        try:
            upload_folder=os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_folder,exist_ok=True)
            unique_filename=f"{uuid.uuid4()}_{secure_filename(image.filename)}"
            filepath=os.path.join(upload_folder, unique_filename)
            image.save(filepath)
            
            image_filename = f"images/{unique_filename}"
            print(f"Image saved to: {filepath}")
            result = model.predict(filepath).json()
            predictions = result["predictions"]
            xyxy = []
            confidences = []
            class_ids = []

            for pred in predictions:
                x, y, w, h = pred["x"], pred["y"], pred["width"], pred["height"]
                x1 = x - w / 2
                y1 = y - h / 2
                x2 = x + w / 2
                y2 = y + h / 2
                xyxy.append([x1, y1, x2, y2])
                confidences.append(pred["confidence"])
                class_ids.append(0) 
                # Assuming all are potholes (class 0)

            if xyxy:  
                xyxy = np.array(xyxy)
                confidences = np.array(confidences)
                class_ids = np.array(class_ids)

                detections = sv.Detections(xyxy=xyxy, confidence=confidences, class_id=class_ids)
                potholes = detections[detections.class_id == 0]

                bounding_boxes = potholes.xyxy
                areas = (bounding_boxes[:, 2] - bounding_boxes[:, 0]) * (bounding_boxes[:, 3] - bounding_boxes[:, 1])
                total_area = float(np.sum(areas))
                pothole_count = len(potholes)

                img = cv2.imread(filepath)
                image_height, image_width = img.shape[:2]
                image_area = image_height * image_width
                normalized_area = total_area / image_area
                
                if pothole_count > 0:
                    validated_by_model = 1
            
        except Exception as e:
            print(f"Error processing image: {e}")
    else:
        print("No valid image uploaded or image format not allowed")
    
    if image and image.filename != '' and validated_by_model == 0:
        return redirect(url_for('home'))
    
    # Note: Default values for pothole_count and normalized_area are 0
    priority=10*pothole_count+3*normalized_area
    
    complaint={
        'user_email': session['user'],
        'image': image_filename,  
        'description': description,
        'contact': contact,
        'latitude': latitude,
        'longitude': longitude,
        'status': "Complaint Registered (Unverified)" if validated_by_model == 0 else "Complaint Registered (Verified)",
        'priority': priority,
        'upvotes': 0,
        'downvotes': 0,  
        'upvoted_by': [],
        'downvoted_by': [],
        'validated_by_model': validated_by_model,
        'pothole_count': pothole_count,
        'normalized_area': normalized_area,
        'complaint_approved_by_admin': False,
        'complaint_resolved': False ,
        'submission_date': datetime.now()
    }
    
    complaints_collection.insert_one(complaint)
    print("Complaint Added:", complaint)
    return redirect(url_for('home'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        if users_collection.find_one({'email': email}):
            return "User already exists!"

        users_collection.insert_one({
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password
        })

        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/admin/resolved')
def admin_resolved():
    if not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    resolved = list(resolved_complaints_collection.find().sort("resolution_date", -1))
    
    return render_template('admin_resolved.html', resolved_complaints=resolved)

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         user = users_collection.find_one({'email': email})
#         if user and bcrypt.check_password_hash(user['password'], password):
#             session['user'] = email
#             session['first_name'] = user.get('first_name', '')  
#             return redirect(url_for('home'))
#         else:
#             return "Invalid credentials!"
#     return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email == "admin@gmail.com" and password == "12345678":
            session['user'] = email
            session['is_admin'] = True
            session['first_name'] = "Admin"
            return redirect(url_for('admin_dashboard'))
        
        user = users_collection.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user'] = email
            session['is_admin'] = False
            session['first_name'] = user.get('first_name', '')  
            return redirect(url_for('home'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    total_users = users_collection.count_documents({})
    verified_requests = complaints_collection.count_documents({"validated_by_model": 1})
    approved_requests = complaints_collection.count_documents({"complaint_approved_by_admin": True})
    resolved_requests = resolved_complaints_collection.count_documents({})

    complaints = list(complaints_collection.find().sort("priority", -1))
    
    return render_template('admin_home.html', 
                          total_users=total_users,
                          verified_requests=verified_requests,
                          approved_requests=approved_requests,
                          resolved_requests=resolved_requests,
                          complaints=complaints)

@app.route('/admin/update_complaint', methods=['POST'])
def update_complaint():
    if not session.get('is_admin', False):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    complaint_id = request.form.get('complaint_id')
    action_type = request.form.get('action_type')
    
    try:
        complaint = complaints_collection.find_one({"_id": ObjectId(complaint_id)})
        if not complaint:
            return jsonify({"success": False, "message": "Complaint not found"}), 404
        if action_type == 'approve':
            complaints_collection.update_one(
                {"_id": ObjectId(complaint_id)},
                {"$set": {
                    "complaint_approved_by_admin": True,
                    "status": "Approved by Admin",
                    "approval_date": datetime.now()
                }}
            )
            
        elif action_type == 'reject':
            complaints_collection.delete_one({"_id": ObjectId(complaint_id)})
            
        elif action_type == 'resolve':
            complaint["resolution_date"] = datetime.now()
            complaint["status"] = "Resolved"
            resolved_complaints_collection.insert_one(complaint)
            complaints_collection.delete_one({"_id": ObjectId(complaint_id)})
            
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"Error processing complaint action: {e}")
        return jsonify({"success": False, "message": str(e)}), 500



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)