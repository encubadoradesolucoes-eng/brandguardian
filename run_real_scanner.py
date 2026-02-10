import sys
from modules.real_scanner import scan_live_real
from modules.extensions import db
from app import app

if __name__ == "__main__":
    brand_name = input("Digite o nome da marca para scan: ").strip()

    with app.app_context():
        print(f"Iniciando scan para marca: '{brand_name}'")
        result = scan_live_real(brand_name)
        print("\nResultado do scan:")
        print(result)
