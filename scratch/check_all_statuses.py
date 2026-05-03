
from app import app, db, IpiRecord
from sqlalchemy import func

def list_all_statuses():
    with app.app_context():
        # Get distinct statuses from IpiRecord
        statuses = db.session.query(IpiRecord.status).distinct().all()
        print("=== Estados encontrados em IpiRecord ===")
        for s in statuses:
            count = IpiRecord.query.filter_by(status=s[0]).count()
            print(f"- {s[0]}: {count} registros")

        # Also check BpiRecord if it exists (searching in models)
        try:
            from app import BpiRecord
            bpi_statuses = db.session.query(BpiRecord.status).distinct().all()
            print("\n=== Estados encontrados em BpiRecord ===")
            for s in bpi_statuses:
                count = BpiRecord.query.filter_by(status=s[0]).count()
                print(f"- {s[0]}: {count} registros")
        except ImportError:
            print("\nBpiRecord não encontrado no modelo.")

if __name__ == '__main__':
    list_all_statuses()
