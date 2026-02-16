
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, EmailLog

with app.app_context():
    logs = EmailLog.query.order_by(EmailLog.timestamp.desc()).limit(10).all()
    print("="*50)
    print("ULTIMOS LOGS DE EMAIL")
    print("="*50)
    for log in logs:
        print(f"Data: {log.timestamp}")
        print(f"Destinatário: {log.recipient}")
        print(f"Assunto: {log.subject}")
        print(f"Status: {log.status}")
        if log.status == 'error':
            print(f"Erro: {log.error_message}")
        print("-" * 30)
