from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
# Database setup
basedir = os.path.abspath(os.path.dirname(__name__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELS ---

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    history = db.Column(db.Text, nullable=True) # JSON or text of past medical history
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'history': self.history
        }

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(50), nullable=False) # 'General', 'Specialist'
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'specialty': self.specialty
        }

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=True)
    symptoms = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Waiting') # 'Waiting', 'In Progress', 'Completed'
    token_number = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='Normal') # 'Normal', 'Urgent'
    type = db.Column(db.String(20), nullable=False) # 'Walk-in', 'Online'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    prescriptions = db.relationship('Prescription', backref='appointment', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'symptoms': self.symptoms,
            'status': self.status,
            'token_number': self.token_number,
            'priority': self.priority,
            'type': self.type,
            'created_at': self.created_at.isoformat(),
            'doctor_name': self.doctor.name if self.doctor else "Unassigned",
            'patient_name': self.patient.name if self.patient else "Unknown"
        }

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    medicines = db.Column(db.Text, nullable=False) # JSON or comma-separated
    order_status = db.Column(db.String(20), nullable=False, default='None') # 'None', 'Ordered', 'Out for Delivery', 'Delivered'

    def to_dict(self):
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'medicines': self.medicines,
            'order_status': self.order_status
        }

# Initialize database
with app.app_context():
    db.create_all()
    
    # Seed demo user
    if not Patient.query.filter_by(phone="1234567899").first():
        p1 = Patient(phone="1234567899", password="pass1", name="Test User", age=30, gender="Male")
        db.session.add(p1)
        db.session.commit()

    # Seed doctors if empty
    if not Doctor.query.filter_by(username="drmaria1").first():
        d1 = Doctor(name="Dr. Maria", username="drmaria1", password="doc2", specialty="General")
        db.session.add(d1)
        db.session.commit()
    
    if not Doctor.query.filter_by(username="drbanner").first():
        d2 = Doctor(name="Dr. Banner", username="drbanner", password="password123", specialty="Specialist")
        db.session.add(d2)
        db.session.commit()

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/kiosk')
def kiosk():
    return render_template('kiosk.html')

@app.route('/online')
def online():
    return render_template('online.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/portal')
def portal():
    return render_template('portal.html')

# --- APIS ---

# AUTH APIS
@app.route('/api/login/patient', methods=['POST'])
def login_patient():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    patient = Patient.query.filter_by(phone=phone, password=password).first()
    if patient:
        return jsonify({'success': True, 'patient': patient.to_dict()})
    return jsonify({'error': 'Invalid phone number or password'}), 401

@app.route('/api/login/doctor', methods=['POST'])
def login_doctor():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    doctor = Doctor.query.filter_by(username=username, password=password).first()
    if doctor:
        return jsonify({'success': True, 'doctor': doctor.to_dict()})
    return jsonify({'error': 'Invalid username or password'}), 401

# Patient Recognition API
@app.route('/api/patient/<phone>', methods=['GET'])
def get_patient(phone):
    patient = Patient.query.filter_by(phone=phone).first()
    if patient:
        # get past prescriptions and appointments
        past_appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.created_at.desc()).all()
        history = [app.to_dict() for app in past_appointments]
        return jsonify({'exists': True, 'patient': patient.to_dict(), 'history': history})
    return jsonify({'exists': False})

@app.route('/api/patient', methods=['POST'])
def create_patient():
    data = request.json
    phone = data.get('phone')
    password = data.get('password', '1234') # default fallback
    if Patient.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Patient with this phone already exists'}), 400
    
    new_patient = Patient(
        phone=phone,
        password=password,
        name=data.get('name'),
        age=data.get('age'),
        gender=data.get('gender'),
        history=data.get('history', '')
    )
    db.session.add(new_patient)
    db.session.commit()
    return jsonify(new_patient.to_dict()), 201

# Smart Triage Engine & Queue Management API
SEVERE_SYMPTOMS = ['chest pain', 'vomiting']

def triage(symptoms_str, pref_doc_id=None):
    symptoms = [s.strip().lower() for s in symptoms_str.split(',')]
    is_severe = any(severe in sym for severe in SEVERE_SYMPTOMS for sym in symptoms)
    
    if pref_doc_id:
        doctor = Doctor.query.get(pref_doc_id)
        if doctor:
            priority = 'Urgent' if is_severe else 'Normal'
            return doctor, priority

    if is_severe:
        doctor = Doctor.query.filter_by(specialty='Specialist').first()
        priority = 'Urgent'
    else:
        doctor = Doctor.query.filter_by(specialty='General').first()
        priority = 'Normal'
        
    return doctor, priority

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    docs = Doctor.query.all()
    res = []
    for d in docs:
        count = Appointment.query.filter_by(doctor_id=d.id, status='Waiting').count()
        doc_dict = d.to_dict()
        doc_dict['queue_size'] = count
        res.append(doc_dict)
    return jsonify({'doctors': res})

