from flask import Blueprint, request, jsonify, session
from sqlalchemy.orm import Session
from database import engine
from models.models import Facility, Booking, BookingStatus, User
from datetime import datetime
from utils.email import send_booking_confirmation
import threading

booking_bp = Blueprint('booking', __name__)


def require_login():
    return session.get('user_id')


# ── Facilities ────────────────────────────────────────────────────────────────

@booking_bp.route('/api/facilities', methods=['GET'])
def get_facilities():
    user_id = require_login()
    if not user_id:
        return jsonify({'error': 'Login required'}), 401
    with Session(engine) as db:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        user_role = user.role.value
        facilities = db.query(Facility).filter_by(is_active=True).all()
        if user_role == 'admin':
            filtered = facilities
        else:
            filtered = []
            for f in facilities:
                if not f.allowed_roles:
                    filtered.append(f)
                    continue
                allowed = [r.strip() for r in f.allowed_roles.split(',')]
                if user_role in allowed:
                    filtered.append(f)
        return jsonify([{
            'id':          f.facility_id,
            'name':        f.name,
            'type':        f.type,
            'capacity':    f.capacity,
            'description': f.description,
            'image_url':   f.image_url or '',
        } for f in filtered]), 200



@booking_bp.route('/api/facilities/search', methods=['GET'])
def search_facilities():
    user_id = require_login()
    if not user_id:
        return jsonify({'error': 'Login required'}), 401
    date_str  = request.args.get('date')
    time_from = request.args.get('from')
    time_to   = request.args.get('to')
    capacity  = request.args.get('capacity', 1, type=int)
    if not date_str:
        return jsonify({'error': 'date required'}), 400
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    import datetime as dt
    if time_from and time_to:
        try:
            start_time = datetime.combine(date, dt.time.fromisoformat(time_from))
            end_time   = datetime.combine(date, dt.time.fromisoformat(time_to))
        except ValueError:
            return jsonify({'error': 'Invalid time format'}), 400
    else:
        start_time = datetime.combine(date, dt.time.min)
        end_time   = datetime.combine(date, dt.time.max)
    with Session(engine) as db:
        user = db.query(User).filter_by(user_id=user_id).first()
        user_role = user.role.value
        all_facilities = db.query(Facility).filter_by(is_active=True).filter(Facility.capacity >= capacity).all()
        if user_role == 'admin':
            facilities = all_facilities
        else:
            facilities = []
            for f in all_facilities:
                if not f.allowed_roles:
                    facilities.append(f)
                    continue
                allowed = [r.strip() for r in f.allowed_roles.split(',')]
                if user_role in allowed:
                    facilities.append(f)
        booked_ids = set()
        for f in facilities:
            conflict = db.query(Booking).filter(
                Booking.facility_id == f.facility_id,
                Booking.status.in_([BookingStatus.approved, BookingStatus.checked_in]),
                Booking.start_time < end_time,
                Booking.end_time   > start_time,
            ).first()
            if conflict:
                booked_ids.add(f.facility_id)
        available = [f for f in facilities if f.facility_id not in booked_ids]
        available.sort(key=lambda f: f.capacity - capacity)
        return jsonify([{
            'id':          f.facility_id,
            'name':        f.name,
            'type':        f.type,
            'capacity':    f.capacity,
            'description': f.description,
            'image_url':   f.image_url or '',
        } for f in available]), 200

@booking_bp.route('/api/facilities/<int:facility_id>', methods=['GET'])
def get_facility(facility_id):
    with Session(engine) as db:
        f = db.query(Facility).filter_by(facility_id=facility_id).first()
        if not f:
            return jsonify({'error': 'Facility not found'}), 404
        return jsonify({
            'id':          f.facility_id,
            'name':        f.name,
            'type':        f.type,
            'capacity':    f.capacity,
            'description': f.description,
            'image_url':   f.image_url or '',
            'is_active':   f.is_active,
            'image_url':   f.image_url or '',
        }), 200


# ── Bookings ──────────────────────────────────────────────────────────────────

@booking_bp.route('/api/bookings', methods=['GET'])
def get_my_bookings():
    user_id = require_login()
    if not user_id:
        return jsonify({'error': 'Login required'}), 401

    with Session(engine) as db:
        bookings = (
            db.query(Booking)
            .filter_by(user_id=user_id)
            .order_by(Booking.start_time.desc())
            .all()
        )
        return jsonify([_serialize_booking(b, db) for b in bookings]), 200


