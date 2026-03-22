import threading
import logging
from flask_mail import Message

logger = logging.getLogger(__name__)

def send_async_email(app, subject, recipient, body):
    try:
        with app.app_context():
            from app import mail
            msg = Message(subject=subject, recipients=[recipient], body=body)
            mail.send(msg)
            logger.info(f"Email sent to {recipient}")
            print(f"EMAIL SENT to {recipient}")
    except Exception as e:
        logger.error(f"Email failed: {e}")
        print(f"EMAIL FAILED: {e}")

def send_email(subject, recipient, body):
    from app import app
    thread = threading.Thread(target=send_async_email, args=(app, subject, recipient, body))
    thread.daemon = False
    thread.start()

def send_booking_confirmation(user_email, user_name, facility_name, start_time, end_time, booking_id):
    subject = "BookSpace - Booking Confirmation"
    body = f"Hi {user_name},\n\nYour booking for {facility_name} from {start_time} to {end_time} has been received and is pending approval.\n\nBooking ID: {booking_id}\n\nThank you,\nBookSpace Team"
    send_email(subject, user_email, body)

def send_booking_status(user_email, user_name, facility_name, start_time, end_time, status):
    subject = f"BookSpace - Booking {status.capitalize()}"
    body = f"Hi {user_name},\n\nYour booking for {facility_name} from {start_time} to {end_time} has been {status}.\n\nThank you,\nBookSpace Team"
    send_email(subject, user_email, body)
