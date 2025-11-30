import os
import uuid
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import webauthn
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential

load_dotenv()

app = Flask(__name__, template_folder='../frontend/templates')
UPLOAD_FOLDER = 'backend/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from backend.models import User, WebAuthnCredential, Scan

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

RP_ID = "localhost"
RP_NAME = "Personalized Consumer Product"
ORIGIN = "http://localhost:5000"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return f"Hello, {current_user.display_name}!"

@app.route('/scan')
@login_required
def scan():
    return render_template('scan.html')

@app.route('/api/register/begin', methods=['POST'])
def register_begin():
    username = request.json.get('username')
    display_name = request.json.get('display_name')

    if not username or not display_name:
        return jsonify({"error": "Missing username or display_name"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    user = User(username=username, display_name=display_name)
    db.session.add(user)
    db.session.commit()

    options = webauthn.generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(user.id).encode('utf-8'),
        user_name=user.username,
        user_display_name=user.display_name,
    )

    session['challenge'] = options.challenge

    return jsonify(options.dict())

@app.route('/api/register/complete', methods=['POST'])
def register_complete():
    credential = RegistrationCredential.parse_raw(request.data)
    challenge = session.pop('challenge', None)

    verification = webauthn.verify_registration_response(
        credential=credential,
        expected_challenge=challenge,
        expected_origin=ORIGIN,
        expected_rp_id=RP_ID,
        require_user_verification=True
    )

    user = User.query.get(int(verification.user_id))
    new_credential = WebAuthnCredential(
        user_id=user.id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count
    )
    db.session.add(new_credential)
    db.session.commit()

    login_user(user)

    return jsonify({"success": True})

@app.route('/api/login/begin', methods=['POST'])
def login_begin():
    username = request.json.get('username')
    if not username:
        return jsonify({"error": "Missing username"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    credentials = WebAuthnCredential.query.filter_by(user_id=user.id).all()
    if not credentials:
        return jsonify({"error": "No credentials found for user"}), 404

    options = webauthn.generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=[{"id": cred.credential_id, "type": "public-key"} for cred in credentials],
    )

    session['challenge'] = options.challenge

    return jsonify(options.dict())

@app.route('/api/login/complete', methods=['POST'])
def login_complete():
    credential = AuthenticationCredential.parse_raw(request.data)
    challenge = session.pop('challenge', None)

    user = User.query.join(WebAuthnCredential).filter(WebAuthnCredential.credential_id == credential.id).first()
    if not user:
        return jsonify({"error": "User not found for this credential"}), 404

    db_credential = WebAuthnCredential.query.filter_by(credential_id=credential.id).first()

    verification = webauthn.verify_authentication_response(
        credential=credential,
        expected_challenge=challenge,
        expected_origin=ORIGIN,
        expected_rp_id=RP_ID,
        credential_public_key=db_credential.public_key,
        credential_current_sign_count=db_credential.sign_count
    )

    db_credential.sign_count = verification.new_sign_count
    db.session.commit()

    login_user(user)

    return jsonify({"success": True})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "Logged out"

@app.route('/api/scans', methods=['POST'])
@login_required
def submit_scan():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    if 'scan' not in request.files:
        return jsonify({"error": "No scan found"}), 400
    scan_file = request.files['scan']
    if scan_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    style = request.form.get('style')
    color = request.form.get('color')
    material = request.form.get('material')
    features = request.form.get('features')

    if scan_file:
        filename = f"{uuid.uuid4()}.png"
        scan_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        scan_file.save(scan_path)

        new_scan = Scan(
            user_id=current_user.id,
            image_path=scan_path,
            preferences={
                "style": style,
                "color": color,
                "material": material,
                "features": features
            }
        )
        db.session.add(new_scan)
        db.session.commit()

        return jsonify({"success": True}), 200

    return jsonify({"error": "An error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)
