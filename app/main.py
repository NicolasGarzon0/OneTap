# ------------------------Imports------------------------ #

import os
import io
import csv
import qrcode
import random
import string
from datetime import date
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request, Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, validator
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Member, AttendanceRecord, Meeting, User
from app.auth_utils import verify_password, hash_password
from app.models import Base
from app.database import engine

# ------------------------Setup App------------------------ #

load_dotenv()
ADMIN_SECRET = os.getenv("ADMIN_SECRET")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=ADMIN_SECRET)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static/templates")

@app.get("/", response_class=HTMLResponse)
def homepage():
    return """
    <html>
        <head>
            <title>OneTap Attendance Tracker</title>
        </head>
        <body style="font-family: sans-serif;">
            <h1>🚀 OneTap Attendance Tracker is Running</h1>
            <p>Welcome! Explore the app:</p>
            <ul>
                <li><a href="/checkin" target="_blank">Member Check-In</a></li>
                <li><a href="/login" target="_blank">Admin Login</a></li>
                <li><a href="/register" target="_blank">Register Admin</a></li>
                <li><a href="/admin" target="_blank">Admin Dashboard</a></li>
                <li><a href="/docs" target="_blank">API Docs</a></li>
            </ul>
        </body>
    </html>
    """

# ------------------------Helper Functions------------------------ #

def generate_unique_code(length=4):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_qr(code: str):
    url = f"http://localhost:8000/checkin/{code}"
    img = qrcode.make(url)
    img.save(f"static/qrcodes/{code}.png")
    return f"/static/qrcodes/{code}.png"

def require_admin(request: Request):
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=401, detail="Unauthorized")

# ------------------------Auth Endpoints------------------------ #

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    
    @validator("email")
    def must_contain_at_symbol(cls, v):
        if "@" not in v:
            raise ValueError("Email must contain '@'")
        return v


