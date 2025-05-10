from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for storing user account information"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with UserProgress
    progress = db.relationship('UserProgress', backref='user', lazy=True)
    
    def set_password(self, password):
        """Set the password hash for the user"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class UserProgress(db.Model):
    """Model for tracking user quiz progress"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    question_name = db.Column(db.String(50), nullable=False)
    correct = db.Column(db.Boolean, default=False)
    answered_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProgress {self.user_id} - {self.subject}_{self.question_name}>'

class UserSession(db.Model):
    """Model for tracking user's current session"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_question_subject = db.Column(db.String(50), nullable=True)
    last_question_name = db.Column(db.String(50), nullable=True)
    correct_answers = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<UserSession {self.user_id}>'