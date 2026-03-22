import os
from flask import Flask, render_template
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'campus-booking-secret-key-change-in-prod')


# ── Register blueprints ───────────────────────────────────────────────────────
from routes.auth    import auth_bp
from routes.booking import booking_bp
from routes.admin   import admin_bp
from routes.ai_booking import ai_bp

app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(ai_bp)

# ── Frontend entry point ──────────────────────────────────────────────────────
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/app')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)