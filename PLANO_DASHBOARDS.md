# Plano de Implementação: Dashboards Separados por Role

## Estrutura de Dashboards

### 1. Dashboard M24 (Admin/Super)
- **Rota**: `/dashboard` (atual, mas com verificação de role)
- **Acesso**: `role == 'admin'`
- **Funcionalidades**:
  - Ver TODAS as entidades (todos os usuários client)
  - Ver TODOS os agentes (todos os usuários agent)
  - Estatísticas globais
  - Gestão de usuários
  - Gestão de planos

### 2. Dashboard Agente PI
- **Rota**: `/agent-dashboard`
- **Acesso**: `role == 'agent'`
- **Funcionalidades**:
  - Dashboard de clientes do agente
  - Prospector de oportunidades
  - Relatórios white-label
  - Suas próprias marcas (se tiver)
  - **NÃO VÊ**: Outros agentes

### 3. Dashboard Entidade (Cliente)
- **Rota**: `/client-dashboard`
- **Acesso**: `role == 'client'`
- **Funcionalidades**:
  - Apenas suas próprias marcas
  - Seus alertas
  - Seus relatórios
  - **NÃO VÊ**: Outras entidades, agentes

## Redirecionamento Inteligente

Quando usuário acessa `/dashboard`, redirecionar baseado no role:
- `admin` → `/dashboard` (mantém)
- `agent` → `/agent-dashboard`
- `client` → `/client-dashboard`

## Arquivos a Criar/Modificar

### Templates:
1. `templates/agent_dashboard.html` (NOVO)
2. `templates/client_dashboard.html` (NOVO)
3. `templates/dashboard.html` (MODIFICAR - adicionar filtros admin)

### Rotas (app.py):
1. `@app.route('/agent-dashboard')` (NOVO)
2. `@app.route('/client-dashboard')` (NOVO)
3. `@app.route('/dashboard')` (MODIFICAR - adicionar redirecionamento)

## Implementação

Vou criar os arquivos na seguinte ordem:
1. Rota de redirecionamento inteligente
2. Template client_dashboard.html
3. Rota /client-dashboard
4. Template agent_dashboard.html
5. Rota /agent-dashboard
6. Modificar dashboard.html para admin
