import os
import sys
import json
import requests
import subprocess
import threading
import socket
import secrets
import difflib
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

from modules.extensions import db
from modules.real_scanner import (
    scan_live_real, 
    purification_real, 
    verificacao_imagem_real
)

# Suporte para Executável (PyInstaller)
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

def get_persistence_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.abspath(os.path.join(os.path.dirname(sys.executable), relative_path))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

app = Flask(__name__, 
            template_folder=get_resource_path('templates'),
            static_folder=get_resource_path('static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ========== ROTA DE SCAN DIRETO ========== 
@app.route('/scan-marca', methods=['GET', 'POST'])
@login_required
def scan_marca_page():
    resultado = None
    termo = ''
    if request.method == 'POST':
        termo = request.form.get('termo', '').strip()
        if termo:
            resultado = scan_live_real(termo, usuario_logado=True)
    return render_template('scan_marca.html', resultado=resultado, termo=termo)

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

db.init_app(app)

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

# Filtro Jinja2 para JSON
@app.template_filter('from_json')
def from_json_filter(value):
    # DOCSTRING_REMOVED Converte string JSON para dict# DOCSTRING_REMOVED 
    if isinstance(value, str):
        return json.loads(value)
    return value

def send_m24_email(recipient, subject, html_content, attachments=None):
    # DOCSTRING_REMOVED Função unificada de envio de email com auditoria automática.# DOCSTRING_REMOVED 
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
    role = db.Column(db.String(20), default='client') # 'admin', 'client', 'agent'
    name = db.Column(db.String(150)) # Nome de exibição
    account_validated = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    last_active = db.Column(db.DateTime, default=datetime.utcnow) # Para saber quem está online
    
    # Perfil de Agente (Se role == 'agent')
    agent_registration_number = db.Column(db.String(50)) # Nº do Agente Oficial
    agent_bio = db.Column(db.Text)
    
    # Sistema de Assinaturas
    subscription_plan = db.Column(db.String(50), default='free') # 'free', 'starter', 'professional', 'business', 'enterprise', 'agent_pro'
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
    # DOCSTRING_REMOVED Planos de assinatura disponíveis# DOCSTRING_REMOVED 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # 'starter', 'professional', etc
    display_name = db.Column(db.String(100)) # Nome amigável
    price_monthly = db.Column(db.Float) # Preço em MT
    max_brands = db.Column(db.Integer) # Limite de marcas
    features = db.Column(db.Text) # JSON com features incluídas
    is_active = db.Column(db.Boolean, default=True)

class RPIMonitoring(db.Model):
    # DOCSTRING_REMOVED Monitoramento da Revista da Propriedade Industrial# DOCSTRING_REMOVED 
    id = db.Column(db.Integer, primary_key=True)
    rpi_number = db.Column(db.String(20)) # Ex: "RPI 2756"
    publication_date = db.Column(db.Date)
    processed = db.Column(db.Boolean, default=False)
    total_new_marks = db.Column(db.Integer, default=0)
    conflicts_detected = db.Column(db.Integer, default=0)
    data_file = db.Column(db.String(255)) # Caminho para arquivo processado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NiceClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    includes = db.Column(db.Text)
    excludes = db.Column(db.Text)
    type = db.Column(db.String(50)) # 'produto' ou 'serviço'

class BrandConflict(db.Model):
    # DOCSTRING_REMOVED Conflitos detectados entre marcas do cliente e novos pedidos# DOCSTRING_REMOVED 
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

class Payment(db.Model):
    # DOCSTRING_REMOVED Transações de pagamento de assinaturas# DOCSTRING_REMOVED 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_name = db.Column(db.String(50))  # Plano adquirido
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='MZN')
    payment_method = db.Column(db.String(50))  # 'mpesa', 'card', 'transfer'
    
    # Detalhes M-Pesa
    phone_number = db.Column(db.String(20))
    mpesa_transaction_id = db.Column(db.String(100))
    mpesa_conversation_id = db.Column(db.String(100))
    reference = db.Column(db.String(100), unique=True)
    
    # Status
    status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'failed', 'refunded'
    response_code = db.Column(db.String(50))
    response_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relacionamento
    user = db.relationship('User', backref='payments')

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Proprietário Original
    agent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Agente Responsável
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
        # DOCSTRING_REMOVED Gera um número de processo único no formato M24-YYYY-XXX.# DOCSTRING_REMOVED 
        year = datetime.utcnow().year
        # Conta marcas criadas este ano
        count = Brand.query.filter(Brand.submission_date >= datetime(year, 1, 1)).count()
        return f"M24-{year}-{(count + 1):03d}"

# --- MODELO DADOS EXTERNOS (ESPELHO DO BPI) ---
class IpiRecord(db.Model):
    __tablename__ = 'ipi_record'
    id = db.Column(db.Integer, primary_key=True)
    process_number = db.Column(db.String(50), index=True) # Nº do BPI ou L.Nº
    
    # Tipo: 'marca', 'logotipo', 'patente', etc.
    record_type = db.Column(db.String(50)) 
    
    # Status: 'pedido' (Aviso), 'concessao' (Aprovado), 'recusa'
    status = db.Column(db.String(50))
    
    brand_name = db.Column(db.String(300)) # Texto da Marca (se houver)
    applicant_name = db.Column(db.String(300)) # Requerente no BPI
    nice_class = db.Column(db.String(50)) # Classe (01-45)
    
    # Metadados do Boletim
    bulletin_number = db.Column(db.String(20)) # Ex: "170"
    publication_date = db.Column(db.Date) # Data do Boletim
    opposition_deadline = db.Column(db.Date) # Data limite para oposição (Pub + 30d)
    
    # Imagem Extraída
    image_path = db.Column(db.String(300)) # Caminho para o arquivo .png recortado
    
    # Log de Importação
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)

class BpiApplicant(db.Model):
    __tablename__ = 'bpi_applicant'
    id = db.Column(db.Integer, primary_key=True)
    req_id = db.Column(db.String(50), unique=True) # ID único ou nº processo
    name = db.Column(db.String(255), nullable=False)
    suffix = db.Column(db.String(50))     # Lda, SA, etc
    category = db.Column(db.String(100))  # Empresa, Individual, etc
    country = db.Column(db.String(100))
    detected_year = db.Column(db.String(10))
    page = db.Column(db.Integer)          # Página do Boletim
    status = db.Column(db.String(50), default='new') # STATUS_01 to STATUS_09
    
    # Novos Campos para STATUS_09 / Detalhamento BPI
    brand_name = db.Column(db.String(200))
    filing_date = db.Column(db.String(50))
    publication_date_bpi = db.Column(db.String(50))
    nice_class = db.Column(db.String(50))
    observations = db.Column(db.Text)
    next_action = db.Column(db.String(200))
    deadline = db.Column(db.String(50))
    alteration_type = db.Column(db.String(100))
    alteration_details = db.Column(db.Text)
    opposition_deadline = db.Column(db.String(50)) 
    renewal_date = db.Column(db.String(50))        # Data da Renovação Atual
    next_renewal_date = db.Column(db.String(50))   # Data da Próxima Renovação
    appeal_deadline = db.Column(db.String(50))      # Prazo de Recurso (STATUS_04)
    refusal_reason = db.Column(db.Text)             # Motivo da Recusa (STATUS_04)
    renunciation_date = db.Column(db.String(50))    # Data de Renúncia (STATUS_05)
    final_refusal_date = db.Column(db.String(50))  # Data de Recusa Definitiva (STATUS_06)
    expiry_date = db.Column(db.String(50))         # Data de Vencimento (STATUS_07)
    renewal_deadline = db.Column(db.String(50))    # Prazo de Renovação (STATUS_07)
    triple_fee = db.Column(db.String(20))          # Taxa Tripla (STATUS_07)
    definite_expiry_date = db.Column(db.String(50)) # Data de Caducidade Definitiva (STATUS_08)
    grant_date = db.Column(db.String(50))          # Data da Concessão (STATUS_02)
    nationality = db.Column(db.String(100))        # Nacionalidade
    full_address = db.Column(db.Text)              # Endereço Completo
    total_processes = db.Column(db.Integer)        # Total de Processos

    def __repr__(self):
        return f"<BpiApplicant {self.name} - {self.status}>"

