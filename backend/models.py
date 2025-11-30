from backend.app import db
from sqlalchemy.dialects.postgresql import JSON
import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(128), nullable=False)
    credentials = db.relationship('WebAuthnCredential', backref='user', lazy=True)
    scans = db.relationship('Scan', backref='user', lazy=True)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'

class WebAuthnCredential(db.Model):
    __tablename__ = 'webauthn_credentials'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    credential_id = db.Column(db.LargeBinary, unique=True, nullable=False)
    public_key = db.Column(db.LargeBinary, nullable=False)
    sign_count = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<WebAuthnCredential {self.id}>'

class Scan(db.Model):
    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    model_path = db.Column(db.String(255), nullable=True)
    preferences = db.Column(JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Scan {self.id}>'