@app.route('/api/appointment', methods=['POST'])
def create_appointment():
    data = request.json
    patient_id = data.get('patient_id')
    symptoms = data.get('symptoms')
    appt_type = data.get('type') # 'Walk-in' or 'Online'
    pref_doc = data.get('preferred_doctor')
    
    doctor, priority = triage(symptoms, pref_doc)
    
    # Calculate Token Number and Wait Time
    # Get all currently waiting or in-progress appointments for this doctor
    ahead = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status.in_(['Waiting', 'In Progress'])
    ).count()
    
    last_appt = Appointment.query.order_by(Appointment.id.desc()).first()
    token_number = (last_appt.token_number + 1) if last_appt else 1
    
    new_appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor.id if doctor else None,
        symptoms=symptoms,
        token_number=token_number,
        priority=priority,
        type=appt_type
    )
    db.session.add(new_appt)
    db.session.commit()
    
    wait_time = ahead * 15 # Wait time in minutes
    
    return jsonify({
        'appointment': new_appt.to_dict(),
        'wait_time_minutes': wait_time,
        'patients_ahead': ahead
    }), 201

@app.route('/api/queue', methods=['GET'])
def get_queue():
    doctor_id = request.args.get('doctor_id')
    query = Appointment.query.filter(Appointment.status.in_(['Waiting', 'In Progress']))
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
        
    appts = query.order_by(Appointment.id.asc()).all()
    queue = []
    for i, appt in enumerate(appts):
        appt_dict = appt.to_dict()
        appt_dict['wait_time_minutes'] = i * 15
        queue.append(appt_dict)
        
    return jsonify({'queue': queue})

# Post-Consultation Workflow API
@app.route('/api/appointment/<int:appt_id>', methods=['GET'])
def get_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    # Also calculate current patients ahead if it's waiting
    ahead = 0
    if appt.status in ['Waiting', 'In Progress']:
        ahead = Appointment.query.filter(
            Appointment.doctor_id == appt.doctor_id,
            Appointment.status.in_(['Waiting', 'In Progress']),
            Appointment.id < appt.id
        ).count()
        
    res = appt.to_dict()
    res['wait_time_minutes'] = ahead * 15
    res['patients_ahead'] = ahead
    return jsonify(res)

@app.route('/api/appointment/<int:appt_id>/status', methods=['PUT'])
def update_appointment_status(appt_id):
    data = request.json
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = data.get('status')
    db.session.commit()
    return jsonify(appt.to_dict())

@app.route('/api/prescription', methods=['POST'])
def create_prescription():
    data = request.json
    appt_id = data.get('appointment_id')
    medicines = data.get('medicines')
    
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'Completed'
    
    presc = Prescription(
        appointment_id=appt_id,
        medicines=medicines,
        order_status='None'
    )
    db.session.add(presc)
    db.session.commit()
    return jsonify(presc.to_dict()), 201

@app.route('/api/prescription/<int:presc_id>', methods=['GET'])
def get_prescription(presc_id):
    presc = Prescription.query.get_or_404(presc_id)
    return jsonify(presc.to_dict())

@app.route('/api/patient/<int:patient_id>/prescriptions', methods=['GET'])
def get_patient_prescriptions(patient_id):
    appts = Appointment.query.filter_by(patient_id=patient_id).all()
    appt_ids = [a.id for a in appts]
    prescriptions = Prescription.query.filter(Prescription.appointment_id.in_(appt_ids)).all()
    return jsonify([p.to_dict() for p in prescriptions])

@app.route('/api/medicine/order', methods=['POST'])
def order_medicine():
    data = request.json
    presc_id = data.get('prescription_id')
    
    presc = Prescription.query.get_or_404(presc_id)
    presc.order_status = 'Ordered'
    db.session.commit()
    
    return jsonify(presc.to_dict())

@app.route('/api/medicine/order/<int:presc_id>/status', methods=['PUT'])
def update_medicine_status(presc_id):
    data = request.json
    presc = Prescription.query.get_or_404(presc_id)
    presc.order_status = data.get('status') # 'Out for Delivery', 'Delivered'
    db.session.commit()
    
    return jsonify(presc.to_dict())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
