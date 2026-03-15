import qrcode
import io
import base64
import json

def generate_qr(booking_id, user_name, facility_name, start_time, end_time):
    data = json.dumps({
        'booking_id': booking_id,
        'user': user_name,
        'facility': facility_name,
        'start': start_time,
        'end': end_time
    })
    qr = qrcode.QRCode(version=1, box_size=8, border=3)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1a3a6b', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()

def generate_qr_base64(booking_id, user_name, facility_name, start_time, end_time):
    return base64.b64encode(generate_qr(booking_id, user_name, facility_name, start_time, end_time)).decode()
