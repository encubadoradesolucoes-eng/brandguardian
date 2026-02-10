from app import app, db, IpiRecord

def check_caducidade():
    with app.app_context():
        # Contagem específica
        count_cad = IpiRecord.query.filter_by(status='caducidade').count()
        count_concessao = IpiRecord.query.filter_by(status='concessao').count()
        count_pedido = IpiRecord.query.filter_by(status='pedido').count()
        count_renovacao = IpiRecord.query.filter_by(status='renovacao').count()
        
        print(f"📊 Estatísticas IpiRecord:\n")
        print(f"   🔴 Caducidade: {count_cad}")
        print(f"   🟢 Concessão: {count_concessao}")
        print(f"   🟡 Pedido: {count_pedido}")
        print(f"   🔵 Renovação: {count_renovacao}")
        
        if count_cad == 0:
            print("\n❌ NENHUM registro de caducidade encontrado! Problema na importação.")
        else:
            print("\n✅ Caducidade encontrada! Verificando amostra:")
            rec = IpiRecord.query.filter_by(status='caducidade').first()
            print(f"   Exemplo: Processo {rec.process_number} - Marca: {rec.brand_name}")

if __name__ == '__main__':
    check_caducidade()