class BrandLog(db.Model):
    # MAR-04: Timeline visual com todos os atos do BPI associados à marca.
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    bpi_id = db.Column(db.Integer, db.ForeignKey('ipi_record.id'), nullable=True)
    applicant_record_id = db.Column(db.Integer, db.ForeignKey('bpi_applicant.id'), nullable=True) # Vínculo com atos extraídos
    
    action_type = db.Column(db.String(50)) # 'publicacao', 'concessao', 'renovacao', 'oposicao', 'transmissao', 'anotacao'
    description = db.Column(db.Text)
    bulletin_number = db.Column(db.String(20))
    event_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    brand = db.relationship('Brand', backref=db.backref('logs', lazy=True, order_by="desc(BrandLog.event_date)"))

class Alert(db.Model):
    # ALT-04/05: Notificações internas e histórico.
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=True)
    
    type = db.Column(db.String(20)) # 'CRITICAL', 'MEDIUM', 'INFO'
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('alerts', lazy=True))

class AuditLog(db.Model):
    # SEC-03: Registro de logs de atividades.
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100)) # 'LOGIN', 'DELETE_BRAND', 'UPDATE_STATUS'
    resource = db.Column(db.String(100)) # 'BRAND', 'USER', 'BPI'
    resource_id = db.Column(db.String(50))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    # PRZ-03/04: Gestão de tarefas e prazos.
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending') # 'pending', 'in_progress', 'completed', 'cancelled'
    priority = db.Column(db.String(20), default='medium') # 'high', 'medium', 'low'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    brand = db.relationship('Brand', backref='tasks')
    user = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')

class BrandDocument(db.Model):
    # MAR-02: Upload de documentos associados.
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    
    title = db.Column(db.String(200))
    doc_type = db.Column(db.String(50)) # 'certificado', 'despacho', 'correspondencia'
    file_path = db.Column(db.String(300))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    brand = db.relationship('Brand', backref='documents')

@app.route('/admin/bpi/requerentes')
@login_required
def bpi_applicants_page():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    # Abas de Status
    active_tab = request.args.get('tab', 'STATUS_01')
    search_query = request.args.get('search', '')
    
    query = BpiApplicant.query
    if active_tab != 'all':
        query = query.filter_by(status=active_tab)
        
    if search_query:
        query = query.filter(
            (BpiApplicant.name.ilike(f'%{search_query}%')) |
            (BpiApplicant.brand_name.ilike(f'%{search_query}%')) |
            (BpiApplicant.req_id.ilike(f'%{search_query}%'))
        )
        
    applicants = query.all()
    
    # Contadores para as abas
    stats = {
        'STATUS_01': BpiApplicant.query.filter_by(status='STATUS_01').count(),
        'STATUS_02': BpiApplicant.query.filter_by(status='STATUS_02').count(),
        'STATUS_03': BpiApplicant.query.filter_by(status='STATUS_03').count(),
        'STATUS_04': BpiApplicant.query.filter_by(status='STATUS_04').count(),
        'STATUS_05': BpiApplicant.query.filter_by(status='STATUS_05').count(),
        'STATUS_06': BpiApplicant.query.filter_by(status='STATUS_06').count(),
        'STATUS_07': BpiApplicant.query.filter_by(status='STATUS_07').count(),
        'STATUS_08': BpiApplicant.query.filter_by(status='STATUS_08').count(),
        'STATUS_09': BpiApplicant.query.filter_by(status='STATUS_09').count(),
        'MASTER': BpiApplicant.query.filter_by(status='MASTER').count(),
        'total': BpiApplicant.query.count()
    }
    
    return render_template('admin/bpi_applicants.html', 
                          applicants=applicants, 
                          stats=stats, 
                          active_tab=active_tab)

@app.route('/admin/nice-classification')
@login_required
def nice_classification_page():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    search_query = request.args.get('search', '')
    query = NiceClass.query
    
    if search_query:
        query = query.filter(
            (NiceClass.title.ilike(f'%{search_query}%')) |
            (NiceClass.description.ilike(f'%{search_query}%')) |
            (NiceClass.includes.ilike(f'%{search_query}%')) |
            (NiceClass.excludes.ilike(f'%{search_query}%')) |
            (db.cast(NiceClass.number, db.String).ilike(f'%{search_query}%'))
        )
    
    classes = query.order_by(NiceClass.number.asc()).all()
    return render_template('admin/nice_classification.html', classes=classes)

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
        role = request.form.get('role', 'client') # 'client' ou 'agent'
        new_user = User(
            username=email, # No novo fluxo, login é o email
            email=email, 
            role=role,
            name=name,
            account_validated=False # Necessário validar via email
        )
        
        # Se for agente, pegamos dados extras
        if role == 'agent':
            new_user.agent_registration_number = request.form.get('agent_reg')
            new_user.subscription_plan = request.form.get('plan', 'agent_pro')
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




@app.route('/analysis')
@login_required
def analysis_page():
    """Página de Análise Inteligente IA - separada da listagem de marcas"""
    # Redirecionar para a página de marcas por enquanto
    # TODO: Criar template dedicado para análise inteligente
    return redirect(url_for('index'))

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

@app.route('/agent/dashboard')
@login_required
def agent_dashboard_old():
    """DEPRECATED - Redireciona para novo dashboard unificado"""
    return redirect(url_for('agent_dashboard_new'))

@app.route('/agent/prospecting')
@login_required
def agent_prospecting():
    if current_user.role != 'agent':
        return redirect(url_for('index'))
    
    # Marcas que NÃO têm agente associado (Oportunidades)
    # Mostramos marcas cujos titulares não estão vinculados a agentes
    opportunities = Brand.query.filter(Brand.agent_id == None).order_by(Brand.submission_date.desc()).all()
    
    return render_template('agent/prospecting.html', opportunities=opportunities)

@app.route('/agent/claim/<int:brand_id>', methods=['POST'])
@login_required
def agent_claim_brand(brand_id):
    if current_user.role != 'agent':
        return jsonify({'status': 'error', 'message': 'Acesso negado'}), 403
    
    brand = Brand.query.get_or_404(brand_id)
    if brand.agent_id:
        return jsonify({'status': 'error', 'message': 'Marca já possui agente'}), 400
    
    brand.agent_id = current_user.id
    db.session.commit()
    
    flash(f"Você agora é o agente responsável pela marca {brand.name}!", "success")
    return redirect(url_for('agent_dashboard_new'))


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
            agent_id=request.form.get('agent_id') if request.form.get('agent_id') else None,
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

    # GET: Passar Lista de Entidades e Agentes
    entities = Entity.query.order_by(Entity.name).all()
    agents = User.query.filter_by(role='agent').all()
    return render_template('register.html', entities=entities, agents=agents, nice_dict=NICE_CLASSES_DICT)


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
    # DOCSTRING_REMOVED Realiza varredura completa em todas as marcas (Relatório Global)# DOCSTRING_REMOVED 
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
    # DOCSTRING_REMOVED API para análise rápida (uso público)# DOCSTRING_REMOVED 
    data = request.json
    name = data.get('name', '')
    classes = data.get('classes', [])

    if not name:
        return jsonify({'error': 'Nome da marca é obrigatório'}), 400

    # Análise básica
    analyzer = BrandAnalyzer()
    results = analyzer.quick_analysis(name, classes, db.session, Brand)

    return jsonify(results)


