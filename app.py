import uuid 
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import os
from werkzeug.utils import secure_filename
import random
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)

client = MongoClient('mongodb://localhost:27017/') 
db = client['pothole_app']
users_collection = db['users']
complaints_collection = db['complaints']
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


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
    return render_template('home.html', user=session.get('user'))

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


@app.route('/your_complaint_status', methods=['GET', 'POST'])
@login_required
def your_complaint_status():
    user_email = session['user']
    complaint_statuses = list(complaints_collection.find({'user_email': user_email}))
    return render_template('your_complaint_status.html', complaint_statuses=complaint_statuses)


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
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        updated_complaint = complaints_collection.find_one({'_id': ObjectId(complaint_id)})
        return jsonify({
            'upvotes': updated_complaint.get('upvotes', 0),
            'downvotes': updated_complaint.get('downvotes', 0),
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
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        updated_complaint = complaints_collection.find_one({'_id': ObjectId(complaint_id)})
        return jsonify({
            'upvotes': updated_complaint.get('upvotes', 0),
            'downvotes': updated_complaint.get('downvotes', 0),
            'user_vote': 'down' if current_user in updated_complaint.get('downvoted_by', []) else None
        })
    else:
        return redirect(url_for('view_complaints'))


@app.route('/submit_complaint', methods=['POST'])
@login_required
def submit_complaint():
    image = request.files.get('image')
    description = request.form.get('description')
    contact = request.form.get('contact')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    image_filename = "no_image.jpg"
    
    if image and image.filename != '' and allowed_file(image.filename):
        try:
            upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_folder, exist_ok=True)
            unique_filename = f"{uuid.uuid4()}_{secure_filename(image.filename)}"
            filepath = os.path.join(upload_folder, unique_filename)
            image.save(filepath)
            
            image_filename = f"images/{unique_filename}"
            print(f"Image saved to: {filepath}")
        except Exception as e:
            print(f"Error saving image: {e}")
    else:
        print("No valid image uploaded or image format not allowed")
    complaint = {
        'user_email': session['user'],
        'image': image_filename,  
        'description': description,
        'contact': contact,
        'latitude': latitude,
        'longitude': longitude,
        'status': "Complaint Registered (Unverified)",
        'priority': random.randint(1, 100),
        'upvotes': 0,
        'downvotes': 0,  
        'upvoted_by': [],
        'downvoted_by': []  
    }
    complaints_collection.insert_one(complaint)
    print("Complaint Added:", complaint)
    return redirect(url_for('home'))



@app.route('/register', methods=['GET', 'POST'])
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



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({'email': email})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user'] = email
            session['first_name'] = user.get('first_name', '')  
            return redirect(url_for('home'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)