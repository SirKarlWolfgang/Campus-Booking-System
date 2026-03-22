import threading
import requests

BREVO_API_KEY = None

def get_api_key():
    import os
    return os.getenv('BREVO_API_KEY')

def send_async_email(subject, recipient, body):
    try:
        api_key = get_api_key()
        response = requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'api-key': api_key,
                'Content-Type': 'application/json'
            },
            json={
                'sender': {'name': 'BookSpace', 'email': 'fakeemailforagroupproject26@gmail.com'},
                'to': [{'email': recipient}],
                'subject': subject,
                'textContent': body
            }
        )
        print(f"EMAIL RESULT: {response.status_code} - {response.text}", flush=True)
    except Exception as e:
        print(f"EMAIL FAILED: {e}", flush=True)

def send_email(subject, recipient, body):
    thread = threading.Thread(target=send_async_email, args=(subject, recipient, body))
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
