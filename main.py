from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import auth, models, crud, schemas
import csv
import io
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="🎉 Event Management API")

app.add_middleware(
    CORSMiddleware,
allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


# 1. Create Event
@app.post("/events", response_model=schemas.EventOut)
def create_event(
    event: schemas.EventCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    return crud.create_event(db, event, user)


# 2. Update Event
@app.put("/events/{event_id}", response_model=schemas.EventOut)
def update_event(
    event_id: int,
    event_data: schemas.EventUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    return crud.update_event(db, event_id, event_data, user)

# 3. Register Attendee
@app.post("/events/{event_id}/attendees", response_model=schemas.AttendeeOut)
def register(
    event_id: int,
    attendee: schemas.AttendeeCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    return crud.register_attendee(db, event_id, attendee, user)


# 4. Check-in
@app.post("/attendees/{attendee_id}/check-in", response_model=schemas.AttendeeOut)
def check_in(
    attendee_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    return crud.check_in_attendee(db, attendee_id, user)


# 5. List Events
@app.get("/events", response_model=list[schemas.EventOut])
def get_events(
    status: str = None,
    location: str = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    crud.update_event_statuses(db)
    return crud.list_events(db, status, location, user)

# 6. List Attendees
@app.get("/events/{event_id}/attendees", response_model=list[schemas.AttendeeOut])
def get_attendees(
    event_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    return crud.list_attendees(db, event_id, user)


# 7. CSV Bulk Check-In
@app.post("/attendees/bulk-checkin")
def bulk_check_in(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.get_current_user)
):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        attendee_id = int(row["attendee_id"])
        crud.check_in_attendee(db, attendee_id, user)
    return {"message": "Bulk check-in successful"}
