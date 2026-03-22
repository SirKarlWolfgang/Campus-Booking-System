import threading
from flask_mail import Message
from flask import current_app

def send_async_email(app, msg, mail):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipient, body, html_body=None):
    from app import app, mail
    msg = Message(subject=subject, recipients=[recipient], body=body, html=html_body)
    thread = threading.Thread(target=send_async_email, args=(app, msg, mail))
    thread.start()
