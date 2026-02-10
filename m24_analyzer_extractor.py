import fitz  # PyMuPDF
import csv
import re
import os

def extract_bpi_challenge(pdf_filename):
    # Setup de Pastas
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(base_dir, pdf_filename)
    output_dir = os.path.join(base_dir, 'bpi')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"🚀 INICIANDO DESAFIO M24 ANALYZER")
    print(f"📂 Lendo Arquivo: {pdf_filename}")
    print(f"📂 Destino: {output_dir}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ ERRO: Arquivo {pdf_filename} não encontrado na raiz!")
        return

    doc = fitz.open(pdf_path)
    
    concessoes = []
    requerentes = {} # {Nome: ID}
    req_counter = 1
    
    # Regex refinado para capturar Processos (comum no BPI: Num Processo isolado ou com barra)
    # Ex: 47520, 6492/2006, etc.
    process_pattern = re.compile(r'^(\d{4,7}(?:/\d{4})?)')
    
    total_pages = len(doc)
    print(f"📄 Total de Páginas: {total_pages}")
    
    count_concessao = 0
    in_section = False
    
    # Heurística de Seção: BPI tem cabeçalhos claros
    # Vamos processar TODAS as páginas buscando o padrão visual de processo
    
    for page_index, page in enumerate(doc):
        page_num = page_index + 1
        text = page.get_text("text")
        
        # Detecção de Contexto (Opcional, mas ajuda a evitar falsos positivos em índices)
        if "Concessão" in text or "CONCESSÃO" in text or "Despachos" in text:
            in_section = True
            
        # Analise linha a linha
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Buffer para tentar montar o registro (Processo -> Marca -> Titular)
        # O BPI muitas vezes tem o processo numa linha, e dados nas seguintes.
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 1. É um número de processo?
            match = process_pattern.search(line)
            if match:
                proc_id = match.group(1)
                
                # Criterio de exclusão: Se for sumário (muitos pontos ......) ou numero de pagina
                if "....." in line or proc_id == str(page_num):
                    i += 1
                    continue

                # Tentar extrair dados das próximas 5-10 linhas (janela de contexto)
                window = lines[i:i+10] # Pega o bloco
                
                # --- HEURÍSTICA DE CAPTURA MELHORADA ---
                
                marca_cand = "Desconhecida"
                titular_cand = "Desconhecido"
                
                # Blacklists para filtrar lixo
                BLOCK_TERMS = ['maputo', 'matola', 'beira', 'moçambique', 'av.', 'rua', 'bairro', 'estrada', 'caixa postal', 'p.o. box', 'box', 'prédio', 'andar', 'flat', 'cidade', 'province', 'street', 'road']
                DESC_TERMS = ['serviços', 'comércio', 'publicidade', 'gestão', 'distribuição', 'venda', 'importação', 'exportação', 'transporte', 'construção', 'consultoria', 'trabalhos', 'negócios', 'mercadorias', 'fungicidas', 'herbicidas']
                LEGAL_TERMS = ['LDA', 'LIMITADA', 'S.A.', 'INC.', 'LIMITED', 'LTD', 'COMPANY', 'SOCIETY', 'HOLDING', 'E.I.', 'S.A.R.L.', 'BIZ', 'GROUP']

                def is_valid_titular(line):
                    l_lower = line.lower()
                    if len(line) < 3 or len(line) > 100: return False
                    
                    # Regra 1: Não pode ser endereço
                    if any(bt in l_lower for bt in BLOCK_TERMS): return False
                    
                    # Regra 2: Não pode ser descrição de serviços (Classe)
                    if any(dt in l_lower for dt in DESC_TERMS): return False
                    
                    # Regra 3: Não pode começar com Numero (ex: "35 Publicidade") - EXCETO se for nome numérico valido mas raro
                    # Se começar com digito e tiver "serviços" ou ";" é lixo
                    if line[0].isdigit() and (';' in line or ' ' in line):
                         return False

                    return True

                # Analisar Janela
                possible_titular_lines = []
                
                for idx, w_line in enumerate(window):
                    if idx == 0: continue # Pula processo
                    if process_pattern.match(w_line): break # Outro processo, paramos
                    
                    # Tentar achar a MARCA (Geralmente a primeira linha válida após processo)
                    # Assumindo que Marca vem ANTES do Titular
                    if marca_cand == "Desconhecida" and len(w_line) > 1:
                        # Se não for endereço nem descrição e não tiver termo legal forte, pode ser marca
                        clean = True
                        if any(x in w_line.lower() for x in BLOCK_TERMS + DESC_TERMS): clean = False
                        if clean:
                             marca_cand = w_line
                             continue # Se achou marca, passa pro proximo

                    # Tentar achar TITULAR
                    if is_valid_titular(w_line):
                        # Se tiver termo legal, é bingo
                        is_legal = any(lt in w_line.upper() for lt in LEGAL_TERMS)
                        
                        if is_legal:
                            titular_cand = w_line
                            break # Achamos o melhor candidato
                        else:
                            possible_titular_lines.append(w_line)
                
                # Se não achou com termo legal, pega o primeiro candidato válido que sobrou
                # (Muitas empresas nao tem LDA no nome fantasia mostrado)
                if titular_cand == "Desconhecido" and possible_titular_lines:
                    # Preferencia: Linhas em UPPERCASE
                    titular_cand = next((p for p in possible_titular_lines if p.isupper()), possible_titular_lines[0])

                # Se a marca ainda for desconhecida, tentar usar a linha anterior ao titular
                # (Lógica posicional inversa)
                
                # Limpeza Final
                if titular_cand in ["Desconhecido", marca_cand]: 
                    # Se falhou, marca como Manual Review para nao sujar o banco
                    i += 1
                    continue 

                # Salvar
                if titular_cand not in requerentes:
                    rid = f"REQ{req_counter:04d}"
                    requerentes[titular_cand] = rid
                    req_counter += 1
                
                concessoes.append({
                    'proc': proc_id,
                    'marca': marca_cand,
                    'classe': classe_found if 'classe_found' in locals() else '0',
                    'titular_id': requerentes[titular_cand],
                    'pagina': page_num
                })
                count_concessao += 1
            
            i += 1
            
    doc.close()
    
    # --- GERAR CSVs ---
    
    # 1. Concessoes
    csv_con = os.path.join(output_dir, f"m24_analyzer_concessoes_{pdf_filename.replace('.pdf','')}.csv")
    with open(csv_con, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Processo', 'Marca', 'Classe', 'ID_Requerente', 'Pagina_BPI'])
        for c in concessoes:
            writer.writerow([c['proc'], c['marca'], c['classe'], c['titular_id'], c['pagina']])

    # 2. Requerentes
    csv_req = os.path.join(output_dir, f"m24_analyzer_requerentes_{pdf_filename.replace('.pdf','')}.csv")
    with open(csv_req, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID_Requerente', 'Nome_Requerente', 'Pagina_Detectado'])
        for nome, rid in requerentes.items():
            # Pegar a primeira pagina onde aparece
            first_pg = next((c['pagina'] for c in concessoes if c['titular_id'] == rid), 0)
            writer.writerow([rid, nome, first_pg])

    print("\n✅ DESAFIO CONCLUÍDO COM SUCESSO!")
    print(f"   - Concessões Identificadas: {count_concessao}")
    print(f"   - Requerentes Únicos: {len(requerentes)}")
    print(f"   - Arquivos gerados em: {output_dir}")

if __name__ == '__main__':
    extract_bpi_challenge('BPI-170-Junho.pdf')
