import fitz  # PyMuPDF
import csv
import re
import os
import sys

def extract_bpi_to_csv(pdf_path, output_dir='output_csvs'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"📄 Processando: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    # Estruturas de Dados
    requerentes = {}  # {Nome: ID}
    concessoes = []
    
    # Regex padrões
    # Ex: "12345 DUMMY MARK (35) ... Requerente: JOAO DA SILVA"
    # Ajustado para o padrão visual do BPI Concessões (Listas verticais ou tabelas)
    
    req_counter = 1
    
    # Loop pelas páginas (Focado em Concessões - geralmente pg 45 em diante, mas vamos varrer buscando headers)
    in_concessao_section = False
    
    print("🔍 Analisando páginas...")
    
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        
        # Detectar Seção
        if "Concessões de Marcas" in text or "MARCAS CONCEDIDAS" in text:
            in_concessao_section = True
            print(f"   -> Seção de Concessões detectada na página {page_num+1}")
        
        if "Recusas" in text or "Renovações" in text:
            if in_concessao_section:
                print(f"   -> Fim da seção na página {page_num+1}")
                in_concessao_section = False
        
        if in_concessao_section:
            # Lógica de Extração Linha a Linha (Simplificada para demonstração)
            # Tenta capturar padrão: "Nº Processo" ... "Marca" ... "Classe" ... "Titular"
            
            # Pattern genérico para capturar blocos
            # No BPI real, concessões são listas. Vamos usar regex para números de processo.
            # Ex: 47520 ... SHOCOLATA ...
            
            lines = text.split('\n')
            current_proc = None
            current_brand = None
            current_class = None
            
            for line in lines:
                line = line.strip()
                
                # Match Processo (Ex: 47520/2023 ou apenas 47520)
                proc_match = re.search(r'^(\d{4,7}(?:/\d{4})?)', line)
                if proc_match:
                    # Salvar anterior se existir
                    if current_proc and current_brand:
                        # Processar Requerente (Mockado aqui pois no texto corrido é difícil sem layout preciso)
                        # No script final usaremos coordenadas (rects) para precisão.
                        req_name = "Requerente Detectado via Layout" 
                        
                        # Gerar ID Requerente
                        if req_name not in requerentes:
                            requerentes[req_name] = f"REQ{req_counter:03d}"
                            req_counter += 1
                        
                        concessoes.append({
                            'proc_id': current_proc,
                            'marca': current_brand,
                            'classe': current_class or '0',
                            'data_concessao': '15/06/2023', # Data do boletim
                            'ano': '2023',
                            'boletim': 'BPI_DETECTADO',
                            'req_id': requerentes[req_name]
                        })

                    current_proc = proc_match.group(1)
                    current_brand = line.replace(current_proc, '').strip() # Resto da linha é marca?
                    current_class = '0' # Teria que buscar na prox linha
                    
                # Tentar achar classe "Kl. 35" ou "(35)"
                class_match = re.search(r'\((\d{1,2})\)', line)
                if class_match and current_proc:
                    current_class = class_match.group(1)

    doc.close()
    
    # Gerar CSVs
    # 1. Concessoes
    csv_con = os.path.join(output_dir, 'concessoes_gerado.csv')
    with open(csv_con, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['proc_id', 'marca', 'classe', 'data_concessao', 'ano', 'boletim', 'req_id'])
        for c in concessoes:
            writer.writerow([c['proc_id'], c['marca'], c['classe'], c['data_concessao'], c['ano'], c['boletim'], c['req_id']])
            
    # 2. Requerentes
    csv_req = os.path.join(output_dir, 'requerentes_gerado.csv')
    with open(csv_req, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['req_id', 'req_nome', 'req_tipo', 'req_pais', 'req_identificado_em'])
        for nome, rid in requerentes.items():
            writer.writerow([rid, nome, 'Empresa', 'Moçambique', '2023'])

    print(f"\n✅ CSVs gerados em: {output_dir}")
    print(f"   - {len(concessoes)} Concessões extraídas.")
    print(f"   - {len(requerentes)} Requerentes identificados.")

if __name__ == '__main__':
    # Exemplo de uso
    import sys
    if len(sys.argv) > 1:
        extract_bpi_to_csv(sys.argv[1])
    else:
        print("Uso: python pdf_to_csv_tool.py <caminho_do_pdf>")
