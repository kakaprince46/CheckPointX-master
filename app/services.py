from cryptography.fernet import Fernet
import os
import africastalking # Make sure this is in requirements.txt and installed
import resend         # Make sure this is in requirements.txt and installed
from datetime import datetime, timezone # Added timezone
from dotenv import load_dotenv

# Import models carefully. If services are imported by models (circular), this can be an issue.
# Usually, services use models, models don't use services.
from .models import db, User, CheckIn, Registration, Event, Session # Added Event and Session
from sqlalchemy.exc import IntegrityError

# load_dotenv() # This is good if .env is in the same directory or a parent.
# It's also loaded in config.py, so ensure consistency or load once.
# For services, it's better if they get config from the app context or passed in.
# For now, relying on os.getenv assuming .env is loaded by config.py when the app starts.

class FingerprintService:
    """Service for handling fingerprint operations"""
    def __init__(self):
        key_str = os.getenv('ENCRYPTION_KEY')
        if not key_str:
            print("CRITICAL ERROR [FingerprintService]: ENCRYPTION_KEY not found in environment variables. Service will not function correctly.")
            # In a real app, you might want to prevent app startup or have this service return a "disabled" state.
            self.cipher = None # Set cipher to None if key is missing
        else:
            try:
                self.cipher = Fernet(key_str.encode()) # Fernet key must be bytes
            except Exception as e:
                print(f"CRITICAL ERROR [FingerprintService]: Invalid ENCRYPTION_KEY. Could not initialize Fernet. Error: {e}")
                self.cipher = None

    def encrypt_template(self, template_data: str) -> str | None:
        if not self.cipher:
            print("WARNING [FingerprintService]: Encryption attempted but cipher is not initialized (ENCRYPTION_KEY missing or invalid).")
            return None # Or return template_data if you want to store unencrypted (NOT RECOMMENDED)
        if not isinstance(template_data, str):
             print(f"WARNING [FingerprintService]: template_data for encryption was not a string (type: {type(template_data)}). Will attempt to encode.")
             # Attempt to convert to string then encode, or raise error
             template_data = str(template_data)

        try:
            encrypted_data_bytes = self.cipher.encrypt(template_data.encode('utf-8'))
            return encrypted_data_bytes.decode('utf-8')
        except Exception as e:
            print(f"ERROR [FingerprintService]: Encryption failed - {e}")
            return None


    def decrypt_template(self, encrypted_template_str: str) -> str | None:
        if not self.cipher:
            print("WARNING [FingerprintService]: Decryption attempted but cipher is not initialized.")
            return None # Or return encrypted_template_str
        if not encrypted_template_str:
            return None
        try:
            decrypted_data_bytes = self.cipher.decrypt(encrypted_template_str.encode('utf-8'))
            return decrypted_data_bytes.decode('utf-8')
        except Exception as e: # Catch specific exceptions like InvalidToken from cryptography.fernet
            print(f"ERROR [FingerprintService]: Decryption failed - {e}")
            return None


    def match_templates(self, template1, template2, threshold=70):
        raise NotImplementedError("Fingerprint matching must be implemented with a specific SDK.")


