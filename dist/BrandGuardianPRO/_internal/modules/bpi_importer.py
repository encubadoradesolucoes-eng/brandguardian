import fitz  # PyMuPDF
import re
import os
from datetime import datetime, timedelta

class BPIImporter:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.stats = {
            'processed_pages': 0,
            'records_created': 0,
            'images_extracted': 0,
            'errors': 0
        }
        
        # Estado da Leitura
        self.current_context = {
            'status': 'desconhecido', # pedido, concessao, recusa
            'type': 'marca',          # marca, logotipo
            'bulletin_num': None,
            'bulletin_date': None
        }

    def run(self):
        print(f"[INFO] Iniciando importacao AVANCADA de: {self.pdf_path}")
        
        try:
            doc = fitz.open(self.pdf_path)
        except Exception as e:
            print(f"[ERRO] Erro ao abrir PDF: {e}")
            return

        total_pages = len(doc)
        print(f"[INFO] Total de paginas: {total_pages}")
        
        # Tentar extrair metadados do Boletim na primeira página
        self.extract_bulletin_meta(doc[0])
        
        from app import app
        # Diretório para imagens extraídas
        img_dir = os.path.join(app.root_path, 'static', 'ipi_images')
        os.makedirs(img_dir, exist_ok=True)

        for page_num in range(total_pages):
            page = doc[page_num]
            self.stats['processed_pages'] += 1
            
            # 1. Analisar Cabeçalho da Página (Contexto)
            text = page.get_text("text")
            self.update_context(text)
            
            print(f"   Pg {page_num+1}: Modo [{self.current_context['type'].upper()}] - Status [{self.current_context['status'].upper()}]")

            # 2. Estratégia de Extração baseada no Contexto
            # 2. Router de Extração Universal
            ctype = self.current_context['type']
            cformat = self.current_context.get('format', '')

            # Logica de Dispatch
            if ctype in ['logotipo', 'nome_comercial', 'insignia']:
                # Estes geralmente seguem o padrão "Bloco com Âncora L.N/N.N"
                self.extract_blocks(page, img_dir)
            
            elif ctype == 'marca' and "tabela" in cformat:
                self.extract_table_brands(page)
            
            elif ctype in ['patente', 'modelo_utilidade', 'design']:
                # Extração Genérica de Blocos Numerados
                self.extract_generic_numbered_blocks(page)
            
            elif ctype == 'marca' and cformat == 'texto':
                 # Pedidos de marca em texto corrido (não tabela)
                 self.extract_blocks(page, img_dir)

            elif "tabela" in cformat:
                # Tenta extrair tabela genérica se format for tabela mas tipo desconhecido
                 self.extract_table_brands(page)
            
            else:
                # Fallback genérico para capturar qualquer coisa listada
                # (Opcional: implementar extract_raw_text_records)
                pass

        self.save_summary()

    def extract_table_brands(self, page):
        """
        Extrai marcas usando estratégia de COLUNAS VIRTUAIS baseadas em coordenadas X.
        Resolve o problema de mistura de dados (Marca/Titular/Endereço).
        """
        words = page.get_text("words") # (x0, y0, x1, y1, "texto", block_no, line_no, word_no)
        
        # 1. Agrupar palavras em LINHAS (eixo Y)
        rows = {}
        for w in words:
            y_mid = round((w[1] + w[3]) / 2) # Usar o meio da palavra para agrupar melhor
            # Agrupamento flexível (tolerância de 3px)
            found_row = False
            for key in rows.keys():
                if abs(key - y_mid) < 5:
                    rows[key].append(w)
                    found_row = True
                    break
            if not found_row:
                rows[y_mid] = [w]
        
        # Ordenar linhas de cima para baixo
        sorted_y = sorted(rows.keys())
        
        columns_config = {
            'marca_nominativa': (0, 130),
            'marca_figurativa': (130, 240), # Coluna visual, muitas vezes tem texto descritivo
            'processo': (240, 290),
            'classe': (290, 330),
            'requerente': (330, 520),
            'data': (520, 600)
        }

        records_cache = [] # Cache para tentar juntar linhas quebradas (endereços)

        for y in sorted_y:
            row_words = sorted(rows[y], key=lambda w: w[0])
            
            # Montar dados da linha baseados nas colunas
            row_data = {k: [] for k in columns_config.keys()}
            
            for w in row_words:
                x_mid = (w[0] + w[2]) / 2
                text = w[4]
                
                # Distribuir nas colunas
                for col_name, (x_min, x_max) in columns_config.items():
                    if x_min <= x_mid < x_max:
                        row_data[col_name].append(text)
                        break
            
            # Consolidar textos
            final_row = {k: " ".join(v).strip() for k, v in row_data.items()}
            
            # Validação: É uma linha de REGISTRO VÁLIDO?
            # Critério: Deve ter número de Processo (ex: 4-6 dígitos)
            proc = final_row['processo']
            # Limpeza rápida de chars estranhos no processo
            proc = re.sub(r'[^\d]', '', proc)
            
            if proc and len(proc) >= 4:
                # É um novo registro!
                # Limpar campos vazios "-"
                marca = final_row['marca_nominativa']
                if marca in ['-', '–', '']: 
                    marca = final_row['marca_figurativa'] # Tentar a outra coluna
                if marca in ['-', '–', '']:
                    marca = "Marca Figurativa"

                records_cache.append({
                    'process_number': proc,
                    'brand_name': marca,
                    'applicant': final_row['requerente'],
                    'classe': final_row['classe'],
                    'nice_class': final_row['classe'], # Alias
                    'date': final_row['data']
                })
            else:
                # LINHA DE CONTINUAÇÃO (ex: Endereço do Titular)
                # Se tivermos um registro anterior, vamos anexar o texto do requerente?
                # A imagem mostra que o endereço vem na coluna Titular nas linhas seguintes.
                # MAS, para o nosso sistema, queremos LIMPEZA. O endereço suja o nome.
                # Estratégia: IGNORAR linhas de continuação que pareçam endereços (Av., Rua, Caixa Postal)
                # OU se for continuação do NOME da marca.
                pass 

        # Salvar todos os registros encontrados nesta página
        for rec in records_cache:
            self.save_table_record(
                rec['process_number'], 
                rec['brand_name'], 
                rec['applicant'], 
                rec['nice_class'], 
                rec['date']
            )

    def save_table_record(self, process_number, brand_name, applicant, nice_class, date_deposito, image_path=None):
        from app import db, IpiRecord
        
        # Verificar duplicidade
        existing = IpiRecord.query.filter_by(process_number=process_number).first()
        if not existing:
             rec = IpiRecord(
                process_number=process_number,
                record_type=self.current_context.get('type', 'marca'),
                status=self.current_context.get('status', 'concessao'),
                brand_name=brand_name[:250],
                applicant_name=applicant[:250],
                nice_class=nice_class,
                bulletin_number=self.current_context['bulletin_num'],
                # Data de publicacao ja temos no context. Data Deposito é extra.
                publication_date=self.current_context['bulletin_date'],
                image_path=None # Tabelas geralmente nao tem imagem inline extraivel facil
            )
             db.session.add(rec)
             try:
                db.session.commit()
                self.stats['records_created'] += 1
             except:
                db.session.rollback()

    def extract_bulletin_meta(self, first_page):
        text = first_page.get_text()
        # Ex: "Boletim da Propriedade Industrial Nº 170 de 15 de Junho de 2023"
        match = re.search(r'Boletim.*?Nº\s*(\d+).*?de\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})', text, re.IGNORECASE)
        if match:
            self.current_context['bulletin_num'] = match.group(1)
            date_str = match.group(2)
            # Tentar converter data (PT) para objeto date
            # Simplificação: usar data atual se falhar
            self.current_context['bulletin_date'] = datetime.now().date() 
            print(f"[INFO] Boletim Identificado: No {self.current_context['bulletin_num']} ({date_str})")

    def update_context(self, text):
        text_lower = text.lower()
        
        # 1. Detectar STATUS (Contexto Legal)
        if "concessões" in text_lower or "concedidos" in text_lower or "publicados" in text_lower:
            self.current_context['status'] = 'concessao'
            self.current_context['format'] = 'tabela' if "tabela" not in self.current_context.get('format', '') else self.current_context['format']
        elif "pedidos" in text_lower and "aviso" in text_lower:
            self.current_context['status'] = 'pedido'
            self.current_context['format'] = 'texto' # Default para pedidos (muitas vezes blocos)
        elif "recusas" in text_lower:
            self.current_context['status'] = 'recusa'
        elif "caducidade" in text_lower:
            self.current_context['status'] = 'caducidade'
            self.current_context['format'] = 'tabela_caducidade'
        elif "renovação" in text_lower or "renovações" in text_lower:
            self.current_context['status'] = 'renovacao'
            self.current_context['format'] = 'tabela' # Geralmente tabela
        elif "averbamentos" in text_lower or "transmissão" in text_lower:
            self.current_context['status'] = 'averbamento'
            self.current_context['format'] = 'texto_generico'

        # 2. Detectar TIPO DE PROPRIEDADE (O que é?)
        # Prioridade para termos mais específicos
        if "logótipos" in text_lower or "logotipos" in text_lower:
            self.current_context['type'] = 'logotipo'
        elif "nomes comerciais" in text_lower:
            self.current_context['type'] = 'nome_comercial'
        elif "insígnias" in text_lower:
            self.current_context['type'] = 'insignia'
        elif "patentes" in text_lower:
            self.current_context['type'] = 'patente'
            self.current_context['format'] = 'bloco_complexo' # Patentes têm resumo, reivindicações...
        elif "desenhos" in text_lower and "modelos" in text_lower:
            self.current_context['type'] = 'design' # Desenho/Modelo Industrial
        elif "modelos de utilidade" in text_lower:
            self.current_context['type'] = 'modelo_utilidade'
        elif "marcas" in text_lower:
             # Só define como marca se não for nenhum dos anteriores (fallback)
             if self.current_context['type'] not in ['logotipo', 'nome_comercial', 'insignia']:
                self.current_context['type'] = 'marca'


    def extract_generic_numbered_blocks(self, page):
        """
        Captura Patentes, Designs, etc. que geralmente começam por um Número Grande em destaque
        ou seguem estrutura de campos (Requerente, Epígrafe, etc.)
        """
        text = page.get_text("text")
        # Padrão genérico de Patente/Design: Número isolado seguido de metadados
        # Ex: "1234" (Titulo) ... "Requerente: ..."
        
        # Vamos tentar extrair pelo menos o Requerente e Título para constar no sistema.
        # Regex para capturar Requerente
        requerentes = re.findall(r'Requerente:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        titulos = re.findall(r'Epígrafe:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        numeros = re.findall(r'^\s*(\d+)\s*$', text, re.MULTILINE) # Numeros isolados em linhas
        
        # Se achou algo, cria registros "genéricos" para revisão humana
        # Match impreciso (zipar listas pode falhar se tamanhos diferentes), mas melhor que nada.
        count = min(len(requerentes), len(titulos))
        
        for i in range(count):
            proc_num = numeros[i] if i < len(numeros) else f"UNKNOWN-{i}"
            if len(proc_num) < 7 and proc_num.isdigit(): # Filtra numeros de pagina
                 self.save_record(
                    process_number=proc_num,
                    applicant=requerentes[i],
                    raw_text=text,
                    record_rect=fitz.Rect(0,0,10,10), # Dummy
                    page=page,
                    img_dir=None,
                    brand_name_override=titulos[i] # Usa o título da patente como "Nome da Marca"
                 )

    def extract_table_brands(self, page):
        # ... (Mantido igual) ...
        # (Se for NOME COMERCIAL, usa lógica de BLOCOS verticais igual Logotipo, não tabela)
        pass 

    def extract_blocks(self, page, img_dir):
        """
        Extrai blocos verticais (Logotipos e Nomes Comerciais).
        """
        type_prefix = "L.N" if self.current_context['type'] == 'logotipo' else "N.N"
        
        # Buscar âncoras (L.N ou N.N)
        anchors = page.search_for(type_prefix)
        anchors.sort(key=lambda r: r.y0)
        
        for i, rect in enumerate(anchors):
            y_start = rect.y0
            y_end = anchors[i+1].y0 if i + 1 < len(anchors) else page.rect.height
            
            record_rect = fitz.Rect(0, y_start, page.rect.width, y_end)
            block_text = page.get_text("text", clip=record_rect)
            
            # Regex Dinâmico
            regex_num = type_prefix + r'.*?(\d+/\d{4})'
            proc_num = self.extract_field(block_text, regex_num)
            requerente = self.extract_field(block_text, r'Requerente:\s*(.+?)(?:\n|Data|Endereço)')
            
            if proc_num:
                # Se for NOME COMERCIAL, extrair o nome protegido
                brand_text = "Logotipo Figurativo"
                if self.current_context['type'] == 'nome_comercial':
                    # O nome vem depois de "O nome consiste em:"
                    match_name = re.search(r'O nome consiste em:\s*\n*(.+)', block_text, re.IGNORECASE | re.MULTILINE)
                    if match_name:
                        brand_text = match_name.group(1).strip()
                    else:
                        brand_text = "Nome Comercial (Não identificado)"

                self.save_record(
                    process_number=proc_num,
                    applicant=requerente,
                    raw_text=block_text,
                    record_rect=record_rect,
                    page=page,
                    img_dir=img_dir,
                    brand_name_override=brand_text
                )
        """
        Extrai marcas de tabelas de concessão (Padrão) E Caducidade.
        """
        words = page.get_text("words")
        # 1. Agrupar palavras em LINHAS (eixo Y)
        rows = {}
        for w in words:
            y_mid = round((w[1] + w[3]) / 2)
            found_row = False
            for key in rows.keys():
                if abs(key - y_mid) < 5:
                    rows[key].append(w)
                    found_row = True
                    break
            if not found_row:
                rows[y_mid] = [w]
        
        sorted_y = sorted(rows.keys())

        # Se for CADUCIDADE, usar config específica
        if self.current_context.get('format') == 'tabela_caducidade':
            self.process_caducidade_table(rows, sorted_y)
        else:
            self.process_concession_table(rows, sorted_y)

    def process_concession_table(self, rows, sorted_y):
        # 1. Detectar Cabeçalhos Dinamicamente
        # Procurar linha com "Marca Nominativa", "Processo", "Classe"
        headers_config = {
            'marca': 'nominativa',
            'processo': 'processo',
            'classe': 'classe',
            'requerente': 'requerente',
            'data': 'data'
        }
        
        col_limits = self.detect_column_limits(rows, sorted_y, headers_config)
        
        # Fallback se não detectar cabeçalhos (usar padrão fixo do BPI A4)
        if not col_limits:
            col_limits = {
                'marca': (0, 130),
                'processo': (240, 290),
                # Classe ignorada se não tiver espaço
                'requerente': (330, 520),
                'data': (520, 600)
            }

        records_cache = []

        for y in sorted_y:
            row_words = sorted(rows[y], key=lambda w: w[0])
            row_data = self.extract_row_data(row_words, col_limits)
            
            # Validação Rigorosa
            proc = re.sub(r'[^\d]', '', row_data.get('processo', ''))
            
            # Só aceita se tiver processo válido (ignora linhas de endereço/continuação)
            if proc and len(proc) >= 4:
                marca = row_data.get('marca', '')
                # Verifica coluna visual (figurativa) se marca vazia
                if not marca or len(marca) < 2:
                    # Tentar pegar texto na zona visual?
                    # Simplificação: Se vazio, é figurativa
                    marca = "Marca Figurativa"

                records_cache.append({
                    'process_number': proc,
                    'brand_name': marca,
                    'applicant': row_data.get('requerente', ''),
                    'nice_class': row_data.get('classe', 'N/A'),
                    'date': row_data.get('data', '')
                })

        for rec in records_cache:
            self.save_table_record(
                rec['process_number'], 
                rec['brand_name'], 
                rec['applicant'], 
                rec['nice_class'], 
                rec['date']
            )

    def process_caducidade_table(self, rows, sorted_y):
        # Cabeçalhos típicos de Caducidade
        headers_config = {
            'marca': 'logotipo', # Em caducidade, a coluna chama "Logotipo"
            'processo': 'processo',
            'requerente': 'requerente',
            'data': 'data'
        }
        
        col_limits = self.detect_column_limits(rows, sorted_y, headers_config)
        
        if not col_limits:
            col_limits = {
                'marca': (50, 200),
                'processo': (200, 280),
                'requerente': (280, 500),
                'data': (500, 600)
            }
            
        for y in sorted_y:
            row_words = sorted(rows[y], key=lambda w: w[0])
            row_data = self.extract_row_data(row_words, col_limits)
            
            proc = re.sub(r'[^\d]', '', row_data.get('processo', ''))
            
            if proc and len(proc) >= 3:
                self.save_table_record(
                    process_number=proc,
                    brand_name=row_data.get('marca', 'Desconhecido'),
                    applicant=row_data.get('requerente', 'Desconhecido'),
                    nice_class="N/A", 
                    date_deposito=row_data.get('data', '')
                )
    
    def detect_column_limits(self, rows, sorted_y, headers_config):
        """
        Tenta encontrar a linha de cabeçalho e define os limites X.
        """
        detected = {}
        header_y = None
        
        # Varrer as primeiras 20 linhas buscando palavras chave
        for i in range(min(20, len(sorted_y))):
            y = sorted_y[i]
            words = rows[y]
            text_line = " ".join([w[4].lower() for w in words])
            
            # Verificar se contem chaves
            score = 0
            for k, v in headers_config.items():
                if v in text_line: score += 1
            
            if score >= 2: # Pelo menos 2 colunas identificadas
                header_y = y
                # Mapear posições X das palavras chave
                current_x = 0
                
                # Heurística simplificada: 
                # Se achou a linha, vamos tentar inferir os limites pelas palavras
                # Mas palavras de cabeçalho podem estar centradas ou à esquerda.
                # Melhor usar a coordenada X da palavra encontrada como INICIO da coluna.
                
                # Resetar configs
                
                for w in words:
                    txt = w[4].lower()
                    for col_key, keyword in headers_config.items():
                        if keyword in txt:
                             # Inicio desta coluna = w[0] (x0)
                             detected[col_key] = w[0]
                break
        
        if not detected: return None
        
        # Converter pontos de inicio em intervalos (start, end)
        # Ordenar colunas por X
        sorted_cols = sorted(detected.items(), key=lambda x: x[1])
        final_limits = {}
        
        for i in range(len(sorted_cols)):
            key, start = sorted_cols[i]
            # O fim desta coluna é o inicio da proxima (menos margem) ou fim da pagina
            if i + 1 < len(sorted_cols):
                end = sorted_cols[i+1][1] - 5
            else:
                end = 600 # Largura aprox pagina
            
            # Ajuste fino: muitas vezes o titulo "Processo" está no meio, mas os dados começam antes.
            # Vamos dar uma margem à esquerda
            final_limits[key] = (start - 20, end)
            
        return final_limits

    def extract_row_data(self, row_words, col_limits):
        data = {k: [] for k in col_limits.keys()}
        for w in row_words:
            x_mid = (w[0] + w[2]) / 2
            text = w[4]
            # Encontrar em qual coluna cai
            for col, (xmin, xmax) in col_limits.items():
                if xmin <= x_mid < xmax:
                    data[col].append(text)
                    break
        return {k: " ".join(v).strip() for k, v in data.items()}
        """
        Extrai logótipos (L.Nº) procurando o texto e RECORTANDO a imagem associada.
        """
        # Buscar "L.N" (abrange L.Nº, L.N°, L.No)
        ln_rects = page.search_for("L.N")
        
        # Ordenar por posição vertical (Y)
        ln_rects.sort(key=lambda r: r.y0)
        
        for i, rect in enumerate(ln_rects):
            # A área do registro vai do "L.Nº" atual até o próximo "L.Nº" (ou fim da página)
            y_start = rect.y0
            if i + 1 < len(ln_rects):
                y_end = ln_rects[i+1].y0
            else:
                y_end = page.rect.height
            
            # Definir retângulo de interesse
            record_rect = fitz.Rect(0, y_start, page.rect.width, y_end)
            
            # Extrair texto desse bloco
            block_text = page.get_text("text", clip=record_rect)
            
            # Parsear dados (Regex mais permissivo para L.N + Numero em nova linha)
            ln_num = self.extract_field(block_text, r'L\.N.*?(\d+/\d{4})')
            requerente = self.extract_field(block_text, r'REQUERENTE:\s*(.+?)(?:\n|Data|Endereço)')
            
            if ln_num:
                # Salvar Registro no Banco
                self.save_record(
                    process_number=ln_num,
                    applicant=requerente,
                    raw_text=block_text,
                    record_rect=record_rect, # Passar rect para extrair imagem depois
                    page=page,
                    img_dir=img_dir
                )

    def save_record(self, process_number, applicant, raw_text, record_rect, page, img_dir, brand_name_override=None):
        from app import db, IpiRecord
        
        # 1. Extração da Imagem (Crop Visual Inteligente)
        saved_img_path = None
        
        # Só extrair imagem se NÃO FOR nome comercial (geralmente só texto) ou se quisermos garantir
        # Para Nomes Comerciais, muitas vezes não tem logo visual, é só texto.
        # Mas vamos tentar extrair sempre se achar a âncora "consiste em:"
        
        anchor_phrase = "O nome consiste em" if self.current_context['type'] == 'nome_comercial' else "O logotipo consiste em"
        anchor_rects = page.search_for(anchor_phrase, clip=record_rect)
        
        if anchor_rects and self.current_context['type'] == 'logotipo':
             # (Lógica de crop igual para LOGOTIPOS)
             # ...
             anchor = anchor_rects[-1]
             logo_x0 = anchor.x0 
             logo_y0 = anchor.y1 + 10 
             logo_area = fitz.Rect(logo_x0, logo_y0, record_rect.x1 - 50, record_rect.y1 - 10)
             if logo_area.height > 30 and logo_area.width > 30:
                 pix = page.get_pixmap(clip=logo_area, dpi=150)
                 filename = f"logo_{process_number.replace('/', '_')}.png"
                 full_path = os.path.join(img_dir, filename)
                 pix.save(full_path)
                 saved_img_path = f"ipi_images/{filename}"
                 self.stats['images_extracted'] += 1

        # 2. Persistir no Banco (IpiRecord)
        existing = IpiRecord.query.filter_by(process_number=process_number).first()
        if not existing:
            deadline = None
            if self.current_context['status'] == 'pedido' and self.current_context['bulletin_date']:
                deadline = self.current_context['bulletin_date'] + timedelta(days=30)

            final_brand_name = brand_name_override or "Marca Figurativa (Logo)"

            rec = IpiRecord(
                process_number=process_number,
                record_type=self.current_context['type'],
                status=self.current_context['status'],
                applicant_name=applicant or "Desconhecido",
                brand_name=final_brand_name,
                bulletin_number=self.current_context['bulletin_num'],
                publication_date=self.current_context['bulletin_date'],
                opposition_deadline=deadline,
                image_path=saved_img_path
            )
            db.session.add(rec)
            try:
                db.session.commit()
                self.stats['records_created'] += 1
            except:
                db.session.rollback()

    def extract_generic_brands(self, text):
        """Versão simplificada para capturar marcas genéricas do texto, similar ao script anterior mas populando IpiRecord"""
        # (Lógica Regex simplificada para brevidade, foco nos logotipos agora)
        pass

    def extract_field(self, text, regex):
        match = re.search(regex, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    def save_summary(self):
        print("\n📊 RESUMO DA IMPORTAÇÃO IPI:")
        print(f"   - Páginas: {self.stats['processed_pages']}")
        print(f"   - Registros IPI Criados: {self.stats['records_created']}")
        print(f"   - Imagens Extraídas: {self.stats['images_extracted']}")

