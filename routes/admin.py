from utils.email import send_booking_status
from flask import Blueprint, request, jsonify, session
from sqlalchemy.orm import Session
from database import engine
from models.models import User, Facility, Booking, BookingStatus, UserRole
import bcrypt

admin_bp = Blueprint('admin', __name__)


def require_admin():
    return session.get('user_role') == 'admin'


# ── Dashboard stats ───────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    with Session(engine) as db:
        return jsonify({
            'total_users':      db.query(User).count(),
            'total_facilities': db.query(Facility).count(),
            'total_bookings':   db.query(Booking).count(),
            'pending_bookings': db.query(Booking).filter_by(status=BookingStatus.pending).count(),
        }), 200


# ── Manage bookings ───────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/bookings', methods=['GET'])
def all_bookings():
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    status_filter = request.args.get('status')

    with Session(engine) as db:
        query = db.query(Booking)
        if status_filter:
            try:
                query = query.filter_by(status=BookingStatus[status_filter])
            except KeyError:
                return jsonify({'error': 'Invalid status'}), 400

        bookings = query.order_by(Booking.created_at.desc()).all()

        result = []
        for b in bookings:
            user     = db.query(User).filter_by(user_id=b.user_id).first()
            facility = db.query(Facility).filter_by(facility_id=b.facility_id).first()
            result.append({
                'booking_id':    b.booking_id,
                'user_id':       b.user_id,
                'user_name':     user.username    if user     else 'Unknown',
                'user_email':    user.email       if user     else '',
                'facility_id':   b.facility_id,
                'facility_name': facility.name    if facility else 'Unknown',
                'start_time':    b.start_time.strftime('%Y-%m-%d %H:%M'),
                'created_at':    b.created_at.strftime('%Y-%m-%d %H:%M') if b.created_at else '',
                'end_time':      b.end_time.strftime('%H:%M'),
                'status':        b.status.value,
                'purpose':       b.purpose or '',
            })

        return jsonify(result), 200


@admin_bp.route('/api/admin/bookings/<int:booking_id>/approve', methods=['POST'])
def approve_booking(booking_id):
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    with Session(engine) as db:
        booking = db.query(Booking).filter_by(booking_id=booking_id).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        booking.status      = BookingStatus.approved
        booking.approved_by = session.get('user_id')
        db.commit()
        user     = db.query(User).filter_by(user_id=booking.user_id).first()
        facility = db.query(Facility).filter_by(facility_id=booking.facility_id).first()
        try:
            send_booking_status(user.email, user.username, facility.name,
                booking.start_time.strftime('%Y-%m-%d %H:%M'), 'approved', booking.booking_id,
                booking.end_time.strftime('%H:%M'))
        except Exception:
            pass
        return jsonify({'message': 'Booking approved'}), 200


@admin_bp.route('/api/admin/bookings/<int:booking_id>/reject', methods=['POST'])
def reject_booking(booking_id):
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    with Session(engine) as db:
        booking = db.query(Booking).filter_by(booking_id=booking_id).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        booking.status = BookingStatus.rejected
        db.commit()
        user     = db.query(User).filter_by(user_id=booking.user_id).first()
        facility = db.query(Facility).filter_by(facility_id=booking.facility_id).first()
        try:
            send_booking_status(user.email, user.username, facility.name,
                booking.start_time.strftime('%Y-%m-%d %H:%M'), 'rejected', booking.booking_id)
        except Exception:
            pass
        return jsonify({'message': 'Booking rejected'}), 200


# ── Manage facilities ─────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/facilities', methods=['GET'])
def list_all_facilities():
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    with Session(engine) as db:
        facilities = db.query(Facility).all()
        return jsonify([{
            'id':          f.facility_id,
            'name':        f.name,
            'type':        f.type,
            'capacity':    f.capacity,
            'description': f.description,
            'is_active':   f.is_active,
        } for f in facilities]), 200


@admin_bp.route('/api/admin/facilities', methods=['POST'])
def add_facility():
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    data        = request.get_json()
    name        = data.get('name', '').strip()
    ftype       = data.get('type', '').strip()
    capacity    = data.get('capacity', 0)
    description = data.get('description', '').strip()
    is_active   = data.get('is_active', True)

    if not name:
        return jsonify({'error': 'name is required'}), 400

    with Session(engine) as db:
        facility = Facility(name=name, type=ftype, capacity=capacity,
                            description=description, is_active=is_active)
        db.add(facility)
        db.commit()
        db.refresh(facility)
        return jsonify({'message': 'Facility added', 'id': facility.facility_id}), 201


@admin_bp.route('/api/admin/facilities/<int:facility_id>', methods=['PUT'])
def update_facility(facility_id):
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    with Session(engine) as db:
        facility = db.query(Facility).filter_by(facility_id=facility_id).first()
        if not facility:
            return jsonify({'error': 'Facility not found'}), 404

        if 'name'        in data: facility.name        = data['name']
        if 'type'        in data: facility.type        = data['type']
        if 'capacity'    in data: facility.capacity    = data['capacity']
        if 'description' in data: facility.description = data['description']
        if 'is_active'   in data: facility.is_active   = data['is_active']

        db.commit()
        return jsonify({'message': 'Facility updated'}), 200


@admin_bp.route('/api/admin/facilities/<int:facility_id>', methods=['DELETE'])
def delete_facility(facility_id):
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    with Session(engine) as db:
        facility = db.query(Facility).filter_by(facility_id=facility_id).first()
        if not facility:
            return jsonify({'error': 'Facility not found'}), 404
        db.delete(facility)
        db.commit()
        return jsonify({'message': 'Facility deleted'}), 200


# ── Manage users ──────────────────────────────────────────────────────────────

@admin_bp.route('/api/admin/users', methods=['GET'])
def list_users():
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    with Session(engine) as db:
        users = db.query(User).all()
        return jsonify([{
            'id':    u.user_id,
            'name':  u.username,
            'email': u.email,
            'role':  u.role.value,
        } for u in users]), 200


@admin_bp.route('/api/admin/users', methods=['POST'])
def create_user():
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    with Session(engine) as db:
        if db.query(User).filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered.'}), 400
        hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
        role   = UserRole.admin if data.get('role') == 'admin' else UserRole.student
        user   = User(username=data['username'], email=data['email'],
                      password_hash=hashed, role=role)
        db.add(user)
        db.commit()
        return jsonify({'message': 'User created.'}), 201


@admin_bp.route('/api/admin/users/<int:uid>', methods=['PUT'])
def update_user(uid):
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()

    with Session(engine) as db:
        user = db.query(User).filter_by(user_id=uid).first()
        if not user:
            return jsonify({'error': 'User not found.'}), 404
        if 'username' in data: user.username = data['username']
        if 'email'    in data: user.email    = data['email']
        if 'role'     in data:
            user.role = UserRole.admin if data['role'] == 'admin' else UserRole.student
        if data.get('password'):
            user.password_hash = bcrypt.hashpw(
                data['password'].encode(), bcrypt.gensalt()).decode()
        db.commit()
        return jsonify({'message': 'User updated.'}), 200


@admin_bp.route('/api/admin/users/<int:uid>', methods=['DELETE'])
def delete_user(uid):
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403

    with Session(engine) as db:
        user = db.query(User).filter_by(user_id=uid).first()
        if not user:
            return jsonify({'error': 'User not found.'}), 404
        db.delete(user)
        db.commit()
        return jsonify({'message': 'User deleted.'}), 200