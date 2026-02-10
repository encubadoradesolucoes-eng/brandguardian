from app import app, db, IpiRecord

def check_records():
    with app.app_context():
        count = IpiRecord.query.count()
        print(f"📊 Total de registros na tabela IpiRecord: {count}")
        
        if count > 0:
            print("🔍 Primeiros 5 registros:")
            recs = IpiRecord.query.limit(5).all()
            for r in recs:
                print(f"   - [{r.record_type}] {r.process_number}: {r.brand_name} (Status: {r.status})")
        else:
            print("⚠️ A TABELA ESTÁ VAZIA!")

if __name__ == '__main__':
    check_records()
