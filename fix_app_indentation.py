import os

try:
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cut_point = 0
    # Procurar onde começa a bagunça
    for i, line in enumerate(lines):
        if "def run_purification_job():" in line:
            cut_point = i
            break
    
    # Se não achou a função, procure o bloco if __name__
    if cut_point == 0:
        for i, line in enumerate(lines):
            if "if __name__ ==" in line:
                cut_point = i
                break

    if cut_point > 0:
        clean_lines = lines[:cut_point]
        
        # Novo final limpo e indentado corretamente (4 espaços)
        tail = """
# ========== MÓDULO PURIFICAÇÃO (GLOBAL CHECK) ==========
PURIFICATION_STATE = {
    'running': False,
    'progress': 0,
    'current_brand': '',
    'conflicts': [],
    'complete': False
}

@app.route('/admin/purification')
@login_required
def purification_page():
    if current_user.role != 'admin': 
        return redirect(url_for('index'))
    return render_template('admin/purification.html')

@app.route('/api/purification/start', methods=['POST'])
@login_required
def start_purification():
    global PURIFICATION_STATE
    PURIFICATION_STATE = {
        'running': True, 
        'progress': 0, 
        'current_brand': '', 
        'conflicts': [], 
        'complete': False
    }
    
    import threading
    thread = threading.Thread(target=run_purification_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/api/purification/status')
@login_required
def status_purification():
    return jsonify(PURIFICATION_STATE)

def run_purification_job():
    pass

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_users()
    port = int(os.environ.get('PORT', 7000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
"""
        with open('app.py', 'w', encoding='utf-8') as f:
            f.writelines(clean_lines)
            f.write(tail)
            
        print("✅ app.py reparado com sucesso!")
        
    else:
        print("❌ Ponto de corte não encontrado.")

except Exception as e:
    print(f"Erro: {e}")
