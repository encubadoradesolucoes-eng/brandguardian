
import os
import sys
import subprocess
import threading
import time
import webbrowser
import socket

# Log de inicialização para depuração
def log_debug(message):
    with open("m24_launcher_debug.log", "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(".")

def get_persistence_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.abspath(os.path.join(os.path.dirname(sys.executable), relative_path))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_node_engine():
    """Inicia o motor do WhatsApp procurado na pasta real do executável."""
    # Priorizar a pasta externa (onde estão os node_modules reais)
    node_dir = os.path.join(get_persistence_path(''), 'whatsapp-engine')
    
    # Se não existir fora, tenta dentro do bundle (apenas fallback)
    if not os.path.exists(node_dir):
        node_dir = os.path.join(get_base_path(), 'whatsapp-engine')

    log_debug(f"Tentando iniciar Node em: {node_dir}")
    
    if not os.path.exists(node_dir):
        log_debug(f"ERRO: Pasta {node_dir} não encontrada em lado nenhum!")
        return

    try:
        # Popen sem criação de janela
        # No local, o usuário deve ter rodado npm install antes
        subprocess.Popen(['node', 'server.js'], 
                         cwd=node_dir, 
                         shell=True, 
                         creationflags=0x08000000) # CREATE_NO_WINDOW
        log_debug("Comando Node disparado.")
    except Exception as e:
        log_debug(f"Exceção ao iniciar Node: {e}")

if __name__ == "__main__":
    # Limpar log antigo
    if os.path.exists("m24_launcher_debug.log"): 
        try: os.remove("m24_launcher_debug.log")
        except: pass

    log_debug("Iniciando M24 PRO Launcher...")
    
    try:
        print("==========================================")
        print("   BRAND GUARDIAN PRO - WINDOWS BUNDLE")
        print("==========================================")
        
        # 1. Preparar pastas persistentes
        os.makedirs(get_persistence_path('uploads'), exist_ok=True)
        os.makedirs(get_persistence_path('database'), exist_ok=True)
        log_debug("Pastas de persistência verificadas.")

        # 2. Importar App tardiamente para capturar erros de importação
        log_debug("Importando Flask App...")
        from app import app
        log_debug("App importado com sucesso.")

        # 3. Iniciar Node
        if not is_port_in_use(3002):
            threading.Thread(target=start_node_engine, daemon=True).start()
            time.sleep(2)
        else:
            log_debug("Porta 3002 já ocupada.")

        # 4. Abrir Navegador
        print("[*] Abrindo painel de controle...")
        log_debug("Agendando abertura de navegador...")
        threading.Timer(2.5, lambda: webbrowser.open("http://127.0.0.1:7000")).start()

        # 5. Rodar Flask
        log_debug("Iniciando Flask Server...")
        app.run(host='127.0.0.1', port=7000, debug=False, use_reloader=False)

    except Exception as e:
        log_debug(f"ERRO FATAL: {e}")
        import traceback
        error_msg = traceback.format_exc()
        log_debug(error_msg)
        
        print("\n\n[ERRO FATAL NO ARRANQUE]")
        print(error_msg)
        input("\n\nPressione ENTER para sair e verifique o arquivo m24_launcher_debug.log")
