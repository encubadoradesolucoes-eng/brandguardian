# 🧪 GUIA DE TESTE RÁPIDO - M24 PRO

## ⚡ TESTE EM 5 MINUTOS

### 1. Preparação (1 min)

```bash
# Instalar dependências
pip install -r requirements.txt

# Migrar base de dados
python migrate_db.py

# Popular planos
python seed_plans.py

# Iniciar aplicação
python app.py
```

### 2. Login (30 seg)

- Acesse: `http://localhost:7000`
- Login: `admin` / `admin123`
- Ou crie nova conta em `/signup`

### 3. Testar Monitoramento RPI (1 min)

```bash
# Em outro terminal
python
>>> from scheduler import check_new_rpi
>>> from app import app, db
>>> with app.app_context():
...     check_new_rpi(app, db)
```

### 4. Testar Página de Pricing (1 min)

- Acesse: `http://localhost:7000/pricing`
- Clique em "Fazer Upgrade" no plano Professional
- Selecione "M-Pesa"
- Digite número: `840000000`
- Confirme

**Resultado Esperado**:
- ✅ Pagamento processado (simulador)
- ✅ Assinatura ativada
- ✅ Email enviado
- ✅ Redirecionamento para /pricing

### 5. Testar Conflitos (1 min)

- Acesse: `http://localhost:7000/conflicts`
- Veja dashboard de conflitos
- (Vazio inicialmente - aguardando RPI real)

### 6. Gerar Relatório PDF (30 seg)

```python
# No terminal Python
from modules.report_generator import BrandReportGenerator
from app import User, Brand

user = User.query.get(1)
brands = Brand.query.filter_by(user_id=1).all()
gen = BrandReportGenerator()
filepath = gen.generate_brand_portfolio_report(user, brands)
print(f"Relatório: {filepath}")
```

---

## 🎯 CHECKLIST DE FUNCIONALIDADES

### Core Features:
- [ ] Login/Signup funcionando
- [ ] Dashboard carregando
- [ ] Registro de marcas
- [ ] Análise de similaridade

### Fase 1 (Monitoramento):
- [ ] Scheduler iniciando
- [ ] RPI scraper funcionando
- [ ] Conflitos sendo detectados
- [ ] Emails de alerta enviados

### Fase 2 (Relatórios):
- [ ] Página de pricing carregando
- [ ] Planos exibidos corretamente
- [ ] Relatórios PDF sendo gerados
- [ ] Download funcionando

### Fase 3 (Pagamentos):
- [ ] Modal de pagamento abrindo
- [ ] Campo de telefone aparecendo (M-Pesa)
- [ ] Pagamento processando
- [ ] Assinatura ativando
- [ ] Email de confirmação enviado

---

## 🐛 TROUBLESHOOTING

### Erro: "ModuleNotFoundError: No module named 'apscheduler'"
```bash
pip install APScheduler==3.10.4
```

### Erro: "ModuleNotFoundError: No module named 'reportlab'"
```bash
pip install reportlab==4.0.7
```

### Scheduler não inicia
- Verificar se `use_reloader=False` em `app.py`
- Verificar logs no console

### Pagamento não processa
- Verificar se `Payment` model foi criado
- Rodar `python migrate_db.py` novamente

### Email não envia
- Verificar credenciais em `app.py` (linhas 90-94)
- Verificar conexão internet

---

## 📊 DADOS DE TESTE

### Usuários:
- **Admin**: `admin` / `admin123`
- **Cliente**: Criar em `/signup`

### Números M-Pesa (Simulador):
- `840000000` - Sempre funciona
- `841111111` - Sempre funciona
- Qualquer número 84XXXXXXX - 90% sucesso

### Planos:
- **Free**: 0 MT - Sem pagamento
- **Starter**: 2.500 MT
- **Professional**: 8.000 MT (Recomendado)
- **Business**: 18.000 MT
- **Enterprise**: Sob consulta

---

## 🚀 PRÓXIMOS PASSOS

Após testar tudo:

1. **Reconstruir Executável**:
```bash
.\build_exe.bat
```

2. **Configurar Produção**:
- Obter credenciais M-Pesa reais
- Configurar `.env`
- Mudar `use_simulator=False`

3. **Deploy**:
- Heroku, Render, ou VPS
- Configurar PostgreSQL
- Configurar HTTPS

---

**Dúvidas?** Consulte:
- `README_COMPLETO.md` - Visão geral
- `IMPLEMENTACAO_FASE1.md` - Monitoramento
- `IMPLEMENTACAO_FASE2.md` - Relatórios
- `IMPLEMENTACAO_FASE3.md` - Pagamentos
