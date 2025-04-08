from sqlalchemy.orm import Session
from app import models, schemas, auth
from datetime import datetime
from fastapi import HTTPException, Depends
from typing import Optional

# Only logged-in users can create events
def create_event(
    db: Session,
    event: schemas.EventCreate,
    user: models.User = Depends(auth.get_current_user)
):
    db_event = models.Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def update_event(
    db: Session,
    event_id: int,
    event_data: schemas.EventUpdate,
    user: models.User = Depends(auth.get_current_user)
):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event_data.dict(exclude_unset=True).items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return event

def register_attendee(
    db: Session,
    event_id: int,
    attendee: schemas.AttendeeCreate,
    user: models.User = Depends(auth.get_current_user)
):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if len(event.attendees) >= event.max_attendees:
        raise HTTPException(status_code=400, detail="Event is full")

    db_attendee = models.Attendee(**attendee.dict(), event_id=event_id)
    db.add(db_attendee)
    db.commit()
    db.refresh(db_attendee)
    return db_attendee

def check_in_attendee(
    db: Session,
    attendee_id: int,
    user: models.User = Depends(auth.get_current_user)
):
    attendee = db.query(models.Attendee).filter(models.Attendee.attendee_id == attendee_id).first()
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    attendee.check_in_status = True
    db.commit()
    return attendee

def list_events(
    db: Session,
    status: Optional[str] = None,
    location: Optional[str] = None,
    user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Event)
    if status:
        query = query.filter(models.Event.status == status)
    if location:
        query = query.filter(models.Event.location == location)
    return query.all()

def list_attendees(
    db: Session,
    event_id: int,
    user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.Attendee).filter(models.Attendee.event_id == event_id).all()

# This can run via a background job or admin-only route
def update_event_statuses(db: Session):
    now = datetime.utcnow()
    events = db.query(models.Event).filter(models.Event.end_time < now, models.Event.status != 'completed')
    for event in events:
        event.status = 'completed'
    db.commit()
