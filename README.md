# 📋 OneTap - Attendance Tracker

**OneTap** is a full-stack, web-based attendance management system built with **FastAPI**, **PostgreSQL**, and **HTML/CSS/JavaScript**. It enables organizations to securely manage meetings, member check-ins, and attendance records through an intuitive dashboard, with support for QR-based codes and CSV exports.

---

## 🚀 Features

- 🔐 **User Registration & Login** 
- 📆 **Meeting Creation** 
- ✅ **Member Check-In Portal** 
- 📊 **Admin Dashboard** 
- 📄 **Export Attendance and Members to CSV**
- 🛡️ **Password hashing**
- 🌐 **Fully responsive frontend with HTML + JS**

---

## 🎥 Project Walkthrough

### Member Check-In
![](assets/Check-In.png)

### Login Page
![](assets/Login.png)

### Registration Page
![](assets/Register.png)

### Admin Dashboard 
![](assets/Admin.gif)

---

## 🔐 Environment Configuration

This project uses environment files to manage secrets and DB connections:

- `.env.local` — for local development (connects to local PostgreSQL)
- `.env.docker` — for Docker-based setup (connects to Docker container)

**Create the one you need by copying the example:**

```bash
cp .env.docker .env  # For Docker
cp .env.local .env   # For local development
```
Then run:
```bash
uvicorn app.main:app --reload          # For local
docker compose --env-file .env up      # For Docker

```

---

## 📦 Setup

### Option 1: Manual (Local Python Environment)

1. **Clone the repository**
```bash
git clone https://github.com/NicolasGarzon0/OneTap.git
cd OneTap
```
2. **Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate 
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.local .env
```
Then edit `.env` with your local PostgreSQL credentials:

```bash
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/your_database
ADMIN_SECRET=your_admin_secret_key
```

5. **Run the app**
```bash
uvicorn app.main:app --reload
```

### Option 2: Docker (via Docker Compose)

1. **Ensure you have Docker installed**

2. **Set up environment variables**
```bash
cp .env.docker .env
```
Then edit `.env` to match your Docker DB setup:
```bash
DATABASE_URL=postgresql://postgres:password@db:5432/onetap_db
ADMIN_SECRET=your_admin_secret_key
```

3. **Start the full stack (FastAPI + PostgreSQL)**
```bash
docker compose --env-file .env up --build
```

### In both cases app is available at:
http://localhost:8000

---

## 🛠️ Tech Stack

### 🔙 Backend
- FastAPI – Web framework for building APIs
- Uvicorn – ASGI server for FastAPI
- PostgreSQL – Relational database system
- SQLAlchemy – ORM for database interactions
- Passlib – Password hashing
- Jinja2 – Templating engine

### 🌐 Frontend
- HTML5 – Markup language for structure
- CSS3 – Styling
- JavaScript – Client-side interactivity

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).