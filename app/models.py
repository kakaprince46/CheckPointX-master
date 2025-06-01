from . import db
from datetime import datetime
from .config import get_fernet_cipher # For fingerprint encryption/decryption
from uuid import uuid4 # <--- ADD THIS IMPORT or ensure it's present
import os
import logging

# Get a logger for this module
model_logger = logging.getLogger(__name__)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), nullable=True, unique=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True) # unique=True will be handled by __table_args__
    email = db.Column(db.String(120), nullable=True, unique=True)
    
    # --- MODIFIED THIS LINE ---
    fallback_id = db.Column(db.String(36), default=lambda: str(uuid4()), nullable=False, unique=True)
    # --- END MODIFICATION ---
    
    _fingerprint_template_1 = db.Column("fingerprint_template_1", db.Text, nullable=True)
    _fingerprint_template_2 = db.Column("fingerprint_template_2", db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    registrations = db.relationship('Registration', backref='user', lazy='dynamic')
    check_ins = db.relationship('CheckIn', backref='user', lazy='dynamic')

    __table_args__ = (db.UniqueConstraint('phone', name='uq_user_phone'),)

    @property
    def fingerprint_template_1(self):
        cipher = get_fernet_cipher()
        if cipher and self._fingerprint_template_1:
            try:
                return cipher.decrypt(self._fingerprint_template_1.encode()).decode()
            except Exception as e: 
                model_logger.error(f"Failed to decrypt fingerprint_template_1 for user {self.id}: {e}", exc_info=False) # exc_info=False for less verbose logs on decrypt failure
                return None 
        return self._fingerprint_template_1

    @fingerprint_template_1.setter
    def fingerprint_template_1(self, plain_text_template):
        cipher = get_fernet_cipher()
        if cipher and plain_text_template:
            try:
                self._fingerprint_template_1 = cipher.encrypt(plain_text_template.encode()).decode()
            except Exception as e: 
                model_logger.error(f"Failed to encrypt fingerprint_template_1 for user (ID will be set on commit): {e}", exc_info=False)
                self._fingerprint_template_1 = None 
        elif plain_text_template:
            if os.getenv('ENCRYPTION_KEY'):
                model_logger.warning(f"Storing fingerprint_template_1 as plain text for user (ID to be set) because cipher is not available, despite ENCRYPTION_KEY being set.")
            self._fingerprint_template_1 = plain_text_template
        else:
            self._fingerprint_template_1 = None

    @property
    def fingerprint_template_2(self):
        cipher = get_fernet_cipher()
        if cipher and self._fingerprint_template_2:
            try:
                return cipher.decrypt(self._fingerprint_template_2.encode()).decode()
            except Exception as e: 
                model_logger.error(f"Failed to decrypt fingerprint_template_2 for user {self.id}: {e}", exc_info=False)
                return None
        return self._fingerprint_template_2

    @fingerprint_template_2.setter
    def fingerprint_template_2(self, plain_text_template):
        cipher = get_fernet_cipher()
        if cipher and plain_text_template:
            try:
                self._fingerprint_template_2 = cipher.encrypt(plain_text_template.encode()).decode()
            except Exception as e: 
                model_logger.error(f"Failed to encrypt fingerprint_template_2 for user (ID to be set): {e}", exc_info=False)
                self._fingerprint_template_2 = None
        elif plain_text_template:
            if os.getenv('ENCRYPTION_KEY'):
                model_logger.warning(f"Storing fingerprint_template_2 as plain text for user (ID to be set) because cipher is not available, despite ENCRYPTION_KEY being set.")
            self._fingerprint_template_2 = plain_text_template
        else:
            self._fingerprint_template_2 = None

    def __repr__(self):
        return f'<User {self.name}>'

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)

    sessions = db.relationship('Session', backref='event', lazy='dynamic')
    registrations = db.relationship('Registration', backref='event', lazy='dynamic')
    check_ins = db.relationship('CheckIn', backref='event', lazy='dynamic')

    def __repr__(self):
        return f'<Event {self.name}>'

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    check_ins = db.relationship('CheckIn', backref='session', lazy='dynamic')

    def __repr__(self):
        return f'<Session {self.name} for Event ID {self.event_id}>'

class Registration(db.Model):
    __tablename__ = 'registrations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    # is_verified = db.Column(db.Boolean, default=False, nullable=False) 

    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='uq_user_event_registration'),)

    def __repr__(self):
        return f'<Registration user_id={self.user_id} event_id={self.event_id}>'

class CheckIn(db.Model):
    __tablename__ = 'check_ins'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False) 
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    device_id = db.Column(db.String(100), nullable=True) 
    is_synced = db.Column(db.Boolean, default=False, nullable=False)
    created_at_local = db.Column(db.DateTime, nullable=True)
    method = db.Column(db.String(50), nullable=True)

    # __table_args__ = (db.UniqueConstraint('user_id', 'session_id', name='uq_user_session_checkin'),)

    def __repr__(self):
        return f'<CheckIn id={self.id} user_id={self.user_id} method={self.method}>'

class OfflineDevice(db.Model):
    __tablename__ = 'offline_devices'
    id = db.Column(db.Integer, primary_key=True)
    device_uuid = db.Column(db.String(36), unique=True, nullable=False) 
    name = db.Column(db.String(100), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<OfflineDevice {self.device_uuid}>'