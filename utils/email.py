import threading
from flask_mail import Message

def send_async_email(app, subject, recipient, body):
    with app.app_context():
        from app import mail
        msg = Message(subject=subject, recipients=[recipient], body=body)
        mail.send(msg)

def send_email(subject, recipient, body):
    from app import app
    thread = threading.Thread(target=send_async_email, args=(app, subject, recipient, body))
    thread.daemon = True
    thread.start()

def send_booking_confirmation(user_email, user_name, facility_name, start_time, end_time, booking_id):
    subject = "BookSpace - Booking Confirmation"
    body = f"Hi {user_name},\n\nYour booking for {facility_name} from {start_time} to {end_time} has been received and is pending approval.\n\nBooking ID: {booking_id}\n\nThank you,\nBookSpace Team"
    send_email(subject, user_email, body)

def send_booking_status(user_email, user_name, facility_name, start_time, end_time, status):
    subject = f"BookSpace - Booking {status.capitalize()}"
    body = f"Hi {user_name},\n\nYour booking for {facility_name} from {start_time} to {end_time} has been {status}.\n\nThank you,\nBookSpace Team"
    send_email(subject, user_email, body)
