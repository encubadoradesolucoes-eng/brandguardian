
import os
from app import app, db, Brand, BrandLog
from modules.process_manager import M24ProcessManager
from datetime import datetime

def test_process_lifecycle():
    with app.app_context():
        # 1. Limpar dados de teste anteriores
        test_brand = Brand.query.filter_by(name="TEST_BRAND_TR").first()
        if test_brand:
            BrandLog.query.filter_by(brand_id=test_brand.id).delete()
            db.session.delete(test_brand)
            db.session.commit()
            print("Dados de teste anteriores removidos.")

        # 2. Registrar uma nova marca (Evento Inicial: Pedido)
        manager = M24ProcessManager()
        
        brand_data = {
            'name': 'TEST_BRAND_TR',
            'process_number': 'TR-2024-001',
            'brand_type': 'Mista',
            'product_description': 'Serviços de consultoria em TI e IA.',
            'status': 'Pedido',
            'profession': 'Desenvolvedor'
        }
        
        success, brand, message = manager.handle_bpi_event(brand_data)
        if success:
            print(f"✅ Marca registrada com sucesso: {brand.name} (ID: {brand.id})")
            print(f"   Status: {brand.status}")
        else:
            print(f"❌ Erro ao registrar marca: {message}")
            return

        # 3. Simular um novo evento para o MESMO processo (Evento: Concessão)
        event_data = {
            'name': 'TEST_BRAND_TR', # Mesmo nome
            'process_number': 'TR-2024-001', # MESMO NÚMERO
            'status': 'Concedido', # NOVO STATUS
            'product_description': 'Serviços de consultoria em TI e IA. (Atualizado)',
        }
        
        success, brand, message = manager.handle_bpi_event(event_data)
        if success:
            print(f"✅ Evento processado para marca existente: {brand.name}")
            print(f"   Novo Status: {brand.status}")
            
            # Verificar se gerou Log
            logs = BrandLog.query.filter_by(brand_id=brand.id).all()
            print(f"   Total de logs encontrados: {len(logs)}")
            for log in logs:
                print(f"   - [{log.event_date}] {log.event_type}: {log.description}")
        else:
            print(f"❌ Erro ao processar evento: {message}")

if __name__ == "__main__":
    test_process_lifecycle()
