from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean
from app.database import Base
from sqlalchemy.orm import relationship
import enum

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class EventStatus(str, enum.Enum):
    scheduled = 'scheduled'
    ongoing = 'ongoing'
    completed = 'completed'
    canceled = 'canceled'

class Event(Base):
    __tablename__ = "events"
    event_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String)
    max_attendees = Column(Integer)
    status = Column(Enum(EventStatus), default="scheduled")
    attendees = relationship("Attendee", back_populates="event")

class Attendee(Base):
    __tablename__ = "attendees"
    attendee_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    event_id = Column(Integer, ForeignKey("events.event_id"))
    check_in_status = Column(Boolean, default=False)
    event = relationship("Event", back_populates="attendees")
