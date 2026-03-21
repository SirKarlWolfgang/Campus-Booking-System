from flask import Blueprint, request, jsonify, session
from sqlalchemy.orm import Session
from database import engine
from models.models import Facility, Booking, BookingStatus, User
from datetime import datetime, timedelta
from groq import Groq
import os
import json

ai_bp = Blueprint('ai_booking', __name__)

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def require_login():
    return session.get('user_id')

@ai_bp.route('/api/ai/parse-booking', methods=['POST'])
def parse_booking():
    user_id = require_login()
    if not user_id:
        return jsonify({'error': 'Login required'}), 401

    text = request.get_json().get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    today = datetime.now().strftime('%Y-%m-%d')
    day_of_week = datetime.now().strftime('%A')

    prompt = f"""You are a booking assistant for a university campus facility booking system.
Today is {day_of_week}, {today}.

The user wants to make a booking. Parse their request and return ONLY a JSON object with these fields:
- facility_type: one of "lab", "hall", "room", "sports", or null if unclear
- date: in YYYY-MM-DD format, or null if unclear
- start_time: in HH:MM 24hr format (must be one of: 08:00, 09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00, 17:00, 18:00, 19:00), or null
- duration: number of hours (1-4, or 3 max if start is 19:00), or null
- capacity: minimum number of people needed, or 1 if not mentioned
- notes: any special requirements mentioned, or null

Time references:
- "morning" = 08:00-12:00, pick 09:00 as default
- "afternoon" = 12:00-17:00, pick 13:00 as default
- "evening" = 17:00-19:00, pick 17:00 as default
- "tomorrow" = {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
- "next Monday/Tuesday/etc" = calculate from today

User request: "{text}"

Return ONLY valid JSON, no explanation."""

    try:
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role':'user','content':prompt}],
            temperature=0.1
        )
        raw = response.choices[0].message.content.strip().replace('```json','').replace('```','').strip()
        parsed = json.loads(raw)
    except Exception as e:
        return jsonify({'error': f'Could not parse request: {str(e)}'}), 500

    if not parsed.get('date') or not parsed.get('start_time'):
        return jsonify({'error': 'Could not determine date or time from your request. Please be more specific.'}), 400

    try:
        start_dt = datetime.strptime(f"{parsed['date']} {parsed['start_time']}", '%Y-%m-%d %H:%M')
        duration = int(parsed.get('duration') or 1)
        end_dt   = start_dt + timedelta(hours=duration)
    except:
        return jsonify({'error': 'Invalid date or time parsed.'}), 400

    capacity = int(parsed.get('capacity') or 1)
    ftype    = parsed.get('facility_type')

    with Session(engine) as db:
        user = db.query(User).filter_by(user_id=user_id).first()
        user_role = user.role.value

        query = db.query(Facility).filter_by(is_active=True).filter(Facility.capacity >= capacity)
        if ftype:
            query = query.filter(Facility.type.ilike(f'%{ftype}%'))

        facilities = query.all()

        if user_role != 'admin':
            filtered = []
            for f in facilities:
                if not f.allowed_roles:
                    filtered.append(f)
                    continue
                allowed = [r.strip() for r in f.allowed_roles.split(',')]
                if user_role in allowed:
                    filtered.append(f)
            facilities = filtered

        available = []
        for f in facilities:
            conflict = db.query(Booking).filter(
                Booking.facility_id == f.facility_id,
                Booking.status.in_([BookingStatus.approved, BookingStatus.checked_in]),
                Booking.start_time < end_dt,
                Booking.end_time   > start_dt,
            ).first()
            if not conflict:
                available.append(f)

        available.sort(key=lambda f: abs(f.capacity - capacity))

        if not available:
            return jsonify({'error': f'No available facilities found for your request on {parsed["date"]} at {parsed["start_time"]}.'}), 404

        best = available[0]
        return jsonify({
            'facility_id':   best.facility_id,
            'facility_name': best.name,
            'facility_type': best.type,
            'capacity':      best.capacity,
            'image_url':     best.image_url or '',
            'date':          parsed['date'],
            'start_time':    parsed['start_time'],
            'end_time':      end_dt.strftime('%H:%M'),
            'duration':      duration,
            'parsed_text':   text,
            'alternatives':  [{
                'facility_id':   f.facility_id,
                'facility_name': f.name,
                'capacity':      f.capacity,
            } for f in available[1:4]]
        }), 200