@app.route('/api/brand/<int:brand_id>/conflicts')
@login_required
def get_brand_conflicts(brand_id):
    """API para retornar evidências detalhadas de conflito (com re-scan)"""
    brand = Brand.query.get_or_404(brand_id)
    
    # Executar análise real para obter os dados detalhados
    # Nota: Isso pode ser lento, idealmente cachearíamos o resultado JSON no banco
    # Mas para garantir dados frescos e cumprir o requisito de 'evidências', rodamos agora.
    analyzer = BrandAnalyzer()
    
    try:
        # analyze_brand já retorna a lista detalhada com 'evidence'
        conflicts = analyzer.analyze_brand(brand.id, db.session, Brand)
        
        # Converter para formato serializável
        serializable_conflicts = []
        for c in conflicts:
            # O objeto 'brand' retornado pelo analyzer é um objeto fake/proxy, precisamos extrair os dados
            c_data = {
                'brand': {
                    'name': c['brand'].name,
                    'owner_name': getattr(c['brand'], 'owner_name', 'N/D'),
                    'process_number': getattr(c['brand'], 'process_number', 'N/D')
                },
                'total_risk': c['total_risk'],
                'text_similarity': c['text_similarity'],
                'visual_similarity': c['visual_similarity'],
                'class_overlap': c['class_overlap'],
                'evidence': c.get('evidence', {})
            }
            serializable_conflicts.append(c_data)
            
        return jsonify({'status': 'success', 'conflicts': serializable_conflicts})
        
    except Exception as e:
        print(f"Erro API Conflicts: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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



@app.route('/agents-list')
@login_required
def agents_list():
    """Lista todos os Agentes de Propriedade Industrial (apenas para admin)"""
    if current_user.role != 'admin':
        flash('Acesso negado. Área restrita a administradores.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Buscar todos os usuários com role='agent'
    agents = User.query.filter_by(role='agent').order_by(User.username).all()
    
    # Estatísticas dos agentes
    agents_data = []
    for agent in agents:
        brands_count = Brand.query.filter_by(owner_id=agent.id).count()
        agents_data.append({
            'agent': agent,
            'brands_count': brands_count,
            'subscription': agent.subscription_plan,
            'registration_number': agent.agent_registration_number or 'N/A'
        })
    
    return render_template('agents_list.html', agents_data=agents_data)

@app.route('/dashboard')
@login_required
def dashboard():
    # Redirecionamento inteligente baseado no role
    if current_user.role == 'agent':
        return redirect(url_for('agent_dashboard_new'))
    elif current_user.role == 'client':
        return redirect(url_for('client_dashboard'))
    
    # Lógica baseada no Perfil (Role) - ADMIN
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
        
        # Alertas e Documentos (Admin vê tudo ou apenas os globais - ajustável)
        alerts = Alert.query.order_by(Alert.created_at.desc()).limit(10).all()
        documents = BrandDocument.query.order_by(BrandDocument.uploaded_at.desc()).limit(5).all()
        
        return render_template('dashboard.html', 
                               stats=stats, 
                               recent=recent, 
                               recommendations=recommendations,
                               alerts=alerts,
                               documents=documents)
    
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
        
        # Alertas e Documentos do Cliente
        alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).limit(10).all()
        my_brand_ids = [b.id for b in my_brands.all()]
        documents = BrandDocument.query.filter(BrandDocument.brand_id.in_(my_brand_ids)).order_by(BrandDocument.uploaded_at.desc()).all()
        
        return render_template('dashboard.html', 
                               stats=stats, 
                               recent=recent, 
                               alerts=alerts,
                               documents=documents)

@app.route('/client-dashboard')
@login_required
def client_dashboard():
    """Dashboard exclusivo para Entidades/Clientes - vê apenas suas próprias marcas"""
    if current_user.role != 'client':
        flash('Acesso negado. Esta área é exclusiva para clientes.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Apenas marcas do próprio usuário
    my_brands = Brand.query.filter_by(owner_id=current_user.id)
    
    stats = {
        'total': my_brands.count(),
        'pending': my_brands.filter(Brand.status.in_(['under_study', 'waiting_admin'])).count(),
        'registered': my_brands.filter(Brand.status.in_(['approved', 'monitored'])).count(),
        'high_risk': my_brands.filter_by(risk_level='high').count(),
        'medium_risk': my_brands.filter_by(risk_level='medium').count(),
        'low_risk': my_brands.filter_by(risk_level='low').count(),
        'user_role': current_user.name or current_user.username,
        'subscription_plan': current_user.subscription_plan,
        'max_brands': current_user.max_brands
    }
    
    recent = my_brands.order_by(Brand.submission_date.desc()).limit(5).all()
    
    # Alertas do cliente
    alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).limit(10).all()
    
    # Documentos das marcas do cliente
    my_brand_ids = [b.id for b in my_brands.all()]
    documents = BrandDocument.query.filter(BrandDocument.brand_id.in_(my_brand_ids)).order_by(BrandDocument.uploaded_at.desc()).limit(10).all()
    
    return render_template('client_dashboard.html', 
                           stats=stats, 
                           recent=recent, 
                           alerts=alerts,
                           documents=documents)

@app.route('/agent-dashboard')
@login_required
def agent_dashboard_new():
    """Dashboard exclusivo para Agentes de PI - ferramentas profissionais"""
    if current_user.role != 'agent':
        flash('Acesso negado. Esta área é exclusiva para agentes de propriedade industrial.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Marcas do próprio agente (se tiver)
    my_brands = Brand.query.filter_by(owner_id=current_user.id)
    
    # Clientes do agente (usuários que ele gerencia - implementar relacionamento depois)
    # Por enquanto, mostrar estatísticas básicas
    
    stats = {
        'my_brands': my_brands.count(),
        'clients_count': 0,  # TODO: Implementar relacionamento agente-cliente
        'opportunities': 0,  # TODO: Implementar prospector
        'reports_generated': 0,  # TODO: Implementar contador de relatórios
        'user_role': 'Agente de Propriedade Industrial',
        'agent_number': current_user.agent_registration_number or 'Não informado',
        'subscription_plan': current_user.subscription_plan
    }
    
    recent = my_brands.order_by(Brand.submission_date.desc()).limit(5).all()
    alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.created_at.desc()).limit(10).all()
    
    return render_template('agent_dashboard.html', 
                           stats=stats, 
                           recent=recent, 
                           alerts=alerts)

@app.route('/conflicts')
@login_required
def conflicts():
    # DOCSTRING_REMOVED Página de alertas de conflitos detectados# DOCSTRING_REMOVED 
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
    # DOCSTRING_REMOVED Marca conflito como analisado# DOCSTRING_REMOVED 
    conflict = BrandConflict.query.get_or_404(conflict_id)
    conflict.status = 'reviewed'
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Conflito marcado como analisado'})

@app.route('/api/conflicts/<int:conflict_id>/dismiss', methods=['POST'])
@login_required
def dismiss_conflict(conflict_id):
    # DOCSTRING_REMOVED Marca conflito como resolvido# DOCSTRING_REMOVED 
    conflict = BrandConflict.query.get_or_404(conflict_id)
    conflict.status = 'dismissed'
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Conflito resolvido'})

@app.route('/entities')
@login_required
def entities():
    # Admin e Agentes podem ver a lista de titulares
    if current_user.role not in ['admin', 'agent']:
        flash('Acesso restrito.', 'danger')
        return redirect(url_for('dashboard'))
        
    # Buscar parâmetros de busca
    search_query = request.args.get('search', '')
    
    query = Entity.query
    if search_query:
        query = query.filter(
            (Entity.name.ilike(f'%{search_query}%')) |
            (Entity.nuit.ilike(f'%{search_query}%')) |
            (Entity.email.ilike(f'%{search_query}%')) |
            (Entity.phone.ilike(f'%{search_query}%'))
        )
        
    all_entities = query.all()
    for ent in all_entities:
        ent.brand_count = Brand.query.filter_by(owner_name=ent.name).count()
        
    # Buscar lista de agentes disponíveis
    agents = User.query.filter_by(role='agent').all()
    
    return render_template('entities.html', entities=all_entities, agents=agents)


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

@app.route('/pricing')
@login_required
def pricing():
    # DOCSTRING_REMOVED Página de planos e assinaturas# DOCSTRING_REMOVED 
    import json
    
    # Buscar todos os planos
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price_monthly).all()
    
    # Plano atual do usuário
    current_plan = SubscriptionPlan.query.filter_by(name=current_user.subscription_plan).first()
    if not current_plan:
        # Fallback para plano free
        current_plan = SubscriptionPlan.query.filter_by(name='free').first()
    
    # Contar marcas do usuário
    brands_count = Brand.query.filter_by(user_id=current_user.id).count()
    
    return render_template('pricing.html',
                           plans=plans,
                           current_plan=current_plan,
                           brands_count=brands_count)

