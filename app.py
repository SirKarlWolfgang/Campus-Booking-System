import os
from flask import Flask, render_template
from flask_mail import Mail
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'campus-booking-secret-key-change-in-prod')

app.config['MAIL_SERVER']         = 'smtp.gmail.com'
app.config['MAIL_PORT']           = 587
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USERNAME']       = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD']       = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('BookSpace', os.getenv('MAIL_USERNAME'))
mail = Mail(app)

# ── Register blueprints ───────────────────────────────────────────────────────
from routes.auth    import auth_bp
from routes.booking import booking_bp
from routes.admin   import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(admin_bp)

# ── Frontend entry point ──────────────────────────────────────────────────────
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/app')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)