import os
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'campus-booking-secret-key')

from routes.auth    import auth_bp
from routes.booking import booking_bp
from routes.admin   import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)