@app.route('/api/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    # DOCSTRING_REMOVED API para fazer upgrade de plano com pagamento M-Pesa# DOCSTRING_REMOVED 
    plan_name = request.form.get('plan_name')
    payment_method = request.form.get('payment_method')
    phone_number = request.form.get('phone_number', '')
    
    # Validar plano
    new_plan = SubscriptionPlan.query.filter_by(name=plan_name, is_active=True).first()
    if not new_plan:
        return jsonify({'status': 'error', 'message': 'Plano inválido'}), 400
    
    # Verificar se não é downgrade para free
    if new_plan.name == 'free' and current_user.subscription_plan != 'free':
        return jsonify({'status': 'error', 'message': 'Para cancelar assinatura, contacte o suporte'}), 400
    
    # Plano Free não requer pagamento
    if new_plan.name == 'free':
        current_user.subscription_plan = 'free'
        current_user.max_brands = 5
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Plano Free ativado!'
        })
    
    # Processar pagamento via M-Pesa
    if payment_method == 'mpesa':
        from modules.mpesa_integration import get_mpesa_client, generate_payment_reference
        
        # Validar número de telefone
        if not phone_number:
            return jsonify({'status': 'error', 'message': 'Número de telefone obrigatório para M-Pesa'}), 400
        
        # Gerar referência única
        reference = generate_payment_reference(current_user.id, plan_name)
        
        # Criar registro de pagamento
        payment = Payment(
            user_id=current_user.id,
            plan_name=new_plan.name,
            amount=new_plan.price_monthly,
            currency='MZN',
            payment_method='mpesa',
            phone_number=phone_number,
            reference=reference,
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()
        
        # Iniciar pagamento M-Pesa
        mpesa = get_mpesa_client(use_simulator=True)  # Mudar para False em produção
        result = mpesa.initiate_c2b_payment(
            amount=new_plan.price_monthly,
            phone_number=phone_number,
            reference=reference,
            description=f"M24 PRO - {new_plan.display_name}"
        )
        
        # Atualizar registro de pagamento
        payment.mpesa_transaction_id = result.get('transaction_id')
        payment.mpesa_conversation_id = result.get('conversation_id')
        payment.response_code = result.get('response_code') or result.get('code')
        payment.response_message = result.get('response_desc') or result.get('message')
        
        if result['status'] == 'success':
            # Pagamento bem-sucedido - ativar assinatura
            from datetime import timedelta
            
            payment.status = 'completed'
            payment.completed_at = datetime.utcnow()
            
            current_user.subscription_plan = new_plan.name
            current_user.max_brands = new_plan.max_brands
            current_user.subscription_start = datetime.utcnow()
            current_user.subscription_end = datetime.utcnow() + timedelta(days=30)
            
            db.session.commit()
            
            # Enviar email de confirmação
            try:
                html = render_template('emails/payment_success.html',
                                       user=current_user,
                                       plan=new_plan,
                                       payment=payment)
                send_m24_email(current_user.email,
                               f"✅ Pagamento Confirmado - {new_plan.display_name}",
                               html)
            except:
                pass  # Não falhar se email não enviar
            
            return jsonify({
                'status': 'success',
                'message': f'Pagamento confirmado! Upgrade para {new_plan.display_name} realizado.',
                'transaction_id': payment.mpesa_transaction_id,
                'redirect': url_for('pricing')
            })
        else:
            # Pagamento falhou
            payment.status = 'failed'
            db.session.commit()
            
            return jsonify({
                'status': 'error',
                'message': f"Erro no pagamento: {result.get('message', 'Erro desconhecido')}",
                'code': result.get('code')
            }), 400
    
    elif payment_method == 'card':
        # TODO: Integrar com Stripe ou outro gateway de cartão
        return jsonify({'status': 'error', 'message': 'Pagamento por cartão em breve'}), 501
    
    elif payment_method == 'transfer':
        # Transferência bancária - gerar instruções
        return jsonify({
            'status': 'pending',
            'message': 'Instruções de transferência enviadas por email',
            'instructions': {
                'bank': 'Millennium BIM',
                'account': '0001234567890',
                'amount': new_plan.price_monthly,
                'reference': generate_payment_reference(current_user.id, plan_name)
            }
        })
    
    return jsonify({'status': 'error', 'message': 'Método de pagamento inválido'}), 400

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



@app.route('/reports/generate', methods=['POST'])
@login_required
def generate_report():
    # DOCSTRING_REMOVED Gera relatório PDF da carteira de marcas# DOCSTRING_REMOVED 
    from modules.report_generator import BrandReportGenerator
    
    report_type = request.form.get('type', 'portfolio')
    
    if report_type == 'portfolio':
        # Relatório completo da carteira
        brands = Brand.query.filter_by(user_id=current_user.id).all()
        generator = BrandReportGenerator()
        filepath = generator.generate_brand_portfolio_report(current_user, brands)
        
        return jsonify({
            'status': 'success',
            'message': 'Relatório gerado com sucesso!',
            'download_url': url_for('download_report', filename=os.path.basename(filepath))
        })
    
    elif report_type == 'conflicts':
        # Relatório de conflitos de uma marca específica
        brand_id = request.form.get('brand_id')
        brand = Brand.query.get_or_404(brand_id)
        
        # Verificar permissão
        if brand.user_id != current_user.id and current_user.role != 'admin':
            return jsonify({'status': 'error', 'message': 'Sem permissão'}), 403
        
        conflicts = BrandConflict.query.filter_by(brand_id=brand_id).all()
        generator = BrandReportGenerator()
        filepath = generator.generate_conflict_alert_report(brand, conflicts)
        
        return jsonify({
            'status': 'success',
            'message': 'Relatório de conflitos gerado!',
            'download_url': url_for('download_report', filename=os.path.basename(filepath))
        })
    
    return jsonify({'status': 'error', 'message': 'Tipo de relatório inválido'}), 400

@app.route('/reports/download/<filename>')
@login_required
def download_report(filename):
    # DOCSTRING_REMOVED Download de relatório PDF# DOCSTRING_REMOVED 
    reports_dir = os.path.join(get_persistence_path('uploads'), 'reports')
    return send_from_directory(reports_dir, filename, as_attachment=True)

@app.route('/scan-live')
def scan_live_page():
    return render_template('scan_live.html')

@app.route('/api/scan-live', methods=['POST'])
def scan_live_api():
    try:
        import socket
        import requests
        import time

        print("DEBUG: Iniciando Scan Live v2...")
        time.sleep(1) # Delay UX

        data = request.json
        if not data or 'term' not in data:
             return jsonify({'status': 'error', 'message': 'Termo não fornecido'}), 400
             
        term = data.get('term', '').lower().strip().replace(' ', '')
        if not term:
             return jsonify({'status': 'error', 'message': 'Termo vazio'}), 400

        print(f"DEBUG: Scan para '{term}'")
        
        is_auth = current_user.is_authenticated
        
        results = {
            'term': term,
            'domains': [],
            'social': [],
            'local': [],
            'bpi': [],
            'restricted': not is_auth,
            'counts': {'domains': 0, 'social': 0, 'local': 0, 'bpi': 0}
        }

        # 1. Busca Local (M24 Database)
        try:
            local_recs = Brand.query.filter(Brand.name.ilike(f'%{term}%')).all()
            results['counts']['local'] = len(local_recs)
            if is_auth:
                for b in local_recs:
                    results['local'].append({
                        'name': b.name,
                        'status': b.status,
                        'owner': b.owner_name
                    })
        except Exception as e:
            print(f"DEBUG: Erro Local: {e}")

        # 2. Busca BPI (IpiRecord Database) - COM INTELECTUALIDADE/SIMILARIDADE
        try:
            import difflib
            
            # Otimização Crítica: NÃO carregar tudo (Query.all()) pois causa OOM (Out Of Memory)
            # Buscamos apenas os 500 candidatos mais prováveis via SQL
            bpi_matches = []
            
            # Busca por prefixo ou similaridade parcial no DB
            candidates = IpiRecord.query.filter(
                (IpiRecord.brand_name.ilike(f'%{term}%'))
            ).limit(500).all()
            
            for r in candidates:
                if not r.brand_name: continue
                db_name = r.brand_name.lower().strip()
                similarity = difflib.SequenceMatcher(None, term, db_name).ratio()
                
                # Regra: Se contém o termo OU similaridade > 60%
                if term in db_name or db_name in term or similarity > 0.6:
                    bpi_matches.append(r)

            results['counts']['bpi'] = len(bpi_matches)
            
            # Ordenar por similaridade (aproximação simples) e limitar
            bpi_recs = bpi_matches[:20] 
            
            if is_auth:
                for r in bpi_recs:
                    results['bpi'].append({
                        'process': r.process_number,
                        'brand': r.brand_name,
                        'applicant': r.applicant_name or 'N/A',
                        'status': r.status,
                        'image': getattr(r, 'image_path', None),
                        'source': r.bulletin_number or 'BPI-Oficial'
                    })
        except Exception as e:
             print(f"DEBUG: Erro BPI: {e}")

        # 3. Busca Web (Domínios .co.mz / .com)
        # Nota: Limitado a 5 checks para ser rápido
        domain_checks = [f"{term}.co.mz", f"{term}.com", f"{term}.mz"]
        
        for domain in domain_checks:
            status = 'available'
            try:
                socket.gethostbyname(domain)
                status = 'occupied'
            except:
                pass # Disponível (ou erro de DNS tratado como disponível/falha)
            
            if status == 'occupied':
                results['counts']['domains'] += 1
            
            if is_auth or status == 'available': # Mostra disponíveis como "isca"
                 results['domains'].append({'domain': domain, 'status': status})

        # 4. Busca Social (Status Code Check)
        networks = [
            {'name': 'Instagram', 'url': f'https://www.instagram.com/{term}/'},
            {'name': 'Facebook', 'url': f'https://www.facebook.com/{term}/'}
        ]
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
        
        for net in networks:
            net_status = 'unknown'
            try:
                # Timeout maior e tratamento de erro
                r = requests.get(net['url'], headers=headers, timeout=5)
                if r.status_code == 200:
                    net_status = 'occupied'
                elif r.status_code == 404:
                    net_status = 'available'
                else: 
                    net_status = f'error ({r.status_code})'
            except Exception as e:
                print(f"DEBUG: Erro Social {net['name']}: {e}")
                net_status = 'error (timeout)'
            
            if net_status == 'occupied':
                results['counts']['social'] += 1
                
            if is_auth:
                results['social'].append({'network': net['name'], 'url': net['url'], 'status': net_status})
            elif net_status == 'available':
                 results['social'].append({'network': net['name'], 'url': net['url'], 'status': 'available'})

        return jsonify(results)

    except Exception as e:
        print(f"ERRO CRÍTICO NO SCAN: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'details': str(e)}), 500

    # ... (Resto do código Web) ...


# Rota de Imagem DESATIVADA temporariamente
@app.route('/api/scan-live/image', methods=['POST'])
def scan_live_image_api():
    return jsonify({
        'status': 'error', 
        'details': 'O módulo de Varredura de Logotipo está em manutenção para aprimoramento do algoritmo. Tente novamente em breve.'
    }), 503

# DOCSTRING_REMOVED 
def scan_live_image_api_OLD():
    # ... (Código antigo comentado ou removido) ...

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


# (Código de imagem removido)


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

@app.route('/admin/import-csv')
@login_required
def import_csv_page():
    if current_user.role != 'admin': return redirect(url_for('index'))
    return render_template('admin/import_csv.html')

@app.route('/admin/import-csv/analyze', methods=['POST'])
@login_required
def analyze_csv_structure():
    # Analisa os headers dos CSVs enviados e propõe mapeamento
    if 'brands_file' not in request.files:
        return jsonify({'status': 'error', 'details': 'Ficheiro de marcas obrigatório'}), 400
        
    import pandas as pd # Se disponivel, ou csv puro
    import io
    import csv
    
    # Função Helper de Heurística
    def guess_column(headers, candidates):
        headers_norm = [h.lower().strip().replace(' ', '_') for h in headers]
        for sys_h in candidates:
             if sys_h in headers_norm:
                 return headers[headers_norm.index(sys_h)]
        # Tentativa parcial
        for sys_h in candidates:
            for h in headers_norm:
                if sys_h in h: return headers[headers_norm.index(h)]
        return None

    try:
        # Analisar Concessões/Marcas
        brands_file = request.files['brands_file']
        brands_stream = io.StringIO(brands_file.stream.read().decode("UTF8"), newline=None)
        brands_headers = next(csv.reader(brands_stream))
        
        # Reset stream para uso posterior se necessario (mas aqui so analisamos headers)
        brands_file.stream.seek(0)
        
        mapping_brands = {
            'process_number': guess_column(brands_headers, ['proc_id', 'processo', 'nr_processo', 'numero_processo', 'id']),
            'brand_name': guess_column(brands_headers, ['marca', 'nome_marca', 'denominacao', 'brand', 'texto']),
            'nice_class': guess_column(brands_headers, ['classe', 'nice', 'niche', 'categoria']),
            'applicant_id': guess_column(brands_headers, ['req_id', 'id_requerente', 'requerente_id']), # Se for relacional
            'applicant_name': guess_column(brands_headers, ['requerente', 'titular', 'dono', 'proprietario']), # Se for flat
            'date': guess_column(brands_headers, ['data_concessao', 'data_pedido', 'data_publicacao', 'data'])
        }
        
        mappings = {'brands': mapping_brands}
        
        # Analisar Requerentes (Opcional)
        if 'applicants_file' in request.files and request.files['applicants_file'].filename != '':
            app_file = request.files['applicants_file']
            app_stream = io.StringIO(app_file.stream.read().decode("UTF8"), newline=None)
            app_headers = next(csv.reader(app_stream))
            app_file.stream.seek(0)
            
            mapping_app = {
                'id': guess_column(app_headers, ['req_id', 'id', 'codigo']),
                'name': guess_column(app_headers, ['req_nome', 'nome', 'empresa', 'designacao'])
            }
            mappings['applicants'] = mapping_app

        return jsonify({'status': 'success', 'mappings': mappings})

    except Exception as e:
        return jsonify({'status': 'error', 'details': str(e)}), 500

@app.route('/admin/import-csv/execute', methods=['POST'])
@login_required
def execute_csv_import():
    try:
        source_name = request.form.get('source_name', 'IMPORT-MANUAL')
        
        # Recalcular mapeamento (ou confiar no frontend? Vamos recalcular para ser stateless seguro)
        # O ideal seria o front mandar o mapeamento aprovado, mas vamos simplificar re-analisando
        # Assumindo que a analise anterior foi aceita.
        
        # 1. Carregar Requerentes (se houver)
        applicants_map = {}
        if 'applicants_file' in request.files and request.files['applicants_file'].filename != '':
            f = request.files['applicants_file']
            stream = io.StringIO(f.stream.read().decode("utf-8"), newline=None)
            reader = csv.DictReader(stream)
            
            # Detectar colunas de chave e valor
            headers = reader.fieldnames
            id_col = next((h for h in headers if h.lower() in ['req_id', 'id', 'codigo']), None)
            name_col = next((h for h in headers if h.lower() in ['req_nome', 'nome', 'empresa']), None)
            
            if id_col and name_col:
                for row in reader:
                    applicants_map[row[id_col]] = row[name_col]

        # 2. Importar Marcas
        f_brands = request.files['brands_file']
        stream_brands = io.StringIO(f_brands.stream.read().decode("utf-8"), newline=None)
        reader_brands = csv.DictReader(stream_brands)
        headers_brands = reader_brands.fieldnames
        
        # Mapeamento dinâmico again
        def find_col(candidates):
            for c in candidates:
                for h in headers_brands:
                    if c in h.lower(): return h
            return None

        col_proc = find_col(['proc_id', 'processo', 'id'])
        col_name = find_col(['marca', 'brand', 'denominacao'])
        col_class = find_col(['classe', 'nice'])
        col_req_id = find_col(['req_id', 'id_requerente']) # Link
        col_req_name = find_col(['requerente', 'titular']) # Flat column
        col_date = find_col(['data', 'date'])

        count = 0
        from datetime import datetime
        
        for row in reader_brands:
            try:
                # Resolver Requerente
                app_name = "Desconhecido"
                if col_req_id and row.get(col_req_id) in applicants_map:
                    app_name = applicants_map[row[col_req_id]]
                elif col_req_name and row.get(col_req_name):
                    app_name = row[col_req_name]
                
                # Resolver Data
                dt_obj = None
                if col_date and row.get(col_date):
                    try:
                        dt_obj = datetime.strptime(row[col_date], '%d/%m/%Y').date()
                    except: pass
                
                # Criar Registro
                rec = IpiRecord(
                    process_number=row.get(col_proc, f"UNK-{count}"),
                    record_type='marca',
                    status='concessao', # Default para import manual
                    brand_name=row.get(col_name, '[Sem Nome]')[:250],
                    applicant_name=app_name[:250],
                    nice_class=row.get(col_class, '0'),
                    publication_date=dt_obj,
                    bulletin_number=source_name
                )
                db.session.add(rec)
                count += 1
            except Exception as e:
                print(f"Skipped row: {e}")
                
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Importação concluída', 'count': count})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'details': str(e)}), 500

# ========== CRIAÇÃO DE DADOS DE TESTE (SEED) ==========
def seed_users():
    # Cria usuários e entidades padrão de forma vinculada
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

@app.route('/admin/upload-bpi', methods=['POST'])
@login_required
def upload_bpi():
    if current_user.role != 'admin':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    
    if 'bpi_file' not in request.files:
        flash('Nenhum arquivo enviado.', 'warning')
        return redirect(url_for('dashboard'))
        
    file = request.files['bpi_file']
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'warning')
        return redirect(url_for('dashboard'))
        
    if file and file.filename.lower().endswith('.pdf'):
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        # Salvar temp
        save_path = os.path.join(app.root_path, filename)
        file.save(save_path)
        
        # Processar em Thread separada para não travar
        try:
            from modules.bpi_importer import BPIImporter
            
            # Função wrapper para rodar com contexto
            def run_import_async(app_obj, path):
                with app_obj.app_context():
                    try:
                        importer = BPIImporter(path)
                        importer.run()
                    except Exception as e:
                        print(f"Erro na thread de importação: {e}")
                    finally:
                        # Opcional: remover arquivo depois
                        try:
                            if os.path.exists(path):
                                os.remove(path)
                        except:
                            pass
            
            # Usar _get_current_object() para passar o app real para a thread
            threading.Thread(target=run_import_async, args=(app._get_current_object(), save_path)).start()
            
            flash(f'Iniciado processamento de {filename}. Você receberá os dados em alguns minutos.', 'success')
        except Exception as e:
            flash(f'Erro ao iniciar importação: {e}', 'danger')
    else:
        flash('Apenas arquivos PDF são permitidos.', 'danger')
        
    return redirect(url_for('dashboard'))

@app.route('/admin/ipi-data')
@login_required
def ipi_data():
    if current_user.role != 'admin':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Filtros
    filter_type = request.args.get('type')
    filter_status = request.args.get('status')
    search_query = request.args.get('q', '')
    
    records = []
    
    # Se o status for um dos STATUS_01-09, buscamos em BpiApplicant
    if filter_status and filter_status.startswith('STATUS_'):
        query = BpiApplicant.query.filter_by(status=filter_status)
        if search_query:
            query = query.filter(
                (BpiApplicant.name.ilike(f'%{search_query}%')) |
                (BpiApplicant.brand_name.ilike(f'%{search_query}%')) |
                (BpiApplicant.req_id.ilike(f'%{search_query}%'))
            )
        
        results = query.order_by(BpiApplicant.id.desc()).all()
        for r in results:
            records.append({
                'process_number': r.req_id,
                'brand_name': r.brand_name or '[Marca de Texto]',
                'applicant_name': r.name,
                'record_type': 'marca',
                'status': r.status,
                'publication_date': r.publication_date_bpi or '2023-06',
                'bulletin_number': '170 (Junho)',
                'image_path': None
            })
    else:
        # Busca padrão em IpiRecord
        query = IpiRecord.query
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                (IpiRecord.brand_name.ilike(search_term)) |
                (IpiRecord.applicant_name.ilike(search_term)) |
                (IpiRecord.process_number.ilike(search_term))
            )

        if filter_type:
            query = query.filter_by(record_type=filter_type)
        if filter_status:
            query = query.filter_by(status=filter_status)
    
        results = query.order_by(IpiRecord.imported_at.desc()).limit(100).all()
        for r in results:
            records.append({
                'process_number': r.process_number,
                'brand_name': r.brand_name,
                'applicant_name': r.applicant_name,
                'record_type': r.record_type,
                'status': r.status,
                'publication_date': r.publication_date,
                'bulletin_number': r.bulletin_number,
                'image_path': r.image_path
            })
    
    return render_template('admin/ipi_data.html', records=records, active_tag='ipi')

