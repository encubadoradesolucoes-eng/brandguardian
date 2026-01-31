import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import json
import requests
import subprocess
import threading
import socket
import secrets # Para gerar senhas automáticas

# Suporte para Executável (PyInstaller)
def get_resource_path(relative_path):
    """Retorna o caminho do recurso (templates, static) no bundle ou local."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

def get_persistence_path(relative_path):
    """Retorna o caminho para persistência (db, uploads) next to the .exe."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.abspath(os.path.join(os.path.dirname(sys.executable), relative_path))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

app = Flask(__name__, 
            template_folder=get_resource_path('templates'),
            static_folder=get_resource_path('static'))
app.config['SECRET_KEY'] = 'm24_super_secure_key_2026'

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Suporte para PostgreSQL (Produção) ou SQLite (Local)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or ('sqlite:///' + os.path.join(get_persistence_path('database'), 'brands.db'))
app.config['UPLOAD_FOLDER'] = get_persistence_path('uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Extensões permitidas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
ALLOWED_DOC_EXTENSIONS = {'xlsx', 'xls', 'csv'}

NICE_CLASSES_DICT = {
    '1': 'Produtos químicos', '2': 'Tintas e vernizes', '3': 'Cosméticos e limpeza', '4': 'Óleos e lubrificantes',
    '5': 'Produtos farmacêuticos', '6': 'Metais comuns', '7': 'Máquinas e ferramentas', '8': 'Ferramentas manuais',
    '9': 'Tecnologia, Software e Elétrica', '10': 'Aparelhos médicos', '11': 'Aparelhos de iluminação/aquecimento',
    '12': 'Veículos e locomoção', '13': 'Armas de fogo', '14': 'Joalharia e relógios', '15': 'Instrumentos musicais',
    '16': 'Papelaria e livros', '17': 'Borracha e plásticos', '18': 'Couro e malas', '19': 'Materiais de construção',
    '20': 'Móveis e espelhos', '21': 'Utensílios domésticos', '22': 'Cordas e tendas', '23': 'Fios para uso têxtil',
    '24': 'Tecidos e têxteis', '25': 'Vestuário, calçado e chapelaria', '26': 'Rendas e bordados', '27': 'Tapetes e revestimentos',
    '28': 'Jogos e brinquedos', '29': 'Carnes e laticínios', '30': 'Café, chá e confeitaria', '31': 'Produtos agrícolas/vivos',
    '32': 'Cervejas e bebidas não alcoólicas', '33': 'Bebidas alcoólicas', '34': 'Tabaco e tabacaria',
    '35': 'Publicidade e Gestão de Negócios', '36': 'Seguros e Financeiro', '37': 'Construção e Reparação',
    '38': 'Telecomunicações', '39': 'Transporte e Viagens', '40': 'Tratamento de materiais', '41': 'Educação e Entretenimento',
    '42': 'Serviços Científicos e Tecnológicos (TI)', '43': 'Serviços de Alimentação e Alojamento',
    '44': 'Serviços Médicos e Veterinários', '45': 'Serviços Jurídicos e de Segurança'
}

@app.template_filter('nice_translate')
def nice_translate(classes_str):
    if not classes_str: return "Não especificado"
    parts = str(classes_str).split(',')
    labels = []
    for p in parts:
        p = p.strip()
        label = NICE_CLASSES_DICT.get(p, p)
        labels.append(f"{p} ({label})")
    return ", ".join(labels)

db = SQLAlchemy(app)

# Criar pastas se não existirem
os.makedirs('uploads', exist_ok=True)
os.makedirs('database', exist_ok=True)
os.makedirs('static', exist_ok=True)

# ========== CONFIGURAÇÃO DE EMAIL (REAL) ==========
from flask_mail import Mail, Message

# PREENCHA AQUI SEUS DADOS REAIS
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'encubadoradesolucoes@gmail.com'  
app.config['MAIL_PASSWORD'] = 'yews wyma gjoq ifvk'      # <--- SENHA CONFIGURADA CORRETAMENTE
app.config['MAIL_DEFAULT_SENDER'] = ('M24 Brand Guardian', 'encubadoradesolucoes@gmail.com')

mail = Mail(app)

def send_m24_email(recipient, subject, html_content, attachments=None):
    """Função unificada de envio de email com auditoria automática."""
    with app.app_context():
        msg = Message(subject=subject, recipients=[recipient])
        msg.html = html_content
        
        if attachments:
            for att in attachments:
                # att = {'filename': '...', 'content_type': '...', 'data': ...}
                msg.attach(att['filename'], att['content_type'], att['data'])
        
        try:
            mail.send(msg)
            # Log de Sucesso
            log = EmailLog(recipient=recipient, subject=subject, status='sent')
            db.session.add(log)
            db.session.commit()
            return True
        except Exception as e:
            error_str = str(e)
            print(f">>> FALHA SMTP ({recipient}): {error_str}")
            # Log de Erro
            log = EmailLog(recipient=recipient, subject=subject, status='error', error_message=error_str)
            db.session.add(log)
            db.session.commit()
            return False

def send_welcome_async(entity_id, name, email):
    with app.app_context():
        try:
            validation_url = f"http://localhost:7000/confirm_validation/{entity_id}"
            html = render_template('emails/welcome_finalize.html', name=name, url=validation_url)
            send_m24_email(email, "🚀 Bem-vindo ao m24 PRO - Finalize seu Acesso", html)
        except Exception as e:
            print(f"Erro render welcome: {e}")

from modules.brand_analyzer import BrandAnalyzer
from modules.web_scraper import WebScraper



# ========== MODELOS DE USUÁRIO E AUTH ==========
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), default='client') # 'admin' ou 'client'
    name = db.Column(db.String(150)) # Nome de exibição
    account_validated = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    last_active = db.Column(db.DateTime, default=datetime.utcnow) # Para saber quem está online
    
    # Sistema de Assinaturas
    subscription_plan = db.Column(db.String(50), default='free') # 'free', 'starter', 'professional', 'business', 'enterprise'
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    max_brands = db.Column(db.Integer, default=5) # Limite de marcas por plano
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.after_request
def update_last_active(response):
    if current_user.is_authenticated:
        # Apenas para fins de tracking de online/offline
        current_user.last_active = datetime.utcnow()
        db.session.commit()
    return response

