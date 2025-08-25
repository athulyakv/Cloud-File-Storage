from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import re

# ------------------ APP CONFIG ------------------
app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# File upload settings
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------ DB & LOGIN MANAGER ------------------
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ------------------ USER MODEL ------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# ------------------ FILE MODEL ------------------
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return render_template("index.html")

# ------------------ SIGNUP ------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(password) < 8 or not re.search(r"\d", password):
            flash("⚠️ Password must be at least 8 characters and contain a number.", "danger")
            return redirect(url_for('signup'))

        if User.query.filter_by(username=username).first():
            flash("⚠️ Username already taken!", "warning")
            return redirect(url_for('signup'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("✅ Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("signup.html")

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"✅ Welcome back, {user.username}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("❌ Invalid username or password", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")

# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
@login_required
def dashboard():
    user_files = File.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", current_user=current_user, files=user_files)

# ------------------ FILE UPLOAD ------------------
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash("⚠️ No file part in request", "danger")
        return redirect(url_for('dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash("⚠️ No file selected", "warning")
        return redirect(url_for('dashboard'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Save record in DB
        new_file = File(filename=filename, user_id=current_user.id)
        db.session.add(new_file)
        db.session.commit()

        flash("✅ PDF uploaded successfully!", "success")
        return redirect(url_for('dashboard'))
    else:
        flash("❌ Only PDF files are allowed!", "danger")
        return redirect(url_for('dashboard'))

# ------------------ FILE DOWNLOAD ------------------
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ------------------ LOGOUT ------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("✅ You have been logged out.", "info")
    return redirect(url_for('login'))

# ------------------ USER LOADER ------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ MAIN ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
