from flask import Flask, render_template_string, jsonify, request
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import app, db

@app.route('/test-visual')
def test_visual():
    """Página de teste simplificada"""
    html = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TESTE Visual Check</title>
    <style>
        body { font-family: monospace; padding: 20px; background: #1a1a1a; color: #fff; }
        .box { border: 2px solid #00ff00; padding: 20px; margin: 20px 0; background: #2a2a2a; }
        .error { color: #ff0000; }
        .success { color: #00ff00; }
        .warning { color: #ffaa00; }
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; background: #00ff00; border: none; }
        pre { background: #000; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>🧪 TESTE DE VERIFICAÇÃO VISUAL</h1>
    
    <div class="box">
        <h2>1. Selecione uma Imagem</h2>
        <input type="file" id="fileInput" accept="image/*">
        <p id="fileInfo" class="warning">Nenhum arquivo selecionado</p>
    </div>
    
    <div class="box">
        <h2>2. Enviar para Análise</h2>
        <button onclick="analisar()">🚀 ANALISAR AGORA</button>
        <p id="status" class="warning">Aguardando...</p>
    </div>
    
    <div class="box">
        <h2>3. Resposta do Servidor</h2>
        <pre id="serverResponse">Nenhuma resposta ainda...</pre>
    </div>
    
    <div class="box">
        <h2>4. Conflitos Detectados</h2>
        <div id="conflicts"></div>
    </div>
    
    <div class="box">
        <h2>5. Resumo Final</h2>
        <div id="summary"></div>
    </div>
    
    <script>
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const status = document.getElementById('status');
        const serverResponse = document.getElementById('serverResponse');
        const conflictsDiv = document.getElementById('conflicts');
        const summaryDiv = document.getElementById('summary');
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                fileInfo.textContent = `✅ ${file.name} (${(file.size/1024).toFixed(1)} KB)`;
                fileInfo.className = 'success';
            }
        });
        
        async function analisar() {
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Selecione uma imagem primeiro!');
                return;
            }
            
            status.textContent = '⏳ Enviando...';
            status.className = 'warning';
            
            const formData = new FormData();
            formData.append('imagem', file);
            formData.append('marca', 'TESTE');
            
            try {
                console.log('📤 Enviando requisição...');
                const response = await fetch('/api/verificacao-imagem-real', {
                    method: 'POST',
                    body: formData
                });
                
                console.log('📥 Resposta recebida:', response.status);
                const data = await response.json();
                console.log('📊 Dados:', data);
                
                // Mostra JSON completo
                serverResponse.textContent = JSON.stringify(data, null, 2);
                
                if (data.status === 'sucesso') {
                    status.textContent = '✅ Análise Concluída!';
                    status.className = 'success';
                    
                    const res = data.resultados;
                    
                    // Processar conflitos
                    conflictsDiv.innerHTML = '';
                    
                    console.log('🔍 Verificando conflitos...');
                    console.log('   conflitos_visuais:', res.conflitos_visuais);
                    console.log('   length:', res.conflitos_visuais ? res.conflitos_visuais.length : 0);
                    
                    if (res.conflitos_visuais && res.conflitos_visuais.length > 0) {
                        conflictsDiv.innerHTML = `<h3 class="error">⚠️ ${res.conflitos_visuais.length} CONFLITOS ENCONTRADOS</h3>`;
                        
                        res.conflitos_visuais.forEach((conf, i) => {
                            const card = document.createElement('div');
                            card.style.cssText = 'border: 2px solid #ff0000; padding: 10px; margin: 10px 0; background: #3a1a1a;';
                            card.innerHTML = `
                                <strong>#${i+1}: ${conf.marca_bpi}</strong><br>
                                Similaridade: <span style="font-size: 1.5em; color: #ff0000;">${conf.similaridade_media}%</span><br>
                                Gravidade: ${conf.gravidade}<br>
                                Processo: ${conf.processo_bpi}<br>
                                Ação: ${conf.acao}
                            `;
                            conflictsDiv.appendChild(card);
                        });
                    } else {
                        conflictsDiv.innerHTML = '<p class="success">✅ Nenhum conflito detectado</p>';
                    }
                    
                    // Processar resumo
                    if (res.resumo) {
                        const r = res.resumo;
                        const cor = r.nivel_risco_visual === 'ALTO' ? 'error' : 
                                   r.nivel_risco_visual === 'MODERADO' ? 'warning' : 'success';
                        
                        summaryDiv.innerHTML = `
                            <p>Risco Visual: <strong style="font-size: 2em;" class="${cor}">${r.risco_visual}%</strong></p>
                            <p>Nível: <strong class="${cor}">${r.nivel_risco_visual}</strong></p>
                            <p>${r.recomendacao}</p>
                        `;
                    }
                    
                } else {
                    status.textContent = '❌ Erro: ' + (data.error || 'Desconhecido');
                    status.className = 'error';
                }
                
            } catch (error) {
                console.error('❌ Erro:', error);
                status.textContent = '❌ Erro de conexão: ' + error;
                status.className = 'error';
            }
        }
    </script>
</body>
</html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    print("🧪 Abrindo página de teste em: http://localhost:7000/test-visual")
    print("👉 Acesse essa URL no navegador!")
