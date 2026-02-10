#!/usr/bin/env python3
"""Script para remover sidebar e voltar ao layout original"""

file_path = r"c:\Users\Acer\Documents\tecnologias\brandguardian\templates\scan_live.html"

# Ler o arquivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remover a sidebar adicionada
# Voltar para o layout original
content = content.replace(
    '<div class="row">\n    <!-- Terminal Principal -->\n    <div class="col-lg-8">',
    '<div class="row justify-content-center">\n    <div class="col-md-10">'
)

# Remover todo o bloco da sidebar até o fim
import re
sidebar_pattern = r'    </div><!-- Fim col-lg-8 Terminal -->.*?</div><!-- Fim row -->\n'
content = re.sub(sidebar_pattern, '', content, flags=re.DOTALL)

# Adicionar fechamento correto
if '{% endblock %}' in content and not '</div>\n</div>\n{% endblock %}' in content:
    content = content.replace('</script>\n{% endblock %}', '</script>\n        </div>\n    </div>\n</div>\n{% endblock %}')

# Escrever de volta
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Sidebar removida com sucesso!")
