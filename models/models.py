from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, Text, ForeignKey, CheckConstraint, Index, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
import enum

Base = declarative_base()

# ----- Enums for role and status -----
class UserRole(enum.Enum):
    student = "student"
    staff   = "staff"
    admin   = "admin"
    guest   = "guest"

class BookingStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    checked_in = "checked_in"
    cancelled  = "cancelled"

# ----- User Model -----
class User(Base):
    __tablename__ = 'user'

    user_id = Column("UserID", Integer, primary_key=True, autoincrement=True)
    username = Column("UserName", String(100), nullable=False)
    email = Column("Email", String(100), nullable=False, unique=True)
    password_hash = Column("PasswordHash", String(255), nullable=False)
    role = Column("Role", Enum(UserRole), nullable=False)

    bookings = relationship("Booking", foreign_keys="Booking.user_id", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    approved_bookings = relationship("Booking", foreign_keys="Booking.approved_by", back_populates="approver")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role.value}')>"

# ----- Facility Model -----
class Facility(Base):
    __tablename__ = 'facility'

    facility_id = Column("FacilityID", Integer, primary_key=True, autoincrement=True)
    name = Column("Name", String(100), nullable=False)
    type = Column("Type", String(50))
    capacity = Column("Capacity", Integer)
    description = Column("Description", Text)
    image_url     = Column("ImageUrl", String(500), nullable=True)
    allowed_roles = Column("AllowedRoles", String(100), nullable=True)
    is_active     = Column("IsActive", Boolean, default=True)

    bookings = relationship("Booking", back_populates="facility", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Facility(name='{self.name}', type='{self.type}')>"

# ----- Booking Model -----
class Booking(Base):
    __tablename__ = 'booking'
    __table_args__ = (
        CheckConstraint('StartTime < EndTime', name='chk_booking_time'),
        Index('idx_booking_facility_time', 'FacilityID', 'StartTime', 'EndTime'),
    )

    booking_id = Column("BookingID", Integer, primary_key=True, autoincrement=True)
    facility_id = Column("FacilityID", Integer, ForeignKey('facility.FacilityID', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    user_id = Column("UserID", Integer, ForeignKey('user.UserID', ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    start_time = Column("StartTime", DateTime, nullable=False)
    end_time = Column("EndTime", DateTime, nullable=False)
    status = Column("Status", Enum(BookingStatus), default=BookingStatus.pending)
    purpose = Column("Purpose", Text)
    created_at = Column("CreatedAt", DateTime, server_default=func.now())
    checked_in_at = Column("CheckedInAt", DateTime, nullable=True)
    approved_by = Column("ApprovedBy", Integer, ForeignKey('user.UserID', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)

    facility = relationship("Facility", back_populates="bookings")
    user = relationship("User", foreign_keys=[user_id], back_populates="bookings")
    approver = relationship("User", foreign_keys=[approved_by], back_populates="approved_bookings")
    notifications = relationship("Notification", back_populates="booking", cascade="all, delete-orphan")

    @validates('start_time', 'end_time')
    def validate_times(self, key, value):
        if key == 'end_time' and hasattr(self, 'start_time') and self.start_time:
            if value <= self.start_time:
                raise ValueError("End time must be after start time")
        return value

    def __repr__(self):
        return f"<Booking(id={self.booking_id}, facility={self.facility_id}, user={self.user_id}, start={self.start_time})>"

# ----- Notification Model -----
class Notification(Base):
    __tablename__ = 'notification'
    __table_args__ = (
        Index('idx_notification_user_read', 'UserID', 'IsRead'),
    )

    notification_id = Column("NotificationID", Integer, primary_key=True, autoincrement=True)
    user_id = Column("UserID", Integer, ForeignKey('user.UserID', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    booking_id = Column("BookingID", Integer, ForeignKey('booking.BookingID', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    message = Column("Message", Text, nullable=False)
    sent_date_time = Column("SentDateTime", DateTime, server_default=func.now())
    channel = Column("Channel", String(20))
    is_read = Column("IsRead", Boolean, default=False)

    user = relationship("User", back_populates="notifications")
    booking = relationship("Booking", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(user={self.user_id}, read={self.is_read})>"

# ----- Event Listener for Overlap Detection -----
@event.listens_for(Booking, 'before_insert')
def check_booking_overlap(mapper, connection, target):
    from sqlalchemy.orm import Session
    session = Session.object_session(target)
    if session is None:
        return
    overlapping = session.query(Booking).filter(
        Booking.facility_id == target.facility_id,
        Booking.status.in_([BookingStatus.approved, BookingStatus.checked_in]),
        Booking.start_time < target.end_time,
        Booking.end_time > target.start_time
    ).first()
    if overlapping:
        raise ValueError("Booking conflict: The facility is already booked during the requested time.")
