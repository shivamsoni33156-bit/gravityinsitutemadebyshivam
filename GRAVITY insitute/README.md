# Gravity Teaching Institute Website

## Technology Stack
- Frontend: HTML5, CSS3 (Advanced), JavaScript
- Backend: Python Flask
- Database: SQLite
- Design: Responsive (mobile/tablet/desktop), Glassmorphism, Gradients

## Quick Start
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run development server:
   ```
   python app.py
   ```
3. Open http://127.0.0.1:5000/

## Demo Credentials
**Admin:** admin@gravity.com / `admin`
**Teacher:** physics@gravity.com / `teacherpass`, chem@gravity.com / `teacherpass`
**Student:** Signup new or use after payment sim.

## Features
- Student/Teacher/Admin auth
- Course enrollment + payment simulation
- Teacher uploads PDFs/materials
- Student dashboard (materials after payment)
- Admin full CRUD (courses/teachers)
- Contact form + Maps
- Professional responsive design

## Deployment (Production)
```
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

**WSGI:** `wsgi.py` created for production deployment.

Project complete per spec! 🚀
