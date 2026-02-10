from app import app, db, Brand, Entity
import sys

def rollback_bpi_import():
    print("🧹 Iniciando limpeza de dados do BPI...")
    
    with app.app_context():
        # 1. Remover Marcas Importadas
        # Identificadas pelo campo registered_by
        brands_to_delete = Brand.query.filter_by(registered_by='Sistema BPI Import').all()
        count_brands = len(brands_to_delete)
        
        if count_brands > 0:
            for brand in brands_to_delete:
                db.session.delete(brand)
            print(f"✅ {count_brands} Marcas marcadas para exclusão.")
        else:
            print("ℹ️ Nenhuma marca importada encontrada.")

        # 2. Remover Entidades Geradas (Sem email e sem NUIT)
        # O importador cria entidades apenas com nome, deixando email e nuit como NULL
        entities_to_delete = Entity.query.filter(Entity.email == None, Entity.nuit == None).all()
        count_entities = len(entities_to_delete)
        
        if count_entities > 0:
            for entity in entities_to_delete:
                db.session.delete(entity)
            print(f"✅ {count_entities} Entidades provisórias marcadas para exclusão.")
        else:
            print("ℹ️ Nenhuma entidade provisória encontrada.")

        # Confirmar e Executar
        if count_brands == 0 and count_entities == 0:
            print("✨ Banco de dados já está limpo!")
            return

        try:
            db.session.commit()
            print("\n🗑️ LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("O sistema voltou ao estado anterior à importação.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao apagar dados: {e}")

if __name__ == '__main__':
    rollback_bpi_import()
