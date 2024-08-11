from flask import Flask, request, jsonify, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import hashlib
import os

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)  # This will enable CORS for all routes

app.secret_key = 'code-fury-server'

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<User {self.name}>'

# Define the SOSMessage model
class SOSMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f'<SOSMessage id={self.id} user_id={self.user_id} location=({self.latitude}, {self.longitude})>'

def hash_password(password):
    """Hash the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/signup', methods=['POST'])
def register():
    if request.is_json:
        try:
            data = request.get_json()
            name = data['name'].strip()
            email = data['email'].strip()
            password = data['password'].strip()
            phone = data['phone'].strip()
        except KeyError as e:
            return jsonify(success=False, message=f'Missing field: {str(e)}'), 400

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify(success=False, message='User already exists with this email address'), 409

        password_hash = hash_password(password)
        print(f"Registering user with email: {email}, hashed password: {password_hash}")

        new_user = User(name=name, email=email, password_hash=password_hash, phone=phone)

        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify(success=True, message='Registration successful!', user={'id': new_user.id, 'name': new_user.name, 'email': new_user.email, 'phone': new_user.phone})
        except Exception as e:
            db.session.rollback()
            return jsonify(success=False, message=f'Error: {str(e)}'), 500
    else:
        return jsonify(success=False, message="Request must be JSON"), 400

@app.route('/api/login', methods=['POST'])
def login():
    if request.is_json:
        try:
            data = request.get_json()
            email = data['email'].strip()
            password = data['password'].strip()
        except KeyError as e:
            return jsonify(success=False, message=f'Missing field: {str(e)}'), 400

        password_hash = hash_password(password)
        print(f"Login attempt with email: {email}, hashed password: {password_hash}")

        user = User.query.filter_by(email=email, password_hash=password_hash).first()

        if user:
            print(f"Login successful for user: {user.name}")
            return jsonify(success=True, user={'id': user.id, 'name': user.name, 'email': user.email, 'phone': user.phone})
        else:
            print("Invalid login credentials")
            return jsonify(success=False, message='Invalid email or password'), 401
    else:
        return jsonify(success=False, message="Request must be JSON"), 400

@app.route('/api/sos', methods=['POST'])
def receive_sos():
    if request.is_json:
        try:
            data = request.get_json()
            location = data['location']
            lat = location['lat']
            lon = location['lon']
            user_id = data.get('userId')  # userId can be null, so use .get()

            # Create a new SOSMessage instance
            new_sos = SOSMessage(latitude=lat, longitude=lon, user_id=user_id)

            # Store the SOSMessage in the database
            db.session.add(new_sos)
            db.session.commit()

            return jsonify(success=True, message='SOS message received!', sos_id=new_sos.id), 201

        except KeyError as e:
            return jsonify(success=False, message=f'Missing field: {str(e)}'), 400
        except Exception as e:
            db.session.rollback()
            return jsonify(success=False, message=f'Error: {str(e)}'), 500
    else:
        return jsonify(success=False, message="Request must be JSON"), 400

@app.route('/<path:path>')
def catch_all(path):
    # Serve static files correctly
    if os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    else:
        return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create the SOSMessage table along with others

    app.run(debug=True)