@booking_bp.route('/api/bookings', methods=['POST'])
def create_booking():
    user_id = require_login()
    if not user_id:
        return jsonify({'error': 'Login required'}), 401

    data        = request.get_json()
    facility_id = data.get('facility_id')
    start_str   = data.get('start_time')   # "YYYY-MM-DDTHH:MM" or "YYYY-MM-DD HH:MM"
    end_str     = data.get('end_time')
    purpose     = data.get('purpose', '')

    if not all([facility_id, start_str, end_str]):
        return jsonify({'error': 'facility_id, start_time and end_time are required'}), 400

    try:
        start_time = datetime.fromisoformat(start_str)
        end_time   = datetime.fromisoformat(end_str)
    except ValueError:
        return jsonify({'error': 'Invalid datetime format. Use YYYY-MM-DDTHH:MM'}), 400

    if end_time <= start_time:
        return jsonify({'error': 'End time must be after start time'}), 400

    if start_time < datetime.now():
        return jsonify({'error': 'Cannot book a time in the past'}), 400

    with Session(engine) as db:
        facility = db.query(Facility).filter_by(facility_id=facility_id, is_active=True).first()
        if not facility:
            return jsonify({'error': 'Facility not found or unavailable'}), 404

        user = db.query(User).filter_by(user_id=user_id).first()
        if facility.allowed_roles:
            allowed = [r.strip() for r in facility.allowed_roles.split(',')]
            if user.role.value not in allowed and user.role.value != 'admin':
                return jsonify({'error': 'You are not allowed to book this facility'}), 403

        try:
            booking = Booking(
                user_id     = user_id,
                facility_id = facility_id,
                start_time  = start_time,
                end_time    = end_time,
                status      = BookingStatus.pending,
                purpose     = purpose,
            )
            db.add(booking)
            db.commit()
            db.refresh(booking)
            user = db.query(User).filter_by(user_id=user_id).first()
            try:
                threading.Thread(target=send_booking_confirmation, args=(
                    user.email, user.username, facility.name,
                    booking.start_time.strftime("%Y-%m-%d %H:%M"),
                    booking.end_time.strftime("%H:%M"),
                    booking.booking_id
                ), daemon=True).start()
            except Exception as e:
                print('Mail error:', e)
        except ValueError as e:
            return jsonify({'error': str(e)}), 409

        return jsonify({
            'message': 'Booking submitted successfully',
            'booking': _serialize_booking(booking, db),
        }), 201


@booking_bp.route('/api/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel_booking(booking_id):
    user_id = require_login()
    if not user_id:
        return jsonify({'error': 'Login required'}), 401

    with Session(engine) as db:
        booking = db.query(Booking).filter_by(booking_id=booking_id, user_id=user_id).first()
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        if booking.status == BookingStatus.rejected:
            return jsonify({'error': 'Booking already cancelled'}), 400

        booking.status = BookingStatus.rejected
        db.commit()
        return jsonify({'message': 'Booking cancelled'}), 200


# ── Availability ──────────────────────────────────────────────────────────────

@booking_bp.route('/api/facilities/<int:facility_id>/availability', methods=['GET'])
def check_availability(facility_id):
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'date query param required (YYYY-MM-DD)'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    with Session(engine) as db:
        bookings = db.query(Booking).filter(
            Booking.facility_id == facility_id,
            Booking.status.in_([BookingStatus.approved, BookingStatus.checked_in]),
        ).all()

        day_bookings = [b for b in bookings if b.start_time.date() == date]

        booked_slots = [{
            'start_time': b.start_time.strftime('%H:%M'),
            'end_time':   b.end_time.strftime('%H:%M'),
            'status':     b.status.value,
        } for b in day_bookings]

        return jsonify({'date': date_str, 'booked_slots': booked_slots}), 200


# ── Helper ────────────────────────────────────────────────────────────────────

def _serialize_booking(booking, db):
    facility = db.query(Facility).filter_by(facility_id=booking.facility_id).first()
    return {
        'id':            booking.booking_id,
        'facility_id':   booking.facility_id,
        'facility_name': facility.name if facility else 'Unknown',
        'start_time':    booking.start_time.strftime('%Y-%m-%d %H:%M'),
        'end_time':      booking.end_time.strftime('%H:%M'),
        'status':        booking.status.value,
        'purpose':       booking.purpose or '',
    }