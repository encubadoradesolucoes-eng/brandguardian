from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/brands.db'
app.config['SECRET_KEY'] = 'rescue'
db = SQLAlchemy(app)

# --- MODELOS MÍNIMOS PARA RECUPERAÇÃO ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), default='client')
    name = db.Column(db.String(150))
    account_validated = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_plan = db.Column(db.String(50), default='free')
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    max_brands = db.Column(db.Integer, default=5)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    process_number = db.Column(db.String(50), unique=True)
    registration_mode = db.Column(db.String(50), default='PROTECTION')
    property_type = db.Column(db.String(100), default='marca') 
    name = db.Column(db.String(200), nullable=False)
    registration_number = db.Column(db.String(100))
    nice_classes = db.Column(db.String(200))  
    country = db.Column(db.String(100), default='Moçambique')
    status = db.Column(db.String(50), default='under_study')  
    logo_path = db.Column(db.String(300))
    colors = db.Column(db.String(500))  
    typography = db.Column(db.String(200))
    slogan = db.Column(db.String(300))
    owner_name = db.Column(db.String(200))
    owner_email = db.Column(db.String(200))
    owner_nuit = db.Column(db.String(100))
    owner_phone = db.Column(db.String(100))
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_analyzed = db.Column(db.DateTime)
    risk_score = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(20), default='low')  
    phonetic_score = db.Column(db.Float, default=0.0)
    visual_score = db.Column(db.Float, default=0.0)
    admin_notes = db.Column(db.Text)
    logo_hash = db.Column(db.String(100))
    phonetic_name = db.Column(db.String(200))
    registered_by = db.Column(db.String(100), default='Sistema m24')

class Entity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    nuit = db.Column(db.String(50))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(200))
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100), default='Moçambique')
    facebook = db.Column(db.String(200))
    instagram = db.Column(db.String(200))
    x_social = db.Column(db.String(200))
    status = db.Column(db.String(50), default='Verificado')

class IpiRecord(db.Model):
    __tablename__ = 'ipi_record'
    id = db.Column(db.Integer, primary_key=True)
    process_number = db.Column(db.String(50), index=True)
    record_type = db.Column(db.String(50))
    status = db.Column(db.String(50))
    brand_name = db.Column(db.String(300))
    applicant_name = db.Column(db.String(300))
    nice_class = db.Column(db.String(50))
    bulletin_number = db.Column(db.String(20))
    publication_date = db.Column(db.Date)
    opposition_deadline = db.Column(db.Date)
    image_path = db.Column(db.String(300))
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)

class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100))
    price_monthly = db.Column(db.Float)
    max_brands = db.Column(db.Integer)
    features = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_name = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='MZN')
    payment_method = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    mpesa_transaction_id = db.Column(db.String(100))
    mpesa_conversation_id = db.Column(db.String(100))
    reference = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(50), default='pending')
    response_code = db.Column(db.String(50))
    response_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class BrandNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_name = db.Column(db.String(100))

class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=True)
    assigned_admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='open')
    channel = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message = db.Column(db.Text)
    is_unread_admin = db.Column(db.Boolean, default=True)

class ProcessActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AppNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SystemConfig(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(255))

class RPIMonitoring(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rpi_number = db.Column(db.String(20))
    publication_date = db.Column(db.Date)
    processed = db.Column(db.Boolean, default=False)
    total_new_marks = db.Column(db.Integer, default=0)
    conflicts_detected = db.Column(db.Integer, default=0)
    data_file = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BrandConflict(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    rpi_id = db.Column(db.Integer, db.ForeignKey('rpi_monitoring.id'))
    conflicting_mark_name = db.Column(db.String(200))
    conflicting_mark_number = db.Column(db.String(50))
    similarity_score = db.Column(db.Float)
    conflict_type = db.Column(db.String(50)) 
    status = db.Column(db.String(50), default='pending')
    notified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200))
    status = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

print("🚀 RESCUE DATABASE STARTING...")
if not os.path.exists('instance'): os.makedirs('instance')

with app.app_context():
    print("1. Creating Tables...")
    db.create_all()
    
    print("2. Seeding Admin...")
    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin@m24.co.mz', email='admin@m24.co.mz', role='admin', name='Admin Rescue', account_validated=True)
        admin.set_password('123456')
        db.session.add(admin)
        db.session.commit()
    
    print("3. Seeding MANUAL DATA (seed_deepseek)...")
    try:
        from seed_from_deepseek import seed_deepseek_data
        # Hack: seed_deepseek expects 'app' context from main module usually, but here we provide our context
        # But wait, seed_deepseek imports 'from app import db, IpiRecord'.
        # That will trigger importing app.py which is broken.
        # I cannot import seed_from_deepseek directly if it imports broken app.py.
        print("⚠️ Cannot import seed module directly because app.py is broken.")
        print("⚠️ Proceeding to manual insert of the known CSV content...")
        
        # Leitura manual do CSV 'concessoes_bpi_junho_2023.csv' e inserção direta
        import csv
        
        if os.path.exists('concessoes_bpi_junho_2023.csv'):
            with open('concessoes_bpi_junho_2023.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # 'Proc', 'Marca', 'Classe', 'Titular', ... (conforme o user file original)
                    # Mapear para IpiRecord
                    rec = IpiRecord(
                        process_number=row.get('proc_id') or row.get('Proc'),
                        brand_name=row.get('marca') or row.get('Marca'),
                        applicant_name=row.get('titular_id') or row.get('Titular'), # Era ID, mas vamos por string
                        bulletin_number='BPI-170'
                    )
                    db.session.add(rec)
                    count += 1
                db.session.commit()
                print(f"✅ {count} records imported manually from CSV!")
        else:
            print("❌ CSV manual not found.")
            
    except Exception as e:
        print(f"❌ Error seeding data: {e}")

print("✅ DATABASE RESCUE COMPLETE!")
