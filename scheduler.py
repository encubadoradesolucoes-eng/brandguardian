"""
Sistema de Jobs Agendados para Monitoramento RPI
Executa tarefas automáticas semanalmente
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os

# Importar após inicialização do app
scheduler = None

def init_scheduler(app, db):
    """Inicializa o agendador de tarefas"""
    global scheduler
    scheduler = BackgroundScheduler()
    
    # Job semanal: Terças-feiras às 10:00 (quando sai a RPI)
    scheduler.add_job(
        func=lambda: check_new_rpi(app, db),
        trigger=CronTrigger(day_of_week='tue', hour=10, minute=0),
        id='rpi_weekly_check',
        name='Verificação Semanal RPI',
        replace_existing=True
    )
    
    # Job diário: Verificar status de processos
    scheduler.add_job(
        func=lambda: update_process_status(app, db),
        trigger=CronTrigger(hour=8, minute=0),
        id='process_status_daily',
        name='Atualização Diária de Status',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Scheduler iniciado com sucesso!")
    return scheduler


def check_new_rpi(app, db):
    """Job: Verifica se há nova RPI e processa"""
    with app.app_context():
        from modules.rpi_scraper import RPIScraper
        from app import RPIMonitoring, Brand, BrandConflict, User
        
        print(f"[{datetime.now()}] Iniciando verificação de nova RPI...")
        
        scraper = RPIScraper()
        rpi_info = scraper.get_latest_rpi()
        
        if rpi_info['status'] == 'found':
            rpi_number = rpi_info['rpi_number']
            
            # Verificar se já foi processada
            existing = RPIMonitoring.query.filter_by(rpi_number=rpi_number).first()
            if existing:
                print(f"RPI {rpi_number} já foi processada anteriormente.")
                return
            
            # Criar registro de monitoramento
            rpi_record = RPIMonitoring(
                rpi_number=rpi_number,
                publication_date=rpi_info['publication_date'],
                processed=False
            )
            db.session.add(rpi_record)
            db.session.commit()
            
            # Download e processamento do PDF
            pdf_path = os.path.join('uploads', 'rpi', f"{rpi_number.replace(' ', '_')}.pdf")
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            
            if scraper.download_rpi_pdf(rpi_info['pdf_url'], pdf_path):
                print(f"PDF da {rpi_number} baixado com sucesso!")
                
                # Converter PDF para texto e parsear
                from modules.rpi_scraper import pdf_to_text
                text_content = pdf_to_text(pdf_path)
                
                if text_content:
                    new_marks = scraper.parse_rpi_text(text_content)
                    rpi_record.total_new_marks = len(new_marks)
                    
                    # Detectar conflitos com marcas dos clientes
                    all_brands = Brand.query.all()
                    conflicts = scraper.detect_conflicts(new_marks, all_brands)
                    
                    # Salvar conflitos detectados
                    for conflict in conflicts:
                        brand_conflict = BrandConflict(
                            brand_id=conflict['brand_id'],
                            rpi_id=rpi_record.id,
                            conflicting_mark_name=conflict['conflicting_mark'],
                            conflicting_mark_number=conflict['conflicting_number'],
                            similarity_score=conflict['similarity_score'],
                            conflict_type=conflict['conflict_type']
                        )
                        db.session.add(brand_conflict)
                    
                    rpi_record.conflicts_detected = len(conflicts)
                    rpi_record.processed = True
                    rpi_record.data_file = pdf_path
                    db.session.commit()
                    
                    print(f"✅ {len(conflicts)} conflitos detectados!")
                    
                    # Notificar clientes afetados
                    notify_conflicts(app, db, conflicts)
                else:
                    print("⚠️ Falha ao extrair texto do PDF")
            else:
                print("❌ Falha ao baixar PDF da RPI")
        else:
            print(f"Nenhuma nova RPI encontrada: {rpi_info.get('message', '')}")


def update_process_status(app, db):
    """Job: Atualiza status de processos INPI"""
    with app.app_context():
        from modules.rpi_scraper import RPIScraper
        from app import Brand
        
        print(f"[{datetime.now()}] Atualizando status de processos...")
        
        scraper = RPIScraper()
        brands_with_process = Brand.query.filter(Brand.process_number.isnot(None)).all()
        
        updated_count = 0
        for brand in brands_with_process:
            status_info = scraper.get_process_status(brand.process_number)
            
            # Atualizar se houver mudança
            if status_info and status_info['status'] != brand.status:
                old_status = brand.status
                brand.status = status_info['status']
                db.session.commit()
                
                # Notificar cliente sobre mudança de status
                notify_status_change(app, brand, old_status, status_info['status'])
                updated_count += 1
        
        print(f"✅ {updated_count} processos atualizados")


def notify_conflicts(app, db, conflicts):
    """Notifica clientes sobre conflitos detectados"""
    with app.app_context():
        from app import Brand, Entity, send_m24_email
        from flask import render_template
        
        # Agrupar conflitos por marca/cliente
        conflicts_by_brand = {}
        for conflict in conflicts:
            brand_id = conflict['brand_id']
            if brand_id not in conflicts_by_brand:
                conflicts_by_brand[brand_id] = []
            conflicts_by_brand[brand_id].append(conflict)
        
        # Enviar notificações
        for brand_id, brand_conflicts in conflicts_by_brand.items():
            brand = Brand.query.get(brand_id)
            if brand and brand.entity_id:
                entity = Entity.query.get(brand.entity_id)
                if entity and entity.email:
                    # Renderizar template de email
                    html = render_template('emails/conflict_alert.html',
                                           brand=brand,
                                           conflicts=brand_conflicts,
                                           total=len(brand_conflicts))
                    
                    subject = f"⚠️ Alerta: {len(brand_conflicts)} possível(is) conflito(s) detectado(s) para '{brand.name}'"
                    send_m24_email(entity.email, subject, html)
                    
                    print(f"📧 Notificação enviada para {entity.email}")


def notify_status_change(app, brand, old_status, new_status):
    """Notifica cliente sobre mudança de status do processo"""
    with app.app_context():
        from app import Entity, send_m24_email
        from flask import render_template
        
        if brand.entity_id:
            entity = Entity.query.get(brand.entity_id)
            if entity and entity.email:
                html = render_template('emails/status_update.html',
                                       brand=brand,
                                       old_status=old_status,
                                       new_status=new_status)
                
                subject = f"📋 Atualização: Processo {brand.process_number} - {brand.name}"
                send_m24_email(entity.email, subject, html)
