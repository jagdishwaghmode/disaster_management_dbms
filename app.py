from flask import Flask, render_template, request, redirect, url_for, flash


from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import os
from dotenv import load_dotenv
import pymysql

# Configure PyMySQL to be used with SQLAlchemy
pymysql.install_as_MySQLdb()

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://root:root123@localhost/disaster_management')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'user'

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    contact = db.Column(db.String(20), nullable=False)

class RationShop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    contact = db.Column(db.String(20), nullable=False)

class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    skills = db.Column(db.String(200), nullable=False)
    availability = db.Column(db.Boolean, default=True)

class Disaster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # flood, earthquake, fire, etc.
    location = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high
    date_reported = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # active, resolved
    description = db.Column(db.Text)

class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)  # fire, police, ambulance, etc.
    contact = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    
class ResourceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(50), nullable=False)  # medical, food, shelter, etc.
    quantity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # pending, approved, delivered
    requestor_name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    date_requested = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('register.html')
            
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return render_template('register.html')
            
        # Create new user (default role is 'user')
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role='user'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        # Get statistics for admin dashboard
        hospitals_count = Hospital.query.count()
        shops_count = RationShop.query.count()
        volunteers_count = Volunteer.query.count()
        active_disasters = Disaster.query.filter_by(status='active').count()
        
        # Get recent disasters
        recent_disasters = Disaster.query.order_by(Disaster.date_reported.desc()).limit(5).all()
        
        # Get pending resource requests
        pending_requests = ResourceRequest.query.filter_by(status='pending').order_by(ResourceRequest.date_requested.desc()).limit(5).all()
        
        return render_template('admin_dashboard.html', 
                              hospitals_count=hospitals_count, 
                              shops_count=shops_count,
                              volunteers_count=volunteers_count,
                              active_disasters=active_disasters,
                              recent_disasters=recent_disasters,
                              pending_requests=pending_requests)
    
    # For regular users
    return render_template('user_dashboard.html')

@app.route('/hospitals')
@login_required
def hospitals():
    hospitals = Hospital.query.all()
    return render_template('hospitals.html', hospitals=hospitals)

@app.route('/ration_shops')
@login_required
def ration_shops():
    shops = RationShop.query.all()
    return render_template('ration_shops.html', shops=shops)

@app.route('/volunteers')
@login_required
def volunteers():
    volunteers = Volunteer.query.all()
    return render_template('volunteers.html', volunteers=volunteers)

@app.route('/disasters')
@login_required
def disasters():
    disasters = Disaster.query.all()
    return render_template('disasters.html', disasters=disasters)

@app.route('/disaster/<int:id>/resolve', methods=['POST'])
@login_required
def resolve_disaster(id):
    if current_user.role != 'admin':
        flash('Only administrators can resolve disasters.')
        return redirect(url_for('disasters'))
    
    disaster = Disaster.query.get_or_404(id)
    disaster.status = 'resolved'
    db.session.commit()
    flash(f'Disaster "{disaster.name}" has been marked as resolved.')
    return redirect(url_for('disasters'))

@app.route('/disaster/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_disaster(id):
    if current_user.role != 'admin':
        flash('Only administrators can edit disasters.')
        return redirect(url_for('disasters'))
    
    disaster = Disaster.query.get_or_404(id)
    
    if request.method == 'POST':
        disaster.name = request.form.get('name')
        disaster.type = request.form.get('type')
        disaster.location = request.form.get('location')
        disaster.severity = request.form.get('severity')
        disaster.description = request.form.get('description')
        
        db.session.commit()
        flash(f'Disaster "{disaster.name}" has been updated successfully.')
        return redirect(url_for('disasters'))
    
    return render_template('edit_disaster.html', disaster=disaster)

@app.route('/disaster/<int:id>/delete', methods=['POST'])
@login_required
def delete_disaster(id):
    if current_user.role != 'admin':
        flash('Only administrators can delete disasters.')
        return redirect(url_for('disasters'))
    
    disaster = Disaster.query.get_or_404(id)
    name = disaster.name
    db.session.delete(disaster)
    db.session.commit()
    flash(f'Disaster "{name}" has been deleted successfully.')
    return redirect(url_for('disasters'))

@app.route('/add_disaster', methods=['GET', 'POST'])
@login_required
def add_disaster():
    if request.method == 'POST':
        from datetime import datetime
        new_disaster = Disaster(
            name=request.form.get('name'),
            type=request.form.get('type'),
            location=request.form.get('location'),
            severity=request.form.get('severity'),
            date_reported=datetime.now(),
            status='active',
            description=request.form.get('description')
        )
        db.session.add(new_disaster)
        db.session.commit()
        flash('Disaster reported successfully!')
        return redirect(url_for('disasters'))
    return render_template('add_disaster.html')

@app.route('/emergency_contacts')
@login_required
def emergency_contacts():
    contacts = EmergencyContact.query.all()
    return render_template('emergency_contacts.html', contacts=contacts)

@app.route('/resource_requests')
@login_required
def resource_requests():
    requests = ResourceRequest.query.all()
    return render_template('resource_requests.html', requests=requests)

@app.route('/resource_request/<int:id>/approve', methods=['POST'])
@login_required
def approve_resource_request(id):
    if current_user.role != 'admin':
        flash('Only administrators can approve resource requests.')
        return redirect(url_for('resource_requests'))
    
    request = ResourceRequest.query.get_or_404(id)
    request.status = 'approved'
    db.session.commit()
    flash(f'Resource request has been approved.')
    return redirect(url_for('resource_requests'))

@app.route('/resource_request/<int:id>/deliver', methods=['POST'])
@login_required
def deliver_resource_request(id):
    if current_user.role != 'admin':
        flash('Only administrators can mark resource requests as delivered.')
        return redirect(url_for('resource_requests'))
    
    request = ResourceRequest.query.get_or_404(id)
    request.status = 'delivered'
    db.session.commit()
    flash(f'Resource request has been marked as delivered.')
    return redirect(url_for('resource_requests'))

@app.route('/add_resource_request', methods=['GET', 'POST'])
@login_required
def add_resource_request():
    if request.method == 'POST':
        from datetime import datetime
        new_request = ResourceRequest(
            resource_type=request.form.get('resource_type'),
            quantity=request.form.get('quantity'),
            location=request.form.get('location'),
            status='pending',
            requestor_name=request.form.get('requestor_name'),
            contact=request.form.get('contact'),
            date_requested=datetime.now(),
            description=request.form.get('description')
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Resource request submitted successfully!')
        return redirect(url_for('resource_requests'))
    return render_template('add_resource_request.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print('Default admin user created')
            
    app.run(debug=True) 