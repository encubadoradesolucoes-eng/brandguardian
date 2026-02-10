from app import app
print(f"DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