class NotificationService:
    def __init__(self):
        self.at_username = os.getenv('AFRICASTALKING_USERNAME')
        self.at_api_key = os.getenv('AFRICASTALKING_API_KEY')
        self.resend_api_key = os.getenv('RESEND_API_KEY')
        self.admin_email = os.getenv('ADMIN_EMAIL')
        self.from_email = os.getenv('DEFAULT_FROM_EMAIL', "noreply@yourevent.com") # Use a default

        self.sms_service = None
        if self.at_username and self.at_api_key:
            try:
                africastalking.initialize(username=self.at_username, api_key=self.at_api_key)
                self.sms_service = africastalking.SMS
                print("INFO [NotificationService]: Africa's Talking SMS service initialized.")
            except Exception as e:
                print(f"WARNING [NotificationService]: Failed to initialize Africa's Talking SMS service: {e}")
        else:
            print("WARNING [NotificationService]: Africa's Talking credentials not fully set. SMS service disabled.")

        if self.resend_api_key:
            resend.api_key = self.resend_api_key
            print("INFO [NotificationService]: Resend email service API key set.")
        else:
            print("WARNING [NotificationService]: Resend API key not set. Email service disabled for Resend.")

    def send_checkin_notifications(self, user: User, session_obj: Session): # Type hinting for clarity
        print(f"INFO [NotificationService]: Attempting check-in notifications for user {user.id}, session {session_obj.id}")
        self.send_checkin_sms(user, session_obj)
        self.send_checkin_email(user, session_obj)
        # Assuming VIP logic is handled elsewhere or based on user property
        if getattr(user, 'is_vip', False): # Example check for a hypothetical is_vip attribute
             self.send_vip_alerts(user, session_obj)

    def send_checkin_sms(self, user: User, session_obj: Session):
        if not self.sms_service:
            print("DEBUG [NotificationService]: SMS service not available. Skipping SMS to user {user.id}.")
            return None
        if not user.phone:
            print(f"DEBUG [NotificationService]: No phone number for user {user.id}. Skipping SMS.")
            return None
        try:
            event_name = session_obj.event.name if session_obj.event else "the event"
            message = f"Hello {user.name}, your check-in for {event_name} - {session_obj.name} is confirmed. Thank you!"
            # Ensure user.phone is in the correct international format if required by Africa's Talking
            response = self.sms_service.send(message, [str(user.phone)])
            print(f"INFO [NotificationService]: SMS sent to {user.phone}. Response: {response}")
            return response
        except Exception as e:
            print(f"ERROR [NotificationService]: SMS sending failed for user {user.id}: {e}")
            return None

    def send_checkin_email(self, user: User, session_obj: Session):
        if not resend.api_key: # Check if API key was set
            print("DEBUG [NotificationService]: Resend API key not set. Skipping email to user {user.id}.")
            return None
        if not user.email:
            print(f"DEBUG [NotificationService]: No email address for user {user.id}. Skipping email.")
            return None

        try:
            event_name = session_obj.event.name if session_obj.event else "the event"
            session_name = session_obj.name
            # Querying CheckIn time here might be complex if not passed directly.
            # For simplicity, let's assume checkin_time is on session_obj or passed if needed for email content
            # Or query it:
            checkin_record = CheckIn.query.filter_by(user_id=user.id, session_id=session_obj.id).order_by(CheckIn.check_in_time.desc()).first()
            checkin_time_display = checkin_record.check_in_time.strftime('%Y-%m-%d %H:%M') if checkin_record else "recently"

            params = {
                "from": self.from_email,
                "to": [user.email],
                "subject": f"Your Check-in Confirmation for {event_name}",
                "html": f"<h1>Check-in Confirmed!</h1><p>Hello {user.name},</p><p>Your check-in to <strong>{event_name}</strong> (Session: {session_name}) at {checkin_time_display} has been confirmed.</p><p>Thank you for attending!</p>"
            }
            email_response = resend.Emails.send(params)
            print(f"INFO [NotificationService]: Email sent to {user.email}. Response: {email_response}")
            return email_response
        except Exception as e:
            print(f"ERROR [NotificationService]: Email sending failed for user {user.id}: {e}")
            return None

    def send_vip_alerts(self, user: User, session_obj: Session):
        if not resend.api_key:
            print("DEBUG [NotificationService]: Resend API key not set for VIP alert. Skipping.")
            return None
        if not self.admin_email:
            print("DEBUG [NotificationService]: ADMIN_EMAIL not set for VIP alert. Skipping.")
            return None
        
        # Example: Add a check for VIP status if you have such a field in your User model
        # if not getattr(user, 'is_vip', False):
        #     return None

        try:
            event_name = session_obj.event.name if session_obj.event else "the event"
            session_name = session_obj.name
            checkin_record = CheckIn.query.filter_by(user_id=user.id, session_id=session_obj.id).order_by(CheckIn.check_in_time.desc()).first()
            checkin_time_display = checkin_record.check_in_time.strftime('%Y-%m-%d %H:%M UTC') if checkin_record else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

            params = {
                "from": self.from_email,
                "to": [self.admin_email],
                "subject": f"VIP Check-in Alert: {user.name} for {event_name}",
                "html": f"<h1>VIP Attendee Checked In</h1><p><strong>Name:</strong> {user.name}</p><p><strong>Phone:</strong> {user.phone}</p><p><strong>Email:</strong> {user.email or 'N/A'}</p><p><strong>Event:</strong> {event_name}</p><p><strong>Session:</strong> {session_name}</p><p><strong>Check-in Time:</strong> {checkin_time_display}</p>"
            }
            alert_response = resend.Emails.send(params)
            print(f"INFO [NotificationService]: VIP Alert for {user.name} sent to {self.admin_email}. Response: {alert_response}")
            return alert_response
        except Exception as e:
            print(f"ERROR [NotificationService]: VIP alert email failed for user {user.id}: {e}")
            return None