# ========== MODELOS ==========
class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200))
    status = db.Column(db.String(50)) # 'sent' ou 'error'
    error_message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SubscriptionPlan(db.Model):
    """Planos de assinatura disponíveis"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # 'starter', 'professional', etc
    display_name = db.Column(db.String(100)) # Nome amigável
    price_monthly = db.Column(db.Float) # Preço em MT
    max_brands = db.Column(db.Integer) # Limite de marcas
    features = db.Column(db.Text) # JSON com features incluídas
    is_active = db.Column(db.Boolean, default=True)

class RPIMonitoring(db.Model):
    """Monitoramento da Revista da Propriedade Industrial"""
    id = db.Column(db.Integer, primary_key=True)
    rpi_number = db.Column(db.String(20)) # Ex: "RPI 2756"
    publication_date = db.Column(db.Date)
    processed = db.Column(db.Boolean, default=False)
    total_new_marks = db.Column(db.Integer, default=0)
    conflicts_detected = db.Column(db.Integer, default=0)
    data_file = db.Column(db.String(255)) # Caminho para arquivo processado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BrandConflict(db.Model):
    """Conflitos detectados entre marcas do cliente e novos pedidos"""
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    rpi_id = db.Column(db.Integer, db.ForeignKey('rpi_monitoring.id'))
    conflicting_mark_name = db.Column(db.String(200))
    conflicting_mark_number = db.Column(db.String(50)) # Número do processo INPI
    similarity_score = db.Column(db.Float) # 0-100
    conflict_type = db.Column(db.String(50)) # 'phonetic', 'visual', 'both'
    status = db.Column(db.String(50), default='pending') # 'pending', 'reviewed', 'dismissed'
    notified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    brand = db.relationship('Brand', backref='conflicts')

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

    def get_user(self):
        return User.query.filter_by(email=self.email).first()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'nuit': self.nuit,
            'email': self.email,
            'status': self.status
        }

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) 
    process_number = db.Column(db.String(50), unique=True) # Ex: M24-2024-001
    registration_mode = db.Column(db.String(50), default='PROTECTION') # PROTECTION (Existente) ou NEW_REGISTRATION (Novo Pedido)
    property_type = db.Column(db.String(100), default='marca') 
    name = db.Column(db.String(200), nullable=False)
    registration_number = db.Column(db.String(100)) # Numero oficial do INPI
    nice_classes = db.Column(db.String(200))  
    country = db.Column(db.String(100), default='Moçambique')
    
    # Status do Processo: under_study, waiting_admin, approved, rejected, monitored
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
    admin_notes = db.Column(db.Text) # Notas do gestor m24
    
    logo_hash = db.Column(db.String(100))
    phonetic_name = db.Column(db.String(200))
    registered_by = db.Column(db.String(100), default='Sistema m24') # Quem registrou (Ex: Admin, Titular)

    def generate_process_number(self):
        """Gera um número de processo único no formato M24-YYYY-XXX."""
        year = datetime.utcnow().year
        # Conta marcas criadas este ano
        count = Brand.query.filter(Brand.submission_date >= datetime(year, 1, 1)).count()
        return f"M24-{year}-{(count + 1):03d}"

class BrandNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_name = db.Column(db.String(100)) # cache name for speed

class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=True) # Contexto opcional
    assigned_admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='open') # open, in_progress, closed
    channel = db.Column(db.String(50)) # chat, whatsapp, call
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message = db.Column(db.Text)
    is_unread_admin = db.Column(db.Boolean, default=True) # Notificação para Admin

class ProcessActivity(db.Model):
    # Log de tudo que acontece no processo (Auditoria)
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100)) # 'status_change', 'new_note', 'analysis'
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def generate_process_number(self):
        year = datetime.now().year
        count = Brand.query.filter(Brand.process_number.like(f"M24-{year}-%")).count()
        return f"M24-{year}-{(count + 1):03d}"

    def to_dict(self):
        return {
            'id': self.id,
            'property_type': self.property_type,
            'name': self.name,
            'registration_number': self.registration_number,
            'nice_classes': self.nice_classes,
            'country': self.country,
            'status': self.status,
            'logo_path': self.logo_path,
            'colors': self.colors,
            'typography': self.typography,
            'slogan': self.slogan,
            'owner_name': self.owner_name,
            'owner_email': self.owner_email,
            'owner_nuit': self.owner_nuit,
            'owner_phone': self.owner_phone,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level
        }



class AppNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info') # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SystemConfig(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(255))



@app.context_processor
def utility_processor():
    def get_user_by_email(email):
        if not email: return None
        return User.query.filter_by(email=email).first()
    return dict(get_user_by_email=get_user_by_email)


# ========== FUNÇÕES AUXILIARES ==========
def allowed_file(filename, type='image'):
    if type == 'image':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    else:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS



# ========== ROTAS DE AUTENTICAÇÃO ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            user.account_validated = True
            from datetime import datetime
            user.last_login = datetime.now()
            db.session.commit()
            
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Email ou senha incorretos.', 'danger')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Dados do Usuário
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Dados da Entidade
        nuit = request.form.get('nuit')
        phone = request.form.get('phone')
        city = request.form.get('city')
        address = request.form.get('address')
        country = request.form.get('country', 'Moçambique')
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado em nossa base.', 'warning')
            return redirect(url_for('signup'))
            
        # 1. Criar Entidade (Titular)
        new_entity = Entity(
            name=name,
            nuit=nuit,
            email=email,
            phone=phone,
            city=city,
            address=address,
            country=country
        )
        db.session.add(new_entity)
        
        # 2. Criar Usuário (Login)
        new_user = User(
            username=email, # No novo fluxo, login é o email
            email=email, 
            role='client',
            name=name,
            account_validated=False # Necessário validar via email
        )
        new_user.set_password(password)
        db.session.add(new_user)
        
        try:
            db.session.commit()
            
            # 3. Enviar Instrução de Finalização (Email)
            threading.Thread(target=send_welcome_async, 
                           args=(new_entity.id, name, email)).start()

            flash('Conta criada! Verifique seu email para validar o acesso.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar cadastro: {str(e)}', 'danger')
            return redirect(url_for('signup'))
        
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing'))


# ========== ROTAS PRINCIPAIS ==========
@app.route('/')
def landing():
    return render_template('landing.html')




@app.route('/save_entity', methods=['POST'])
def save_entity():
    entity_id = request.form.get('entity_id')
    
    if entity_id:
        # Editar existente
        entity = Entity.query.get(entity_id)
        if entity:
            entity.name = request.form.get('name')
            entity.nuit = request.form.get('nuit')
            entity.email = request.form.get('email')
            entity.phone = request.form.get('phone')
            entity.country = request.form.get('country')
            entity.address = request.form.get('address')
            flash('Titular atualizado com sucesso!', 'success')
    else:
        # Criar novo
        new_entity = Entity(
            name=request.form.get('name'),
            nuit=request.form.get('nuit'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            country=request.form.get('country'),
            address=request.form.get('address'),
            city='Maputo' # Default
        )
        db.session.add(new_entity)
        flash('Novo titular cadastrado com sucesso!', 'success')
    
    db.session.commit()
    return redirect(url_for('entities'))

@app.route('/entity/delete/<int:id>')
def delete_entity(id):
    entity = Entity.query.get(id)
    if entity:
        db.session.delete(entity)
        db.session.commit()
        flash('Titular removido.', 'success')
    return redirect(url_for('entities'))



@app.route('/dossie')
@login_required
def index():
    # FILTRAGEM COMPLETA POR STATUS
    status_filter = request.args.get('status')
    search_query = request.args.get('q')
    
    query = Brand.query
    
    if current_user.role != 'admin':
        query = query.filter_by(user_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
        
    if search_query:
        query = query.filter(Brand.name.ilike(f'%{search_query}%'))

    brands = query.order_by(Brand.submission_date.desc()).all()
    
    # Contadores para os filtros
    c_query = Brand.query
    if current_user.role != 'admin':
        c_query = c_query.filter_by(user_id=current_user.id)
        
    counts = {
        'all': c_query.count(),
        'under_study': c_query.filter_by(status='under_study').count(),
        'waiting_admin': c_query.filter_by(status='waiting_admin').count(),
        'approved': c_query.filter_by(status='approved').count(),
        'rejected': c_query.filter_by(status='rejected').count(),
        'monitored': c_query.filter_by(status='monitored').count()
    }

    return render_template('index.html', brands=brands, counts=counts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Dados da Marca
        name = request.form.get('name')
        property_type = request.form.get('type', 'marca')
        nice_classes = request.form.get('nice_classes', '') 
        country = request.form.get('country', 'Moçambique')
        slogan = request.form.get('slogan')
        
        # Colors
        c1 = request.form.get('color1', '#6366f1')
        c2 = request.form.get('color2', '#a855f7')
        colors = json.dumps([c1, c2])

        # Logo Upload
        logo_path = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logo_path = filename

        # --- Lógica de Titular (Entity) ---
        entity_id = request.form.get('entity_id')
        
        owner_name = request.form.get('owner_name')
        owner_nuit = request.form.get('nuit')
        owner_email = request.form.get('owner_email')
        owner_phone = request.form.get('owner_phone')
        owner_address = request.form.get('owner_address')
        owner_city = request.form.get('owner_city')
        owner_country = request.form.get('owner_country')
        
        if entity_id and entity_id not in ['new', 'current_user']:
            # Usar Titular Existente (Admin escolhendo)
            entity = Entity.query.get(int(entity_id))
        elif entity_id == 'current_user':
            # Cliente Logado vinculado automaticamente
            entity = Entity.query.filter_by(email=current_user.email).first()
        
        if entity:
            # --- ATUALIZAR DADOS DA ENTIDADE (Se editado no form) ---
            # O usuário explicitamente pediu para atualizar dados
            if owner_email and owner_email != entity.email:
                 entity.email = owner_email
            if owner_phone: entity.phone = owner_phone
            if owner_address: entity.address = owner_address
            if owner_city: entity.city = owner_city
            if owner_country: entity.country = owner_country
            if owner_name: entity.name = owner_name
            if owner_nuit: entity.nuit = owner_nuit
            
            db.session.commit()
            print(f">>> Dados da Entidade {entity.name} atualizados.")
        
        else:
            # Criar Novo Titular (Se não existir pelo email/nuit)
            # Verifica duplicidade básica
            existing_ent = Entity.query.filter((Entity.nuit == owner_nuit) | (Entity.email == owner_email)).first()
            if existing_ent:
                entity = existing_ent
                flash('Titular já existia no banco de dados. Vinculado automaticamente.', 'info')
            else:
                new_entity = Entity(
                    name=owner_name,
                    nuit=owner_nuit,
                    email=owner_email,
                    phone=owner_phone,
                    address=owner_address,
                    city=owner_city,
                    country=owner_country
                )
                db.session.add(new_entity)
                db.session.commit()
                entity = new_entity

        # --- GESTÃO DE CONTA DE USUÁRIO (LOGIN) ---
        user = User.query.filter_by(email=entity.email).first()
        raw_password = None
        if not user:
            raw_password = secrets.token_urlsafe(8)
            user = User(
                username=entity.email,
                email=entity.email,
                role='client',
                name=entity.name
            )
            user.set_password(raw_password)
            db.session.add(user)
            db.session.commit()

        # Criar nova marca (VINCULADA AO USUÁRIO)
        new_brand = Brand(
            name=name,
            property_type=property_type,
            nice_classes=nice_classes,
            country=country,
            slogan=slogan,
            logo_path=logo_path,
            owner_name=entity.name,
            owner_email=entity.email,
            owner_nuit=entity.nuit,
            owner_phone=entity.phone,
            user_id=user.id if user else (current_user.id if current_user.is_authenticated else None),
            registered_by=current_user.name if current_user.is_authenticated else 'Auto-Registro',
            registration_mode=request.form.get('registration_mode', 'NEW_REGISTRATION')
        )
        
        # Gerar número de processo para novos pedidos
        if new_brand.registration_mode == 'NEW_REGISTRATION':
            new_brand.process_number = new_brand.generate_process_number()
            new_brand.status = 'under_study'
        else:
            new_brand.status = 'monitored' # Marcas já existentes que estamos vigiando
        
        db.session.add(new_brand)
        db.session.commit()

        # --- NOTIFICAÇÕES TUDO-EM-UM (Threaded) ---
        def notify_async(entity_id, brand_id, pwd):
            with app.app_context():
                try:
                    ent = Entity.query.get(entity_id)
                    brand_data = Brand.query.get(brand_id)
                    if not ent or not brand_data: return

                    # 1. WhatsApp
                    wa_api = os.environ.get('WHATSAPP_API_URL', 'http://localhost:3002')
                    if ent.phone:
                        cred_text = f"\n\n🔑 *Acesso ao Portal:* {ent.email} / {pwd}" if pwd else ""
                        msg_wa = (f"🔐 *M24 Brand Guardian*\n\n"
                                  f"Olá *{ent.name}*,\n"
                                  f"Recebemos seu pedido de proteção para a marca *{brand_data.name}*.\n"
                                  f"Processo: {brand_data.process_number or 'Vigilância Ativa'}{cred_text}\n\n"
                                  f"Status: *Sob Análise IA*")
                        try:
                            requests.post(f'{wa_api}/send', json={'phone': ent.phone, 'message': msg_wa}, timeout=5)
                        except Exception as wa_err:
                            print(f">>> Erro WhatsApp Async: {wa_err}")
                    
                    # 2. Email
                    cred_html = f"<div style='background:#f3f4f6; padding:15px; margin:20px 0;'><strong>Dados de Acesso:</strong> {ent.email} / {pwd}</div>" if pwd else ""
                    html_content = (f"<h3>Olá, {ent.name}</h3>"
                                     f"<p>Confirmamos o início do processo de proteção para a marca <strong>{brand_data.name}</strong>.</p>"
                                     f"<p>Número de Processo: <strong>{brand_data.process_number or 'Monitoramento'}</strong></p>"
                                     f"{cred_html}"
                                     f"<p>Nossa IA já está varrendo a base nacional para detectar possíveis conflitos.</p>"
                                     f"<hr><small>M24 Security Systems</small>")
                    
                    send_m24_email(ent.email, f"Protocolo de Proteção: {brand_data.name} - M24 Brand Guardian", html_content)

                except Exception as ex:
                    print(f"Erro Crítico Notificação Async: {ex}")

        threading.Thread(target=notify_async, args=(entity.id, new_brand.id, raw_password)).start()

        # Iniciar análise automática inteligente
        try:
            analyzer = BrandAnalyzer()
            with app.app_context():
                analyzer.analyze_brand(new_brand.id, db.session, Brand)
            
            # Tomada de Decisão Automatizada M24
            if new_brand.registration_mode == 'NEW_REGISTRATION':
                if new_brand.risk_score > 60: # Alto risco
                     new_brand.status = 'waiting_admin' # Precisa de veredito humano
                     print(f">>> PROCESSO {new_brand.process_number} EM LISTA DE ESPERA (RISCO ALTO)")
                elif new_brand.risk_score < 15: # Baixíssimo risco (Reduzido para 15% para maior segurança)
                     new_brand.status = 'approved'
                     print(f">>> PROCESSO {new_brand.process_number} APROVADO AUTOMATICAMENTE")
                else: # Risco Moderado
                     new_brand.status = 'waiting_admin'
            
            # Garantir que sai do estado 'under_study' após análise
            if new_brand.status == 'under_study':
                new_brand.status = 'waiting_admin'

            db.session.commit()
        except Exception as e:
            print(f"Erro analise: {e}")

        flash('Processo submetido com sucesso! Credenciais enviadas ao titular.', 'success')
        return redirect(url_for('index'))

    # GET: Passar Lista de Entidades
    entities = Entity.query.order_by(Entity.name).all()
    return render_template('register.html', entities=entities, nice_dict=NICE_CLASSES_DICT)


@app.route('/import', methods=['POST'])
def import_brands():
    if 'file' not in request.files:
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file and allowed_file(file.filename, 'doc'):
        try:
            # Ler Excel
            df = pd.read_excel(file) if file.filename.endswith(('.xlsx', '.xls')) else pd.read_csv(file)

            imported = 0
            for _, row in df.iterrows():
                # Mapear colunas (ajustar conforme seu template)
                brand = Brand(
                    name=row.get('Nome', ''),
                    nice_classes=str(row.get('Classes', '')),
                    country=row.get('País', ''),
                    slogan=row.get('Slogan', ''),
                    owner_name=row.get('Titular', ''),
                    owner_email=row.get('Email', ''),
                    colors=row.get('Cores', '[]'),
                    status='pending'
                )
                db.session.add(brand)
                imported += 1

            db.session.commit()
            flash(f'{imported} marcas importadas com sucesso!', 'success')

        except Exception as e:
            flash(f'Erro ao importar arquivo: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/analyze/<int:brand_id>')
def analyze_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)

    # Executar análise
    analyzer = BrandAnalyzer()
    similar_brands = analyzer.analyze_brand(brand_id, db.session, Brand)

    # Executar varredura web (opcional)
    if request.args.get('web_scan'):
        scraper = WebScraper()
        web_results = scraper.search_brand(brand.name)
    else:
        web_results = []

    return render_template('analyze.html',
                           brand=brand,
                           similar=similar_brands,
                           web_results=web_results)


@app.route('/api/global_scan', methods=['POST'])
@login_required
def global_scan():
    """Realiza varredura completa em todas as marcas (Relatório Global)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    brands = Brand.query.all()
    analyzer = BrandAnalyzer()
    
    count = 0
    for brand in brands:
        try:
            with app.app_context():
                analyzer.analyze_brand(brand.id, db.session, Brand)
            count += 1
        except Exception as e:
            print(f"Erro no scan global (Brand {brand.id}): {e}")
            
    # Salvar data da última varredura global
    config = SystemConfig.query.get('last_global_scan')
    if not config:
        config = SystemConfig(key='last_global_scan')
        db.session.add(config)
    config.value = datetime.now().isoformat()
    db.session.commit()
            
    return jsonify({
        'status': 'success',
        'message': f'Análise global concluída. {count} marcas processadas.',
        'timestamp': config.value
    })

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API para análise rápida (uso público)"""
    data = request.json
    name = data.get('name', '')
    classes = data.get('classes', [])

    if not name:
        return jsonify({'error': 'Nome da marca é obrigatório'}), 400

    # Análise básica
    analyzer = BrandAnalyzer()
    results = analyzer.quick_analysis(name, classes, db.session, Brand)

    return jsonify(results)


@app.route('/brand/<int:brand_id>')
def brand_detail(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    entity = Entity.query.filter_by(email=brand.owner_email).first()
    
    # Buscar mensagens/notas internas
    notes = BrandNote.query.filter_by(brand_id=brand_id).order_by(BrandNote.timestamp.asc()).all()
    
    history = [
        {'date': brand.submission_date, 'title': 'Submissão do Processo', 'desc': f'Processo iniciado por {brand.registered_by or "Sistema"}.'},
        {'date': brand.last_analyzed, 'title': 'Análise Inteligente m24 IA', 'desc': f'Varredura de similaridade concluída com Score de {brand.risk_score}%.'}
    ]
    
    # Adicionar decisões ao histórico se existirem
    if brand.status == 'approved':
        history.append({'date': datetime.now(), 'title': 'Aprovação Administrativa', 'desc': 'O gestor validou os critérios de viabilidade.'})
    elif brand.status == 'rejected':
        history.append({'date': datetime.now(), 'title': 'Reprovação IA/Humana', 'desc': 'Conflitos críticos impeditivos detectados.'})

    return render_template('brand_detail.html', brand=brand, entity=entity, history=history, notes=notes)

@app.route('/brand/action/<int:brand_id>/<action>')
@login_required
def update_brand_status(brand_id, action):
    if current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    brand = Brand.query.get_or_404(brand_id)
    old_status = brand.status
    
    if action == 'approve':
        brand.status = 'approved'
        flash(f'Marca {brand.name} aprovada com sucesso!', 'success')
    elif action == 'reject':
        brand.status = 'rejected'
        flash(f'Marca {brand.name} marcada como REPROVADA.', 'danger')
    elif action == 'monitor':
        brand.status = 'monitored'
        flash(f'Marca {brand.name} agora está em vigilância ativa IPI.', 'info')
    
    if brand.status != old_status:
        # Registrar Atividade
        act = ProcessActivity(
            brand_id=brand.id,
            user_id=current_user.id,
            action='status_change',
            description=f"Status alterado de {old_status.upper()} para {brand.status.upper()}"
        )
        db.session.add(act)
    
    db.session.commit()
    return redirect(url_for('brand_detail', brand_id=brand_id))

@app.route('/brand/add_note/<int:brand_id>', methods=['POST'])
@login_required
def add_brand_note(brand_id):
    content = request.form.get('content')
    if content:
        note = BrandNote(
            brand_id=brand_id,
            user_id=current_user.id,
            content=content,
            user_name=current_user.name or current_user.username
        )
        db.session.add(note)
        db.session.commit()
        flash('Mensagem registrada no histórico do processo.', 'success')
    return redirect(url_for('brand_detail', brand_id=brand_id))

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/brands')
def api_brands():
    brands = Brand.query.all()
    return jsonify([brand.to_dict() for brand in brands])


@app.route('/dashboard')
@login_required
def dashboard():
    # Lógica baseada no Perfil (Role)
    if current_user.role == 'admin':
        # ADMIN: Relatório Global de Inteligência
        total_brands = Brand.query.count()
        high_risk_count = Brand.query.filter_by(risk_level='high').count()
        waiting_admin = Brand.query.filter_by(status='waiting_admin').count()
        
        # Gerar Recomendações Automáticas (Logica IA)
        recommendations = []
        hr_brands = Brand.query.filter_by(risk_level='high').limit(3).all()
        for b in hr_brands:
            recommendations.append({
                'brand': b.name,
                'action': 'Iniciar Oposição Legal',
                'reason': f'Similaridade crítica ({(b.risk_score or 0):.1f}%) detectada.'
            })
        
        stats = {
            'total': total_brands,
            'pending': Brand.query.filter(Brand.status.in_(['under_study', 'waiting_admin'])).count(),
            'registered': Brand.query.filter(Brand.status.in_(['approved', 'monitored'])).count(),
            'waiting_admin': waiting_admin,
            'high_risk': high_risk_count,
            'medium_risk': Brand.query.filter_by(risk_level='medium').count(),
            'low_risk': Brand.query.filter_by(risk_level='low').count(),
            'protected_value': total_brands * 15000,
            'total_entities': Entity.query.count(),
            'user_role': 'Gestor de Plataforma M24'
        }
        
        recent = Brand.query.order_by(Brand.submission_date.desc()).limit(8).all()
        return render_template('dashboard.html', stats=stats, recent=recent, recommendations=recommendations)
    
    else:
        # CLIENTE: Vê apenas suas estatísticas
        my_brands = Brand.query.filter_by(user_id=current_user.id)
        stats = {
            'total': my_brands.count(),
            'pending': my_brands.filter(Brand.status.in_(['under_study', 'waiting_admin'])).count(),
            'registered': my_brands.filter(Brand.status.in_(['approved', 'monitored'])).count(),
            'high_risk': my_brands.filter_by(risk_level='high').count(),
            'low_risk': my_brands.filter_by(risk_level='low').count(),
            'medium_risk': my_brands.filter_by(risk_level='medium').count(),
            'protected_value': 0, # Clientes não vêem valor global
            'user_role': current_user.name
        }
        recent = my_brands.order_by(Brand.submission_date.desc()).limit(5).all()
        high_risk = my_brands.filter_by(risk_level='high').limit(5).all()
        return render_template('dashboard.html', stats=stats, recent=recent, high_risk=high_risk)

@app.route('/conflicts')
@login_required
def conflicts():
    """Página de alertas de conflitos detectados"""
    if current_user.role == 'admin':
        all_conflicts = BrandConflict.query.order_by(BrandConflict.created_at.desc()).all()
    else:
        # Cliente vê apenas conflitos de suas marcas
        my_brand_ids = [b.id for b in Brand.query.filter_by(user_id=current_user.id).all()]
        all_conflicts = BrandConflict.query.filter(BrandConflict.brand_id.in_(my_brand_ids)).order_by(BrandConflict.created_at.desc()).all()
    
    # Estatísticas
    pending = sum(1 for c in all_conflicts if c.status == 'pending')
    reviewed = sum(1 for c in all_conflicts if c.status == 'reviewed')
    dismissed = sum(1 for c in all_conflicts if c.status == 'dismissed')
    total_rpis = RPIMonitoring.query.filter_by(processed=True).count()
    
    return render_template('conflicts.html',
                           conflicts=all_conflicts,
                           pending_conflicts=pending,
                           reviewed_conflicts=reviewed,
                           dismissed_conflicts=dismissed,
                           total_rpis=total_rpis)

@app.route('/api/conflicts/<int:conflict_id>/review', methods=['POST'])
@login_required
def review_conflict(conflict_id):
    """Marca conflito como analisado"""
    conflict = BrandConflict.query.get_or_404(conflict_id)
    conflict.status = 'reviewed'
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Conflito marcado como analisado'})

@app.route('/api/conflicts/<int:conflict_id>/dismiss', methods=['POST'])
@login_required
def dismiss_conflict(conflict_id):
    """Marca conflito como resolvido"""
    conflict = BrandConflict.query.get_or_404(conflict_id)
    conflict.status = 'dismissed'
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Conflito resolvido'})

@app.route('/entities')
@login_required
def entities():
    # Apenas ADMIN pode ver a lista de todos os titulares
    if current_user.role != 'admin':
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('dashboard'))
        
    all_entities = Entity.query.all()
    for ent in all_entities:
        ent.brand_count = Brand.query.filter_by(owner_name=ent.name).count()
    return render_template('entities.html', entities=all_entities)


@app.route('/support')
@login_required
def support():
    # 1. Marcas do utilizador (para contexto do cliente)
    if current_user.role == 'admin':
        # Visão do Gestor: Fila de Atendimento
        tickets = SupportTicket.query.order_by(SupportTicket.is_unread_admin.desc(), SupportTicket.created_at.desc()).all()
        return render_template('support_admin.html', tickets=tickets)
    else:
        # Visão do Cliente: Pedir Ajuda
        my_brands = Brand.query.filter_by(user_id=current_user.id).all()
        tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.created_at.desc()).all()
        
        # Gestores Online (Ativos nos últimos 15 min)
        limit = datetime.utcnow() - timedelta(minutes=15)
        online_admins = User.query.filter(User.role == 'admin', User.last_active >= limit).all()
        
        return render_template('support.html', brands=my_brands, admins=online_admins, tickets=tickets)

@app.route('/api/create_support_ticket', methods=['POST'])
@login_required
def create_support_ticket():
    data = request.form
    new_ticket = SupportTicket(
        user_id=current_user.id,
        brand_id=data.get('brand_id') if data.get('brand_id') else None,
        assigned_admin_id=data.get('admin_id'),
        subject=data.get('subject', 'Pedido de Assistência'),
        channel=data.get('channel', 'chat'),
        last_message=data.get('message')
    )
    db.session.add(new_ticket)
    
    # Notificar via log de atividade se houver marca
    if new_ticket.brand_id:
        activity = ProcessActivity(
            brand_id=new_ticket.brand_id,
            user_id=current_user.id,
            action='support_requested',
            description=f"Solicitou assistência via {new_ticket.channel.upper()}: {new_ticket.subject}"
        )
        db.session.add(activity)

    db.session.commit()
    flash('Pedido de suporte enviado! Um gestor entrará em contacto em breve.', 'success')
    return redirect(url_for('support'))


@app.route('/api-docs')
def api_docs():
    return render_template('api.html')



@app.route('/property-types')
def property_types():
    # Grid de tipos de propriedade intelectual
    return render_template('property_types.html')


@app.route('/scan-live')
def scan_live_page():
    return render_template('scan_live.html')

@app.route('/api/scan-live', methods=['POST'])
def scan_live_api():
    """Realiza varredura em tempo real (DNS, HTTP Status)"""
    import socket
    import requests
    import time  # <--- FALTAVA ISSO
    
    time.sleep(1) # UX Delay para sensação de processamento

    data = request.json
    term = data.get('term', '').lower().replace(' ', '')
    
    is_auth = current_user.is_authenticated # Checa se está logado
    
    results = {
        'term': term,
        'domains': [], # Se não logado, vai vir vazio ou com flag de oculto
        'social': [],
        'local': [],
        'restricted': not is_auth, # Front saberá se mostra ou esconde
        'counts': {'domains': 0, 'social': 0, 'local': 0} # Contadores para o "Teaser"
    }

    # 0. Verificar Base de Dados Local (Inteligência Interna)
    local_conflicts = []
    # Busca por similaridade simples (contém o termo)
    similar_brands = Brand.query.filter(Brand.name.ilike(f'%{term}%')).all()
    results['counts']['local'] = len(similar_brands)
    
    if is_auth: # Só preenche lista se logado
        for brand in similar_brands:
            local_conflicts.append({
                'name': brand.name,
                'status': brand.status,
                'owner': brand.owner_name
            })
        results['local'] = local_conflicts

    # 1. Verificar Domínios e Variações Comerciais (Inteligência Web)
    variations = [term, f"{term}mz", f"{term}lda", f"loja{term}", f"{term}servicos"]
    tlds = ['.co.mz', '.com']
    
    checked_domains = []
    
    for var in variations:
        for tld in tlds:
            if len(checked_domains) >= 8: break 
            
            domain = f"{var}{tld}"
            status = 'available'
            try:
                socket.gethostbyname(domain)
                status = 'occupied'
            except:
                pass
            
            # Lógica Teaser: Conta tudo, mas só retorna dados se auth OU se for 'disponível' (para não assustar à toa? não, melhor esconder tudo ocupado)
            if status == 'occupied':
                results['counts']['domains'] += 1
                if is_auth:
                    results['domains'].append({'domain': domain, 'status': status})
            elif var == term: # Termo exato disponível mostra pra todos como isca
                 results['domains'].append({'domain': domain, 'status': 'available'})

    # 2. Verificar Redes Sociais
    # ... (mesma lógica) ...


    # 2. Verificar Redes Sociais (HTTP Request Real)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    networks = [
        {'name': 'Instagram', 'url': f'https://www.instagram.com/{term}/'},
        {'name': 'Facebook', 'url': f'https://www.facebook.com/{term}/'},
        {'name': 'LinkedIn', 'url': f'https://www.linkedin.com/company/{term}'},
        {'name': 'YouTube', 'url': f'https://www.youtube.com/@{term}'}
    ]
    
    for net in networks:
        net_status = 'unknown'
        try:
            r = requests.get(net['url'], headers=headers, timeout=2)
            if r.status_code == 200:
                net_status = 'occupied'
            elif r.status_code == 404:
                net_status = 'available'
        except:
            pass
        
        if net_status == 'occupied':
            results['counts']['social'] += 1
            if is_auth:
                 results['social'].append({'network': net['name'], 'url': net['url'], 'status': 'occupied'})
        elif net_status == 'available':
             results['social'].append({'network': net['name'], 'url': net['url'], 'status': 'available'})

    return jsonify(results)


@app.route('/reports')
@login_required
def reports():
    if current_user.role != 'admin':
        flash('Acesso restrito ao gestor.', 'danger')
        return redirect(url_for('dashboard'))

    # Estatísticas Globais
    total_brands = Brand.query.count()
    high_risk = Brand.query.filter_by(risk_level='high').all()
    
    # Verificar última varredura global
    last_scan = SystemConfig.query.get('last_global_scan')
    last_scan_date = last_scan.value if last_scan else 'Nunca realizada'
    
    # Recomendação de Varredura (15 dias)
    needs_scan = True
    if last_scan:
        last_dt = datetime.fromisoformat(last_scan.value)
        days_since = (datetime.now() - last_dt).days
        if days_since < 15:
            needs_scan = False

    return render_template('reports.html', 
                           total=total_brands, 
                           high_risk=high_risk, 
                           last_scan=last_scan_date,
                           needs_scan=needs_scan)

@app.route('/export/<type>')
def export_data(type):
    import csv
    from io import StringIO
    from flask import make_response

    # Preparar dados baseado no tipo
    if type == 'brands':
        filename = 'm24_carteira_marcas.csv'
        data = [['ID', 'Marca', 'Titular', 'Status', 'Risco']]
        items = Brand.query.all()
        for i in items:
            data.append([i.id, i.name, i.owner_name, i.status, i.risk_level])
            
    elif type == 'entities':
        filename = 'm24_titulares.csv'
        data = [['ID', 'Nome', 'NUIT', 'Email', 'País']]
        items = Entity.query.all()
        for i in items:
            data.append([i.id, i.name, i.nuit, i.email, i.country])
    else:
        return redirect(url_for('reports'))

    # Gerar CSV em memória
    si = StringIO()
    cw = csv.writer(si, delimiter=';') # Ponto e vírgula para Excel PT abrir melhor
    cw.writerows(data)
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv; charset=utf-8-sig" # UTF-8 BOM para acentos funcionarem no Excel
    return output


@app.route('/sw.js')
def service_worker():
    return "", 200, {'Content-Type': 'application/javascript'}





import subprocess
import threading

# Configurações do Sistema
SYSTEM_CONFIG = {
    'whatsapp_api_url': 'http://localhost:3002/send'
}

# --- Gestão do Motor WhatsApp (Node.js) ---
# DESATIVADO: Agora usamos o run_system.bat para iniciar o Node externamente
# Isso dá mais controle e visibilidade dos logs para o usuário.
def start_whatsapp_engine():
    pass 

# Iniciar em Thread separada (Desativado)
# threading.Thread(target=start_whatsapp_engine, daemon=True).start()

@app.route('/settings/integrations')
@login_required
def integrations():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    
    # Ler Status e QR Code do disco (Shared Files)
    qr_code = None
    status = 'DISCONNECTED'
    
    try:
        if os.path.exists('static/whatsapp_qr.txt'):
            with open('static/whatsapp_qr.txt', 'r') as f:
                qr_code = f.read()
                
        if os.path.exists('static/whatsapp_status.txt'):
            with open('static/whatsapp_status.txt', 'r') as f:
                status = f.read()
    except:
        pass

    # Buscar logs de email para o painel de controlo
    email_logs = EmailLog.query.order_by(EmailLog.timestamp.desc()).limit(15).all()
    
    return render_template('integrations.html', qr_code=qr_code, status=status, email_logs=email_logs)

@app.route('/api/support/ticket/<int:ticket_id>')
@login_required
def get_ticket_details(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    # Segurança: Apenas Admin ou o Dono do Ticket podem ver
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        return jsonify({'status': 'error', 'details': 'Acesso negado'}), 403
    
    user = User.query.get(ticket.user_id)
    entity = Entity.query.filter_by(email=user.email).first()
    brand = Brand.query.get(ticket.brand_id) if ticket.brand_id else None
    
    return jsonify({
        'id': ticket.id,
        'subject': ticket.subject,
        'channel': ticket.channel,
        'message': ticket.last_message,
        'status': ticket.status,
        'created_at': ticket.created_at.strftime('%d/%m/%Y %H:%M'),
        'user': {
            'name': user.name or user.username,
            'email': user.email,
            'phone': entity.phone if entity else 'N/D'
        },
        'brand': {
            'name': brand.name,
            'process': brand.process_number
        } if brand else None
    })

@app.route('/api/support/reply', methods=['POST'])
@login_required
def support_reply():
    if current_user.role != 'admin':
        return jsonify({'status': 'error'}), 403
    
    data = request.json
    ticket = SupportTicket.query.get(data.get('ticket_id'))
    if not ticket: return jsonify({'status': 'error'}), 404
    
    ticket.status = data.get('status', ticket.status)
    ticket.is_unread_admin = False
    
    # Criar notificação para o cliente
    notif = AppNotification(
        user_id=ticket.user_id,
        title="Atualização de Suporte",
        message=f"O gestor atualizou o seu pedido #{ticket.id} para {ticket.status.upper()}.",
        type='success' if ticket.status == 'closed' else 'info'
    )
    db.session.add(notif)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/api/notifications')
@login_required
def get_notifications():
    notifications = AppNotification.query.filter_by(user_id=current_user.id).order_by(AppNotification.timestamp.desc()).limit(10).all()
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'is_read': n.is_read,
        'timestamp': n.timestamp.strftime('%H:%M - %d/%m')
    } for n in notifications])

@app.route('/api/notifications/mark_read', methods=['POST'])
@login_required
def mark_notifications_read():
    AppNotification.query.filter_by(user_id=current_user.id, is_read=False).update({AppNotification.is_read: True})
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/support/mark_read/<int:ticket_id>', methods=['POST'])
@login_required
def support_mark_read(ticket_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error'}), 403
    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.is_unread_admin = False
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/toggle-whatsapp', methods=['POST'])
@login_required
def toggle_whatsapp():
    # Agora é gerido pelo Node
    return jsonify({'status': 'success'})

@app.route('/api/whatsapp/status')
@login_required
def whatsapp_status():
    status = 'DISCONNECTED'
    qr_code = None
    
    try:
        if os.path.exists('static/whatsapp_status.txt'):
             with open('static/whatsapp_status.txt', 'r') as f:
                status = f.read().strip()
                
        if os.path.exists('static/whatsapp_qr.txt'):
             with open('static/whatsapp_qr.txt', 'r') as f:
                qr_code = f.read().strip()
    except:
        pass
        
    return jsonify({'status': status, 'qr_code': qr_code})


@app.route('/admin/email-audit')
@login_required
def email_audit():
    if current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    logs = EmailLog.query.order_by(EmailLog.timestamp.desc()).limit(100).all()
    return render_template('admin/email_audit.html', logs=logs)

@app.route('/test-email')
@login_required
def test_email():
    if current_user.role != 'admin':
        return "Denied", 403
    try:
        msg = Message(subject="M24 Teste de Conexão", recipients=[current_user.email])
        msg.body = "Se você recebeu isso, o SMTP do m24 está funcionando perfeitamente!"
        mail.send(msg)
        return "Email enviado com sucesso! Verifique sua caixa de entrada."
    except Exception as e:
        return f"Falha no SMTP: {str(e)}"

@app.route('/api/check-entity-exists')
@login_required
def check_entity_exists():
    nuit = request.args.get('nuit')
    email = request.args.get('email')
    
    query = Entity.query
    if nuit:
        query = query.filter(Entity.nuit == nuit)
    elif email:
        query = query.filter(Entity.email == email)
    else:
        return jsonify(None)
        
    entity = query.first()
    if entity:
        return jsonify({
            'id': entity.id,
            'name': entity.name,
            'nuit': entity.nuit,
            'email': entity.email,
            'phone': entity.phone,
            'address': entity.address,
            'city': entity.city,
            'country': entity.country
        })
    return jsonify(None)

@app.route('/api/send-whatsapp', methods=['POST'])
@login_required
def send_whatsapp():
    data = request.json
    msg = data.get('message')
    phone = data.get('target_phone', '258840000000') 
    msg_type = data.get('type', 'text') # 'text' ou 'card'
    
    print(f">>> Routing to Internal Engine (3002)... Type: {msg_type}")
    
    try:
        if msg_type == 'card':
            url = 'http://localhost:3002/send-file'
            # Caminho absoluto para garantir que o Node ache
            card_path = os.path.join(os.getcwd(), 'static', 'm24_card.png')
            
            # Se cartão não existe, criar um dummy ou usar logo
            if not os.path.exists(card_path):
                 print("!!! Cartão não encontrado, enviando texto.")
                 return jsonify({'status': 'error', 'details': 'Imagem do cartão não encontrada em static/m24_card.png'}), 404

            payload = {
                'phone': phone, 
                'filePath': card_path,
                'caption': f"{msg}\n\n(Enviado pela #EncubadoraDeSolucoes)"
            }
        else:
            url = 'http://localhost:3002/send'
            payload = {
                'phone': phone, 
                'message': f"{msg}\n\n(Enviado pela #EncubadoraDeSolucoes)"
            }

        res = requests.post(url, json=payload, timeout=20) # Mais tempo para upload de imagem
        
        if res.status_code == 200:
            return jsonify({'status': 'success', 'gateway_id': 'INTERNAL-ENGINE', 'target': phone})
        else:
            return jsonify({'status': 'error', 'details': res.text}), 500

    except Exception as e:
        print(f"Erro Motor WhatsApp: {e}")
        return jsonify({'status': 'error', 'details': 'Motor WhatsApp Offline (Aguarde inicialização...)'}), 503

@app.route('/api/stats/reports')
@login_required
def report_stats():
    # 1. Distribuição de Riscos
    high = Brand.query.filter_by(risk_level='high').count()
    medium = Brand.query.filter_by(risk_level='medium').count()
    low = Brand.query.filter_by(risk_level='low').count()
    
    # 2. Status dos Processos
    pending = Brand.query.filter_by(status='pending').count()
    registered = Brand.query.filter_by(status='registered').count()
    rejected = Brand.query.filter_by(status='rejected').count()
    
    # 3. Tipos de Propriedade (Simulado para MVP, ideal seria group_by)
    types_dist = {
        'Marcas': Brand.query.filter_by(property_type='marca').count(),
        'Patentes': Brand.query.filter_by(property_type='patente').count(),
        'Logos': Brand.query.filter(Brand.logo_path.isnot(None)).count()
    }

    return jsonify({
        'risks': [high, medium, low],
        'status': [pending, registered, rejected],
        'types': list(types_dist.values()),
        'total_brands': Brand.query.count()
    })

@app.route('/invite_entity/<int:entity_id>')
@login_required
def invite_entity(entity_id):
    if current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
        
    entity = Entity.query.get_or_404(entity_id)
    
    # 1. Verificar/Criar Usuário
    user = User.query.filter_by(email=entity.email).first()
    raw_password = None
    
    if not user:
        raw_password = secrets.token_urlsafe(8)
        user = User(
            username=entity.email,
            email=entity.email,
            role='client',
            name=entity.name
        )
        user.set_password(raw_password)
        db.session.add(user)
        db.session.commit()
    else:
        raw_password = secrets.token_urlsafe(8)
        user.set_password(raw_password)
        db.session.commit()

    # 2. Enviar Notificações
    try:
        credenciais_html = f"<div style='background:#f3f4f6; padding:15px; border-radius:8px; margin:20px 0;'><strong>🔑 As suas Credenciais:</strong><br>Login: {entity.email}<br>Senha: {raw_password}</div>"
        
        def invite_async_task(ent_name, ent_email, pwd_html):
            html = (f"<h2>Bem-vindo ao M24 Brand Guardian</h2>"
                    f"<p>Prezado(a) <strong>{ent_name}</strong>,</p>"
                    f"<p>Sua conta foi regularizada em nosso sistema.</p>"
                    f"<div style='background: #d1fae5; color: #065f46; padding: 15px; border-radius: 8px; border: 1px solid #10b981; margin: 15px 0;'>"
                    f"<strong>🎁 PLANO BETA ATIVADO:</strong><br>"
                    f"Você recebeu acesso completo ao painel de proteção de marcas."
                    f"</div>"
                    f"{pwd_html}"
                    f"<p><a href='http://localhost:7000/login' style='background: #6366f1; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display:inline-block;'>Acessar Painel Agora</a></p>"
                    f"<hr><small>M24 Security | #EncubadoraDeSolucoes</small>")
            send_m24_email(ent_email, "Convite Oficial - M24 Brand Guardian", html)

        threading.Thread(target=invite_async_task, args=(entity.name, entity.email, credenciais_html)).start()

        if entity.phone:
            msg = (f"🔐 *M24 Brand Guardian - Convite de Acesso*\n\n"
                   f"Olá *{entity.name}*,\n"
                   f"Sua conta foi ativada com sucesso.\n\n"
                   f"🔑 Login: {entity.email}\n"
                   f"🔑 Senha: {raw_password}\n\n"
                   f"Acesse agora para proteger suas marcas.\n"
                   f"(Enviado pela #EncubadoraDeSolucoes)")
            
            def send_whats():
                try:
                    requests.post('http://localhost:3002/send', json={'phone': entity.phone, 'message': msg}, timeout=5)
                except: pass
            threading.Thread(target=send_whats).start()

        flash(f'Convite enviado para {entity.name}!', 'success')
        
    except Exception as e:
        flash(f'Erro ao convidar: {e}', 'danger')

    return redirect(url_for('entities'))


# ========== CRIAÇÃO DE DADOS DE TESTE (SEED) ==========
def seed_users():
    """Cria usuários e entidades padrão de forma vinculada"""
    # 1. Admin
    if not User.query.filter_by(role='admin').first():
        admin_user = User(
            username='admin@m24.co.mz',
            email='admin@m24.co.mz',
            role='admin',
            name='Administrador m24',
            account_validated=True
        )
        admin_user.set_password('123456')
        db.session.add(admin_user)
        print(">>> Usuário ADMIN criado: admin@m24.co.mz / 123456")

    # 2. Entidade + Usuário Cliente
    test_email = 'cliente@empresa.co.mz'
    if not Entity.query.filter_by(email=test_email).first():
        # Criar a Entidade primeiro
        test_entity = Entity(
            name='Empresa de Teste, Lda',
            nuit='999888777',
            email=test_email,
            phone='+258 84 000 0000',
            city='Maputo',
            address='Av. Marginal, 123',
            country='Moçambique'
        )
        db.session.add(test_entity)
        
        # Criar o Usuário para esta Entidade
        if not User.query.filter_by(email=test_email).first():
            test_user = User(
                username=test_email,
                email=test_email,
                role='client',
                name='Empresa de Teste, Lda',
                account_validated=True
            )
            test_user.set_password('123456')
            db.session.add(test_user)
            print(f">>> VÍNCULO CRIADO: Entidade e Usuário para {test_email}")

    db.session.commit()

@app.route('/api/entity/action', methods=['POST'])
@login_required
def entity_action():
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'details': 'Acesso negado'}), 403
        
    data = request.json
    entity_id = data.get('entity_id')
    action = data.get('action')
    
    entity = Entity.query.get_or_404(entity_id)
    user = User.query.filter_by(email=entity.email).first()
    
    try:
        if action == 'validate':
            # Reutiliza a lógica de validação
            return send_validation(entity_id)

        elif action == 'card-email':
            # Enviar Cartão de Visita via Email
            def send_card_email_async(ent_id):
                with app.app_context():
                    try:
                        ent = Entity.query.get(ent_id)
                        if not ent: return
                        
                        html = render_template('emails/business_card.html', entity=ent)
                        attachments = []
                        
                        card_path = os.path.join(app.static_folder, 'm24_card.png')
                        if os.path.exists(card_path):
                            with app.open_resource(card_path) as fp:
                                attachments.append({
                                    'filename': 'm24_card.png',
                                    'content_type': 'image/png',
                                    'data': fp.read()
                                })
                        
                        send_m24_email(ent.email, "📇 Cartão de Visita Digital - M24 Pro", html, attachments)
                    except Exception as e:
                        print(f"Erro async card email: {e}")

            threading.Thread(target=send_card_email_async, args=(entity.id,)).start()
            return jsonify({'status': 'success', 'details': 'Cartão enviado para o e-mail.'})

        elif action == 'card-whatsapp':
            # Enviar Cartão via WhatsApp (utilizando o motor node)
            if not entity.phone:
                return jsonify({'status': 'error', 'details': 'Entidade sem número de telefone.'})
            
            payload = {
                'phone': entity.phone,
                'filePath': os.path.join(os.getcwd(), 'static', 'm24_card.png'),
                'caption': f"Olá {entity.name}, aqui está o nosso cartão de visita digital. Estamos à disposição para proteger suas marcas!"
            }
            # URL do motor WhatsApp vinda de env ou default local
            wa_api = os.environ.get('WHATSAPP_API_URL', 'http://localhost:3002')
            try:
                requests.post(f'{wa_api}/send-file', json=payload, timeout=10)
                return jsonify({'status': 'success', 'details': 'Cartão enviado via WhatsApp.'})
            except:
                return jsonify({'status': 'error', 'details': 'Motor WhatsApp offline.'})

        elif action == 'status-update':
            # Notificar Status das Marcas (Email + WA)
            brands = Brand.query.filter_by(owner_email=entity.email).all()
            if not brands:
                return jsonify({'status': 'error', 'details': 'Nenhuma marca encontrada para este titular.'})

            def send_status_notif(app_obj, ent, brands_list):
                with app_obj.app_context():
                    # 1. Email Report
                    try:
                        msg = Message(
                            subject=f"📊 Relatório de Status: {len(brands_list)} Ativos Monitorados",
                            recipients=[ent.email]
                        )
                        msg.html = render_template('emails/status_report.html', entity=ent, brands=brands_list)
                        mail.send(msg)
                    except: pass

                    # 2. WhatsApp Report
                    if ent.phone:
                        wa_msg = f"🔍 *M24 Pro - Atualização de Status*\n\nOlá *{ent.name}*,\n\nAtualmente monitoramos *{len(brands_list)}* ativos seus.\n"
                        for b in brands_list:
                            status_pt = "Registrada" if b.status == 'registered' else "Em Análise"
                            wa_msg += f"\n• *{b.name}*: {status_pt}"
                        # Detectar URL base dinamicamente para o link no WA
                        base_url = request.host_url.rstrip('/')
                        wa_msg += f"\n\nAceda ao painel para detalhes: {base_url}"
                        wa_api = os.environ.get('WHATSAPP_API_URL', 'http://localhost:3002')
                        requests.post(f'{wa_api}/send', json={'phone': ent.phone, 'message': wa_msg}, timeout=5)

            threading.Thread(target=send_status_notif, args=(app, entity, brands)).start()
            return jsonify({'status': 'success', 'details': 'Relatórios de status disparados.'})

    except Exception as e:
        return jsonify({'status': 'error', 'details': str(e)}), 500

    return jsonify({'status': 'error', 'details': 'Ação desconhecida'}), 400

# ========== INICIALIZAÇÃO E ROTAS AUXILIARES ==========
@app.route('/send_validation/<int:entity_id>')
@login_required
def send_validation(entity_id):
    if current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
        
    entity = Entity.query.get_or_404(entity_id)
    user = User.query.filter_by(email=entity.email).first()
    
    if not user:
        # Se não existe usuário, criamos um primeiro
        raw_password = secrets.token_urlsafe(8)
        user = User(username=entity.email, email=entity.email, role='client', name=entity.name)
        user.set_password(raw_password)
        db.session.add(user)
        db.session.commit()
    else:
        # Se já existe, apenas garantimos uma senha para o email de instrução
        raw_password = "sua_senha_atual" # Ou resetamos para garantir

    # Enviar Email de Validação Obrigatória
    try:
        def send_validation_email(app, entity_data, password):
            with app.app_context():
                try:
                    msg = Message(
                        subject="⚠️ AÇÃO NECESSÁRIA: Valide seu Cadastro - M24 Pro",
                        recipients=[entity_data['email']]
                    )
                    # O link de validação deve ser dinâmico para funcionar no servidor
                    base_url = request.host_url.rstrip('/')
                    validation_url = f"{base_url}/confirm_validation/{entity_data['id']}"
                    
                    msg.html = (f"<div style='font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;'>"
                                f"<div style='background: #1e1b4b; padding: 30px; text-align: center;'>"
                                f"<h2 style='color: white; margin: 0;'>M24 Brand Guardian</h2>"
                                f"</div>"
                                f"<div style='padding: 30px;'>"
                                f"<h3>Olá, {entity_data['name']}</h3>"
                                f"<p>Para garantir a segurança jurídica de suas marcas em Moçambique, precisamos que você <strong>valide seus dados de acesso</strong>.</p>"
                                f"<div style='background: #fffbeb; border: 1px solid #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0;'>"
                                f"<strong>🔑 Seus dados de acesso temporário:</strong><br>"
                                f"Login: {entity_data['email']}<br>"
                                f"Senha: {password}"
                                f"</div>"
                                f"<p style='text-align: center; margin-top: 30px;'>"
                                f"<a href='{validation_url}' style='background: #6366f1; color: white; padding: 15px 25px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;'>CONFIRMAR E VALIDAR AGORA</a>"
                                f"</p>"
                                f"<p style='font-size: 0.8rem; color: #6b7280; margin-top: 30px;'>Ao clicar, você confirma a exatidão dos dados e ativa o monitoramento 24h.</p>"
                                f"</div></div>")
                    mail.send(msg)
                    # Log de Sucesso
                    with app.app_context():
                        log = EmailLog(recipient=entity_data['email'], subject=msg.subject, status='sent')
                        db.session.add(log)
                        db.session.commit()
                except Exception as e:
                    print(f"Erro Email Validação: {e}")
                    # Log de Erro
                    with app.app_context():
                        log = EmailLog(recipient=entity_data['email'], subject="Validação de Cadastro", status='error', error_message=str(e))
                        db.session.add(log)
                        db.session.commit()

        threading.Thread(target=send_validation_email, args=(app, {'id': entity.id, 'name': entity.name, 'email': entity.email}, raw_password)).start()
        flash(f'Solicitação de validação enviada para {entity.name}!', 'success')
        return jsonify({'status': 'success', 'details': f'Validado para {entity.name}'})
    except Exception as e:
        flash(f'Erro: {e}', 'danger')
        return jsonify({'status': 'error', 'details': str(e)}), 500

@app.route('/confirm_validation/<int:entity_id>')
def confirm_validation(entity_id):
    entity = Entity.query.get_or_404(entity_id)
    user = User.query.filter_by(email=entity.email).first()
    if user:
        user.account_validated = True
        db.session.commit()
        login_user(user)
        flash('Sua conta foi validada com sucesso! Bem-vindo ao painel.', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        # Tabelas são criadas apenas se não existirem. Dados preservados.
        db.create_all()
        seed_users()
        
        # Inicializar sistema de monitoramento automático
        try:
            from scheduler import init_scheduler
            init_scheduler(app, db)
            print("🤖 Sistema de monitoramento RPI ativado!")
        except Exception as e:
            print(f"⚠️ Scheduler não iniciado: {e}")
        
    app.run(debug=True, use_reloader=False, port=7000)  # use_reloader=False para evitar duplicação de jobs
