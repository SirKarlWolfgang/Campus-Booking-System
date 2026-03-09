from flask import Blueprint, request, jsonify, session
from sqlalchemy.orm import Session
from database import engine
from models.models import User, UserRole
import bcrypt

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/register', methods=['POST'])
def register():
    data     = request.get_json()
    name     = data.get('name', '').strip()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    with Session(engine) as db:
        if db.query(User).filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(username=name, email=email, password_hash=hashed, role=UserRole.student)
        db.add(user)
        db.commit()
        db.refresh(user)

        session['user_id']   = user.user_id
        session['user_role'] = user.role.value

        return jsonify({
            'message': 'Account created successfully',
            'user': {'id': user.user_id, 'name': user.username, 'email': user.email, 'role': user.role.value}
        }), 201


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    with Session(engine) as db:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401

        try:
            pw_ok = bcrypt.checkpw(password.encode(), user.password_hash.encode())
        except Exception:
            pw_ok = (password == user.password_hash)

        if not pw_ok:
            return jsonify({'error': 'Invalid email or password'}), 401

        session['user_id']   = user.user_id
        session['user_role'] = user.role.value

        return jsonify({
            'message': 'Login successful',
            'user': {'id': user.user_id, 'name': user.username, 'email': user.email, 'role': user.role.value}
        }), 200


@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/api/me', methods=['GET'])
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    with Session(engine) as db:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            session.clear()
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'user': {'id': user.user_id, 'name': user.username, 'email': user.email, 'role': user.role.value}
        }), 200