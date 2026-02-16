
import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)
inspector = inspect(engine)

for table_name in ['brand', 'ipi_record']:
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    print(f"Table {table_name}: {'image_data' in columns}")
    if 'image_data' in columns:
        col = next(c for c in inspector.get_columns(table_name) if c['name'] == 'image_data')
        print(f"  Type: {col['type']}")