# ========== MÓDULO PURIFICAÇÃO (GLOBAL CHECK) ==========
PURIFICATION_STATE = {
    'running': False,
    'progress': 0,
    'current_brand': '',
    'conflicts': [],
    'complete': False
}

@app.route('/admin/purification')
@login_required
def purification_page():
    if current_user.role != 'admin': 
        return redirect(url_for('index'))
    return render_template('admin/purification.html')

@app.route('/api/purification/start', methods=['POST'])
@login_required
def start_purification():
    global PURIFICATION_STATE
    PURIFICATION_STATE = {
        'running': True, 
        'progress': 0, 
        'current_brand': '', 
        'conflicts': [], 
        'complete': False
    }
    
    import threading
    thread = threading.Thread(target=run_purification_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/api/purification/status')
@login_required
def status_purification():
    return jsonify(PURIFICATION_STATE)

def run_purification_job():
    global PURIFICATION_STATE
    import time
    import socket # NECESSÁRIO PARA DNS CHECK
    from sqlalchemy import or_
    
    with app.app_context():
        try:
            brands = Brand.query.all()
            total = len(brands)
            
            if total == 0:
                PURIFICATION_STATE['complete'] = True
                PURIFICATION_STATE['running'] = False
                return

            processed = 0
            
            for brand in brands:
                if not PURIFICATION_STATE['running']:
                    break
                    
                PURIFICATION_STATE['current_brand'] = f"[M24] Verificando {brand.name}..."
                
                # FASE 1: Proteção de Cliente (M24 vs BPI)
                # Verifica se a marca do cliente sofre ameaça no BPI
                
                # Comparar contra TODO o BPI em memória (Mais preciso que SQL LIKE)
                client_clean = brand.name.lower().strip().replace(' ', '')
                
                # Carregar BPI se vazio (otimização)
                if not 'bpi_cache' in locals():
                    bpi_cache = IpiRecord.query.all()

                for bpi_record in bpi_cache:
                    bpi_clean = bpi_record.brand_name.lower().strip().replace(' ', '')
                    
                    similarity = difflib.SequenceMatcher(None, client_clean, bpi_clean).ratio()
                    
                    if similarity > 0.95:
                         # Marca Idêntica = Provável Registro do Próprio Cliente.
                         # Não é conflito negativo.
                         pass
                    elif similarity > 0.70:
                         # Marca Parecida = Ameaça Real
                         conflict_text = f"Conflito de Similaridade ({int(similarity*100)}%) com '{bpi_record.brand_name}' (BPI)."
                         PURIFICATION_STATE['conflicts'].append({
                            'brand': brand.name,
                            'issue': conflict_text,
                            'source': 'Ameaça no IPI',
                            'risk_score': similarity
                         })
                         
                         # Notificar cliente (futuro)
                
                processed += 1
                PURIFICATION_STATE['progress'] = int((processed / total) * 100)
                time.sleep(0.2) 

            # FASE 2: PROSPECÇÃO BPI (Gerar Leads)
            # Analisa marcas do BPI que NÃO são clientes para achar falhas de proteção
            bpi_records = IpiRecord.query.all()
            total_bpi = len(bpi_records)
            
            for i, record in enumerate(bpi_records):
                if not PURIFICATION_STATE['running']: break
                
                # Ignorar se já é cliente nossa
                is_client = Brand.query.filter(Brand.name.ilike(record.brand_name)).first()
                if is_client: continue

                PURIFICATION_STATE['current_brand'] = f"[Auditoria] {record.brand_name}"
                
                # === MOTOR DE RISCO JURÍDICO (BRAND PROTECTION CORE) ===
                
                clean_name = record.brand_name.lower().strip().replace(' ', '')
                
                # 1. DETECÇÃO DE CYBERSQUATTING (USO INDEVIDO NA WEB)
                # Procura por variações que visam enganar (Typosquatting) ou uso direto
                # Ex: marca "utec" -> procura "utecc.co.mz", "utec-moz.com", "utec.co.mz"
                target_domains = [
                    f"{clean_name}.co.mz",      # Exato
                    f"{clean_name}.com",        # Exato Global
                    f"{clean_name}c.co.mz",     # Typo comum (phonetic duplication)
                    f"{clean_name}mz.co.mz"     # Variação local
                ]
                
                import socket
                import difflib
                
                for domain in target_domains:
                    is_active = False
                    try:
                        socket.gethostbyname(domain)
                        is_active = True
                    except:
                        pass
                    
                    if is_active:
                        # Se está ativo, calculamos o RISCO de ser uma violação
                        # (Neste caso, assumimos alto risco pois o nome é base da marca)
                        risk_score = difflib.SequenceMatcher(None, clean_name, domain.split('.')[0]).ratio()
                        
                        if risk_score > 0.75: # 75% de similaridade no radical
                            PURIFICATION_STATE['conflicts'].append({
                               'brand': record.brand_name,
                               'issue': f"ATIVO: '{domain}'. Potencial Cybersquatting.",
                               'source': 'Risco DIGITAL (Web)',
                               'risk_score': risk_score,
                               'applicant': record.applicant_name or 'N/A'
                            })

                # 3. DETECÇÃO DE USO INDEVIDO EM REDES SOCIAIS (SOCIAL SQUATTING)
                networks = [
                    {'name': 'Instagram', 'url': f'https://www.instagram.com/{clean_name}/'},
                    {'name': 'Facebook', 'url': f'https://www.facebook.com/{clean_name}/'}
                ]
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
                
                for net in networks:
                    try:
                        r = requests.get(net['url'], headers=headers, timeout=3)
                        if r.status_code == 200:
                            PURIFICATION_STATE['conflicts'].append({
                                'brand': record.brand_name,
                                'issue': f"CONTA ATIVA: @{clean_name} no {net['name']}. Risco de Impostor.",
                                'source': 'Risco SOCIAL',
                                'risk_score': 0.90,
                                'applicant': record.applicant_name or 'N/A'
                            })
                    except:
                        pass

                # 2. DETECÇÃO DE COLISÃO DE MARCAS (BPI vs BPI)
                # Verifica se existem marcas diferentes registradas que são foneticamente idênticas
                for other in bpi_records:
                    if other.id == record.id: continue
                    
                    other_clean = other.brand_name.lower().strip().replace(' ', '')
                    
                    # IGNORAR AUTO-CORRESPONDÊNCIA (Nome igual não é conflito, é duplicidade ou mesma empresa)
                    if clean_name == other_clean: continue

                    # Cálculo de Similaridade (Confundibilidade)
                    similarity = difflib.SequenceMatcher(None, clean_name, other_clean).ratio()
                    
                    # Se for > 80% similar, há risco de confusão no mercado
                    if similarity > 0.80:
                         conflict_text = f"Marca similar '{other.brand_name}' ({int(similarity*100)}%) detectada no BPI."
                         PURIFICATION_STATE['conflicts'].append({
                            'brand': record.brand_name,
                            'issue': conflict_text,
                            'source': 'Conflito de Registro (Colisão)',
                            'risk_score': similarity,
                            'applicant': record.applicant_name or 'N/A'
                         })
                         break # Registra 1 conflito e segue para não duplicar alertas

                time.sleep(0.05)

            db.session.commit()
            
        except Exception as e:
            print(f"Erro na purificação: {e}")
        finally:
            PURIFICATION_STATE['running'] = False
            PURIFICATION_STATE['complete'] = True
            PURIFICATION_STATE['progress'] = 100

# ==========================================
# ROTAS DE INTELIGÊNCIA REAL (BPI + DNS + LOCAL)
# ==========================================

@app.route('/api/scan-live-real', methods=['POST'])
def api_scan_live_real():
    """Rota para Scan Live real (Substitui a versão simulada)"""
    try:
        data = request.get_json()
        if not data:
            data = request.form
        
        termo = data.get('termo', '').strip()
        
        if not termo or len(termo) < 2:
            return jsonify({
                'error': 'Termo inválido (mínimo 2 caracteres)'
            }), 400
        
        usuario_logado = current_user.is_authenticated
        
        # Executa scan HONESTO
        resultados = scan_live_real(termo, usuario_logado)
        
        # Log da consulta (Apenas para auditoria)
        if usuario_logado and current_user.role == 'admin':
            log = AuditLog(
                user_id=current_user.id,
                action='SCAN_LIVE_REAL',
                resource='BRAND',
                resource_id=termo[:50],
                details=f"Scan live realizado: {termo}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        
        # Debug: Log what we're returning
        print(f"[API DEBUG] usuario_logado={usuario_logado}")
        print(f"[API DEBUG] BPI results count: {len(resultados.get('bpi', []))}")
        if 'resumo_bpi' in resultados:
            print(f"[API DEBUG] resumo_bpi: {resultados['resumo_bpi']}")
        
        response_payload = {
            'status': 'sucesso',
            'resultados': resultados
        }

        # Debug leve para admin (ajuda a validar termo e BPI no UI)
        if usuario_logado and current_user.role == 'admin':
            try:
                from sqlalchemy import or_

                termo_original = termo.strip()
                termo_limpo = ''.join([c for c in termo_original.lower() if c.isalnum()])
                busca_sql = IpiRecord.query.filter(
                    or_(
                        IpiRecord.brand_name.ilike(f'%{termo_original}%'),
                        IpiRecord.brand_name.ilike(f'%{termo_limpo}%')
                    )
                ).limit(5).all()

                response_payload['debug'] = {
                    'termo': termo,
                    'bpi_count': len(resultados.get('bpi', [])),
                    'sql_count': len(busca_sql),
                    'sql_sample': [
                        {
                            'id': r.id,
                            'brand_name': r.brand_name,
                            'process_number': r.process_number
                        } for r in busca_sql
                    ],
                    'limites': resultados.get('limites', [])
                }
            except Exception as e:
                response_payload['debug'] = {
                    'termo': termo,
                    'bpi_count': len(resultados.get('bpi', [])),
                    'debug_error': str(e)[:120]
                }

        return jsonify(response_payload)
        
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500

@app.route('/api/purification-real', methods=['POST'])
@login_required
def api_purification_real():
    """Auditoria interna real (Admin Only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Executa em thread separada para não travar a UI
        thread = threading.Thread(target=run_purification_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'iniciado',
            'mensagem': 'Auditoria profunda iniciada em background.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_purification_background():
    """Helper para rodar purification em background"""
    with app.app_context():
        try:
            resultados = purification_real()
            
            # Salva resultado no banco
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"purification_{timestamp}.json"
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(resultados, f, ensure_ascii=False, indent=2)
            
            # Atualiza config
            config = SystemConfig.query.get('ultima_purificacao')
            if not config:
                config = SystemConfig(key='ultima_purificacao')
                db.session.add(config)
            
            config.value = json.dumps({
                'timestamp': timestamp,
                'conflitos': resultados.get('estatisticas', {}).get('conflitos_detectados', 0),
                'arquivo': filename
            })
            db.session.commit()
            print(f"✅ Purification concluído e salvo em {filename}")
            
        except Exception as e:
            print(f"❌ Erro no Purification Background: {e}")

@app.route('/api/verificacao-imagem-real', methods=['POST'])
@login_required
def api_verificacao_imagem_real():
    """Rota para verificação visual real"""
    try:
        marca_nome = request.form.get('marca', '').strip()
        imagem = request.files.get('imagem')
        
        if not imagem:
            return jsonify({'error': 'Nenhuma imagem fornecida'}), 400
        
        # Salva temporariamente
        filename = secure_filename(f"temp_{uuid.uuid4().hex[:8]}.png")
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imagem.save(temp_path)
        
        try:
            # Executa análise real
            resultados = verificacao_imagem_real(temp_path, marca_nome)
            return jsonify({'status': 'sucesso', 'resultados': resultados})
            
        finally:
            # Limpa lixo
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/visual-check')
@login_required
def visual_check_page():
    return render_template('visual_check.html')

@app.route('/test-visual-simple')
def test_visual_simple():
    """Página de teste simplificada SEM login necessário"""
    from flask import render_template_string
    html = open('test_visual_simple.html', 'r', encoding='utf-8').read() if os.path.exists('test_visual_simple.html') else '''
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>TESTE</title>
<style>body{font-family:monospace;padding:20px;background:#1a1a1a;color:#fff}
.box{border:2px solid #0f0;padding:20px;margin:20px 0;background:#2a2a2a}
.error{color:#f00}.success{color:#0f0}.warning{color:#fa0}
button{padding:10px 20px;font-size:16px;cursor:pointer;background:#0f0;border:none;color:#000}
pre{background:#000;padding:10px;overflow-x:auto;font-size:11px}</style>
</head><body>
<h1>🧪 TESTE VISUAL CHECK</h1>
<div class="box"><h2>Upload</h2>
<input type="file" id="f" accept="image/*"><p id="fi" class="warning">Nenhum arquivo</p></div>
<div class="box"><button onclick="test()">🚀 TESTAR</button><p id="st">Aguardando...</p></div>
<div class="box"><h2>Resposta</h2><pre id="resp">...</pre></div>
<div class="box"><h2>Conflitos</h2><div id="conf"></div></div>
<script>
f.onchange=e=>{const fi=e.target.files[0];if(fi){document.getElementById('fi').textContent=fi.name;document.getElementById('fi').className='success'}}
async function test(){
const file=f.files[0];if(!file){alert('Selecione imagem!');return}
document.getElementById('st').textContent='Enviando...';
const fd=new FormData();fd.append('imagem',file);fd.append('marca','TEST');
try{
const r=await fetch('/api/verificacao-imagem-real',{method:'POST',body:fd});
const d=await r.json();
document.getElementById('resp').textContent=JSON.stringify(d,null,2);
document.getElementById('st').textContent='Concluído!';document.getElementById('st').className='success';
const cv=d.resultados?.conflitos_visuais||[];
document.getElementById('conf').innerHTML=cv.length?cv.map((c,i)=>`<div style="border:2px solid red;padding:10px;margin:5px"><b>${c.marca_bpi}</b>: ${c.similaridade_media}%</div>`).join(''):'Nenhum';
}catch(e){document.getElementById('st').textContent='ERRO:'+e;document.getElementById('st').className='error'}
}
</script></body></html>'''
    return render_template_string(html)

@app.route('/api/purification-resultados')
@login_required
def api_purification_resultados():
    """Consulta último relatório de auditoria"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Busca config
        config = SystemConfig.query.get('ultima_purificacao')
        if not config or not config.value:
             return jsonify({'status': 'nenhum_resultado'})
             
        dados = json.loads(config.value)
        arquivo = dados.get('arquivo')
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], arquivo)
        
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                resultados = json.load(f)
            return jsonify({'status': 'disponivel', 'resultados': resultados})
            
        return jsonify({'status': 'erro', 'mensagem': 'Arquivo de relatório não encontrado'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_users()
    port = int(os.environ.get('PORT', 7000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)
