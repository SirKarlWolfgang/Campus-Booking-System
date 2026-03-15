from flask_mail import Message
from app import mail
from utils.qr import generate_qr

def send_booking_confirmation(to_email, user_name, facility_name, start_time, end_time, booking_id):
    msg = Message(subject="BookSpace - Booking Received", recipients=[to_email])
    msg.html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;color:#1a1a18">
      <div style="background:#1a3a6b;padding:24px 32px">
        <h2 style="color:#fff;margin:0">BookSpace</h2>
        <p style="color:#c8e6ff;margin:4px 0 0;font-size:13px">Durban University of Technology</p>
      </div>
      <div style="padding:32px;border:1px solid #ddd9d0;border-top:none">
        <p>Hi <strong>{user_name}</strong>,</p>
        <p style="color:#555;font-size:14px">Your booking request has been received and is pending admin approval.</p>
        <div style="background:#f5f2ec;border:1px solid #ddd9d0;padding:20px;margin:24px 0;font-size:13px">
          <p><span style="color:#8a8680">Facility:</span> <strong>{facility_name}</strong></p>
          <p><span style="color:#8a8680">Date:</span> <strong>{start_time.split(' ')[0]}</strong></p>
          <p><span style="color:#8a8680">Time:</span> <strong>{start_time.split(' ')[1]} to {end_time}</strong></p>
          <p><span style="color:#8a8680">Booking ID:</span> <strong>#{booking_id}</strong></p>
        </div>
        <p style="font-size:13px;color:#8a8680">You will receive another email once your booking is approved or rejected.</p>
      </div>
      <div style="padding:16px 32px;background:#f5f2ec;border:1px solid #ddd9d0;border-top:none;font-size:11px;color:#8a8680">
        BookSpace - Campus Facility Booking System | DUT
      </div>
    </div>"""
    mail.send(msg)

def send_booking_status(to_email, user_name, facility_name, start_time, status, booking_id, end_time=''):
    colour  = "#2d6a4f" if status == "approved" else "#9b2335"
    label   = "Approved" if status == "approved" else "Rejected"
    message = "Your booking has been approved. Please arrive on time." if status == "approved" \
              else "Unfortunately your booking has been rejected. You may submit a new request."
    msg = Message(subject=f"BookSpace - Booking {label}", recipients=[to_email])
    if status == 'approved':
        qr_bytes = generate_qr(booking_id, user_name, facility_name, start_time, end_time)
        msg.attach('booking_qr.png', 'image/png', qr_bytes)
    msg.html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;color:#1a1a18">
      <div style="background:#1a3a6b;padding:24px 32px">
        <h2 style="color:#fff;margin:0">BookSpace</h2>
        <p style="color:#c8e6ff;margin:4px 0 0;font-size:13px">Durban University of Technology</p>
      </div>
      <div style="padding:32px;border:1px solid #ddd9d0;border-top:none">
        <p>Hi <strong>{user_name}</strong>,</p>
        <div style="background:{colour};color:#fff;padding:12px 20px;margin-bottom:24px;font-size:15px;font-weight:bold">
          Booking {label}
        </div>
        <p style="color:#555;font-size:14px">{message}</p>
        <div style="background:#f5f2ec;border:1px solid #ddd9d0;padding:20px;margin:24px 0;font-size:13px">
          <p><span style="color:#8a8680">Facility:</span> <strong>{facility_name}</strong></p>
          <p><span style="color:#8a8680">Date:</span> <strong>{start_time.split(' ')[0]}</strong></p>
          <p><span style="color:#8a8680">Booking ID:</span> <strong>#{booking_id}</strong></p>
        </div>
      </div>
      <div style="padding:16px 32px;background:#f5f2ec;border:1px solid #ddd9d0;border-top:none;font-size:11px;color:#8a8680">
        BookSpace - Campus Facility Booking System | DUT
      </div>
    </div>"""
    mail.send(msg)
