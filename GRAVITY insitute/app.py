from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gravity_teaching_secret_key_change_in_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/pdf'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

db = SQLAlchemy(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(50), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.String(50))
    price = db.Column(db.Float, default=0.0)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, success, failed

class StudyMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    file_path = db.Column(db.String(300))
    material_type = db.Column(db.String(20))  # pdf, video

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    file_path = db.Column(db.String(300))
    due_date = db.Column(db.Date)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)

# Decorators
def login_required(required_role=None):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('student_login'))
            user_role = session.get('role')
            if required_role and user_role != required_role:
                flash('Access denied.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

# Initialize DB and sample data
with app.app_context():
    db.create_all()
    
    # Sample courses if empty
    if Course.query.count() == 0:
        courses = [
            Course(name='IIT-JEE Preparation', description='Complete JEE prep', duration='2 years', price=50000),
            Course(name='NEET Preparation', description='Complete NEET prep', duration='1 year', price=40000),
            Course(name='Class 11 Science', description='Class 11 PCM', duration='1 year', price=20000),
            Course(name='Class 12 Science', description='Class 12 PCB', duration='1 year', price=20000),
            Course(name='Foundation (Class 9-10)', description='Foundation course', duration='2 years', price=15000)
        ]
        for course in courses:
            db.session.add(course)
        db.session.commit()
    
    # Sample teachers
    if Teacher.query.count() == 0:
        pw_hash = generate_password_hash('teacherpass')
        teachers = [
            Teacher(name='Dr. Physics', email='physics@gravity.com', password_hash=pw_hash, subject='Physics'),
            Teacher(name='Prof. Chem', email='chem@gravity.com', password_hash=pw_hash, subject='Chemistry'),
        ]
        for teacher in teachers:
            db.session.add(teacher)
        db.session.commit()
    
    # Sample admin
    if Admin.query.count() == 0:
        admin_hash = generate_password_hash('admin')
        admin = Admin(name='Admin', email='admin@gravity.com', password_hash=admin_hash)
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route('/')
def home():
    courses = Course.query.all()
    return render_template('index.html', courses=courses)

@app.route('/courses')
def courses():
    all_courses = Course.query.all()
    return render_template('courses.html', courses=all_courses)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        msg = ContactMessage(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form.get('phone'),
            message=request.form['message']
        )
        db.session.add(msg)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/student-signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        if Student.query.filter_by(email=request.form['email']).first():
            flash('Email already registered.', 'danger')
            return render_template('student_signup.html')
        student = Student(
            name=request.form['name'],
            email=request.form['email'],
            password_hash=generate_password_hash(request.form['password'])
        )
        db.session.add(student)
        db.session.commit()
        flash('Signup successful! Please login.', 'success')
        return redirect(url_for('student_login'))
    return render_template('student_signup.html')

@app.route('/student-login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student = Student.query.filter_by(email=request.form['email']).first()
        if student and check_password_hash(student.password_hash, request.form['password']):
            session['user_id'] = student.id
            session['role'] = 'student'
            return redirect(url_for('student_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('student_login.html')

@app.route('/teacher-login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        teacher = Teacher.query.filter_by(email=request.form['email']).first()
        if teacher and check_password_hash(teacher.password_hash, request.form['password']):
            session['user_id'] = teacher.id
            session['role'] = 'teacher'
            return redirect(url_for('teacher_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('teacher_login.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin = Admin.query.filter_by(email=request.form['email']).first()
        if admin and check_password_hash(admin.password_hash, request.form['password']):
            session['user_id'] = admin.id
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('admin_login.html')

@app.route('/student-dashboard')
@login_required('student')
def student_dashboard():
    student_id = session['user_id']
    payments = Payment.query.filter_by(student_id=student_id, status='success').all()
    course_ids = [p.course_id for p in payments]
    enrolled_courses = Course.query.filter(Course.id.in_(course_ids)).all()
    materials = StudyMaterial.query.filter(StudyMaterial.course_id.in_([c.id for c in enrolled_courses])).all()
    assignments = Assignment.query.join(Course).filter(Course.id.in_([c.id for c in enrolled_courses])).all()
    return render_template('student_dashboard.html', materials=materials, assignments=assignments)

@app.route('/teacher-dashboard')
@login_required('teacher')
def teacher_dashboard():
    teacher_id = session['user_id']
    materials = StudyMaterial.query.filter_by(teacher_id=teacher_id).all()
    courses = Course.query.all()
    return render_template('teacher_dashboard.html', materials=materials, courses=courses)

@app.route('/upload-material', methods=['POST'])
@login_required('teacher')
def upload_material():
    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('teacher_dashboard'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('teacher_dashboard'))
        if file:
            material_type = request.form.get('material_type', 'pdf')
            filename = secure_filename(file.filename)
            if material_type == 'video':
                video_folder = 'uploads/video'
                os.makedirs(video_folder, exist_ok=True)
                file_path = os.path.join(video_folder, filename)
            else:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            material = StudyMaterial(
                title=request.form['title'],
                course_id=request.form['course_id'],
                teacher_id=session['user_id'],
                file_path=filename,
                material_type=material_type
            )
        db.session.add(material)
        db.session.commit()
        flash('Material uploaded successfully!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/admin-dashboard')
@login_required('admin')
def admin_dashboard():
    students = Student.query.all()
    payments = Payment.query.all()
    teachers = Teacher.query.all()
    courses = Course.query.all()
    return render_template('admin_dashboard.html', students=students, payments=payments, teachers=teachers, courses=courses)

@app.route('/payment/<int:course_id>', methods=['GET', 'POST'])
@login_required('student')
def payment(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        # Simulate payment
        payment = Payment(
            student_id=session['user_id'],
            course_id=course_id,
            amount=course.price,
            status='success'  # Simulated success
        )
        db.session.add(payment)
        db.session.commit()
        flash('Payment successful! Access granted.', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('payment.html', course=course)

@app.route('/uploads/<material_type>/<filename>')
def uploaded_file(material_type, filename):
    if material_type == 'pdf':
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    elif material_type == 'video':
        video_folder = 'uploads/video'
        return send_from_directory(video_folder, filename)
    abort(404)

@app.route('/enroll')
def enroll():
    return redirect(url_for('courses'))

@app.route('/admin/add-course', methods=['POST'])
@login_required('admin')
def add_course():
    course = Course(
        name=request.form['name'],
        description=request.form['description'],
        duration=request.form['duration'],
        price=float(request.form['price'])
    )
    db.session.add(course)
    db.session.commit()
    flash('Course added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-teacher', methods=['POST'])
@login_required('admin')
def add_teacher():
    teacher = Teacher(
        name=request.form['name'],
        email=request.form['email'],
        password_hash=generate_password_hash(request.form['password']),
        subject=request.form['subject']
    )
    db.session.add(teacher)
    db.session.commit()
    flash('Teacher added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-course/<int:course_id>')
@login_required('admin')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-teacher/<int:teacher_id>')
@login_required('admin')
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    db.session.delete(teacher)
    db.session.commit()
    flash('Teacher deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