@app.get("/register", response_class=HTMLResponse)
def serve_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_user(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(username=payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["is_admin"] = True
    request.session["user_id"] = user.id
    request.session["username"] = user.username

    return {"msg": "Registration successful"}


@app.get("/login", response_class=HTMLResponse)
def serve_login(request: Request):
    error = request.session.pop("login_error", None)
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@app.post("/login")
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        request.session["login_error"] = "Invalid username or password"
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    request.session["is_admin"] = True
    request.session["user_id"] = user.id
    return RedirectResponse(url="/admin", status_code=302)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@app.post("/delete-account")
def delete_account(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not logged in")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    meetings = db.query(Meeting).filter(Meeting.created_by == user_id).all()
    for meeting in meetings:
        db.query(AttendanceRecord).filter(AttendanceRecord.meeting_id == meeting.id).delete()
        db.delete(meeting)

    db.delete(user)
    db.commit()
    request.session.clear()

    return RedirectResponse(url="/register", status_code=302)

# ------------------------Check-In System------------------------ #

class CheckInRequest(BaseModel):
    name: str
    email: str
    code: str

    @validator("email")
    def must_contain_at_symbol(cls, v):
        if "@" not in v:
            raise ValueError("Email must contain '@'")
        return v

    @validator("code")
    def code_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Code must not be empty")
        return v

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Name must not be empty")
        return v

@app.get("/checkin", response_class=HTMLResponse)
def serve_checkin_page(request: Request):
    return templates.TemplateResponse("checkin.html", {"request": request, "code": ""})

@app.get("/checkin/{code}", response_class=HTMLResponse)
def serve_checkin_with_code(request: Request, code: str):
    return templates.TemplateResponse("checkin.html", {"request": request, "code": code})

@app.post("/check-in")
def check_in(check_in_data: CheckInRequest, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    
    today = date.today()
    meeting = db.query(Meeting).filter(Meeting.date == today, Meeting.code == check_in_data.code).first()
    if not meeting:
        return {"msg": "Invalid or expired check-in code"}

    member = db.query(Member).filter(Member.email == check_in_data.email).first()
    if not member:
        member = Member(
            name=check_in_data.name,
            email=check_in_data.email,
            created_by=user_id  
        )
        db.add(member)
        db.commit()
        db.refresh(member)

    attendance_exists = db.query(AttendanceRecord).filter(
        AttendanceRecord.user_id == member.id,
        AttendanceRecord.meeting_id == meeting.id
    ).first()

    if attendance_exists:
        return {"msg": "Member already checked in for this meeting"}

    new_attendance_record = AttendanceRecord(
        user_id=member.id,
        meeting_id=meeting.id
    )
    db.add(new_attendance_record)
    db.commit()
    db.refresh(new_attendance_record)

    return {
        "msg": "Check-in successful",
        "name": member.name,
        "email": member.email,
        "meeting_date": meeting.date.isoformat()
    }

# ------------------------Admin UI Endpoints------------------------ #

@app.get("/admin", response_class=HTMLResponse)
def serve_admin(request: Request, _: None = Depends(require_admin)):
    return templates.TemplateResponse("admin.html", {"request": request})

# ------------------------Meeting CRUD (User)------------------------ #

class NewMeeting(BaseModel):
    title: str
    date: str

@app.get("/api/meetings")
def get_meetings(
    request: Request,
    meeting_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin)
):
    user_id = request.session.get("user_id")
    query = db.query(Meeting).filter(Meeting.created_by == user_id)
    if meeting_date:
        query = query.filter(Meeting.date == meeting_date)
    meetings = query.all()
    return {
        "meetings": [
            {"id": m.id, "date": m.date.isoformat(), "code": m.code, "title": m.meeting_title}
            for m in meetings
        ]
    }

@app.post("/api/meetings")
def create_meeting(meeting_data: NewMeeting, request: Request, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    user_id = request.session.get("user_id")

    duplicate = db.query(Meeting).filter(
        Meeting.created_by == user_id,
        Meeting.date == meeting_data.date,
        Meeting.meeting_title == meeting_data.title
    ).first()
    
    if duplicate:
        raise HTTPException(status_code=400, detail="You already created a meeting with this title on that date.")

    while True:
        code = generate_unique_code()
        existing = db.query(Meeting).filter(Meeting.code == code).first()
        if not existing:
            break

    meeting = Meeting(
        date=meeting_data.date,
        code=code,
        meeting_title=meeting_data.title,
        created_by=user_id
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    qr_path = generate_qr(meeting.code)

    return {
        "msg": "Meeting created successfully",
        "meeting_id": meeting.id,
        "date": meeting.date.isoformat(),
        "code": meeting.code,
        "title": meeting.meeting_title,
        "qr_url": qr_path
    }

@app.delete("/api/meetings/{id}")
def delete_meeting(id: int, request: Request, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    user_id = request.session.get("user_id")
    meeting = db.query(Meeting).filter(Meeting.id == id, Meeting.created_by == user_id).first()
    if not meeting:
        return {"msg": "Meeting not found or unauthorized"}
    try:
        db.delete(meeting)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete meeting due to database error.")

    file_path = f"static/qrcodes/{meeting.code}.png"
    if os.path.exists(file_path):
        os.remove(file_path)
    return {"msg": "Meeting deleted successfully"}

# ------------------------Member Management------------------------ #

@app.get("/api/members")
def get_members(request: Request, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    user_id = request.session.get("user_id")
    members = db.query(Member).filter(Member.created_by == user_id).all()
    return {"members": [{"id": m.id, "name": m.name, "email": m.email} for m in members]}

@app.delete("/api/members/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db), _: None = Depends(require_admin)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.query(AttendanceRecord).filter(AttendanceRecord.user_id == member.id).delete()
    db.delete(member)
    db.commit()
    return {"msg": "Member deleted successfully"}

@app.get("/api/members/export")
def export_members(db: Session = Depends(get_db), _: None = Depends(require_admin)):
    members = db.query(Member).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email"])
    for m in members:
        writer.writerow([m.name, m.email])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=members.csv"})

# ------------------------Attendance Management------------------------ #

@app.get("/api/attendance")
def get_attendance(
    request: Request,
    meeting_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    user_name: Optional[str] = Query(None),
    meeting_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    _: None = Depends(require_admin)
):
    user_id_session = request.session.get("user_id")
    query = db.query(AttendanceRecord).join(Meeting).filter(Meeting.created_by == user_id_session)
    if meeting_id:
        query = query.filter(AttendanceRecord.meeting_id == meeting_id)
    elif user_id:
        query = query.filter(AttendanceRecord.user_id == user_id)
    elif user_name:
        query = query.join(Member).filter(Member.name.ilike(f"%{user_name}%"))
    elif meeting_date:
        query = query.join(Meeting).filter(Meeting.date == meeting_date)
    records = query.all()
    return {
        "attendance": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "user_name": r.member.name if r.member else "(deleted)",
                "user_email": r.member.email if r.member else "(deleted)",
                "meeting_id": r.meeting_id,
                "meeting_title": r.meeting.meeting_title if r.meeting else "(deleted)",
                "meeting_date": r.meeting.date.isoformat() if r.meeting else "N/A"
            }
            for r in records
            if r.member and r.meeting
        ]
    }

@app.get("/api/attendance/export")
def export_attendance(request: Request, meeting_id: Optional[int] = Query(None), user_id: Optional[int] = Query(None), db: Session = Depends(get_db), _: None = Depends(require_admin)):
    user_id_session = request.session.get("user_id")
    query = db.query(AttendanceRecord).join(Meeting).filter(Meeting.created_by == user_id_session)
    if meeting_id:
        query = query.filter(AttendanceRecord.meeting_id == meeting_id)
    elif user_id:
        query = query.filter(AttendanceRecord.user_id == user_id)
    records = query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Member Name", "Member Email", "Meeting Title", "Meeting Date"])
    for r in records:
        writer.writerow([r.member.name, r.member.email, r.meeting.meeting_title, r.meeting.date.isoformat()])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=attendance.csv"})

# ------------------------Database Setup------------------------ #
Base.metadata.create_all(bind=engine)
