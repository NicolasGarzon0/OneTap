from sqlalchemy import Column, Integer, String, Date, ForeignKey, UniqueConstraint
from app.database import Base
from sqlalchemy.orm import relationship

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    __table_args__ = (
        UniqueConstraint("email", "created_by", name="unique_email_per_user"),
    )
    name = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))

    attendance_records = relationship("AttendanceRecord", back_populates="member", cascade="all, delete")
    creator = relationship("User", back_populates="members")

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    code = Column(String(4))
    meeting_title = Column(String, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))

    attendance_records = relationship("AttendanceRecord", back_populates="meeting", cascade="all, delete")
    creator = relationship("User", back_populates="meetings")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id"))
    meeting_id = Column(Integer, ForeignKey("meetings.id"))

    member = relationship("Member", back_populates="attendance_records")
    meeting = relationship("Meeting", back_populates="attendance_records")

    __table_args__ = (
        UniqueConstraint("user_id", "meeting_id", name="one_checkin_per_meeting"),
    )

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    members = relationship("Member", back_populates="creator", cascade="all, delete")
    meetings = relationship("Meeting", back_populates="creator", cascade="all, delete")