class SyncService:
    """Service for handling offline sync operations"""
    def __init__(self):
        # Initialize FingerprintService here or ensure it's passed if needed by its methods
        try:
            self.fingerprint_service = FingerprintService()
        except ValueError as e: # Handles missing ENCRYPTION_KEY
            print(f"WARNING [SyncService]: Could not initialize internal FingerprintService: {e}. Fingerprint operations in sync will be affected.")
            self.fingerprint_service = None
        except Exception as e_fp_sync:
            print(f"ERROR [SyncService]: Unexpected error initializing internal FingerprintService: {e_fp_sync}")
            self.fingerprint_service = None


    def process_sync_data(self, device_id, sync_data_payload):
        # The detailed logic for this is currently in your routes.py /sync endpoint.
        # This service method could be called by that route, or the route could
        # use more granular methods from this service if you break down the sync logic.
        # For now, as per your routes.py, this service isn't directly orchestrating the whole sync.
        print(f"INFO [SyncService]: process_sync_data called for device_id: {device_id}. Payload (first 200 chars): {str(sync_data_payload)[:200]}")
        # Example of how you might call helper methods if you refactor /sync route's logic here:
        # new_users_feedback = []
        # for reg_data in sync_data_payload.get('new_registrations', []):
        #     user, reg = self._process_synced_registration(reg_data)
        #     if user:
        #         new_users_feedback.append({'local_id': reg_data.get('local_id'), 'server_id': user.id, 'fallback_id': user.fallback_id})
        #
        # synced_checkins_feedback = []
        # for checkin_data in sync_data_payload.get('check_ins', []):
        #     checkin_obj = self._process_synced_checkin(device_id, checkin_data, new_users_feedback) # Pass mapping if needed
        #     if checkin_obj:
        #          synced_checkins_feedback.append({'local_id': checkin_data.get('local_id'), 'server_id': checkin_obj.id, 'status': 'synced'})
        #
        # # db.session.commit() would happen here after all operations
        # return {'new_users_feedback': new_users_feedback, 'synced_checkins_feedback': synced_checkin_responses}
        raise NotImplementedError("Detailed sync processing logic currently resides in routes.py/sync. Refactor here if desired.")

    # Example helper methods (you would move logic from routes.py/sync here)
    def _process_synced_registration(self, user_data):
        # ... (logic to find or create user, create registration)
        # Make sure to handle db.session.add() but commit in the main process_sync_data
        # or handle transactions carefully.
        # This should use self.fingerprint_service if available and needed.
        pass

    def _process_synced_checkin(self, device_id, checkin_data, new_user_mapping=None):
        # ... (logic to find user (using mapping if needed), event, session, create checkin)
        pass