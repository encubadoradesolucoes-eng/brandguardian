FROM python:3.11-slim

# Instalar Node.js e ferramentas do sistema
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -sL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependências de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o projeto
COPY . .

# Instalar dependências do WhatsApp Engine durante o Build
WORKDIR /app/whatsapp-engine
RUN npm install
WORKDIR /app

# Criar pastas persistentes
RUN mkdir -p database uploads

# Definir porta
ENV PORT=7000
EXPOSE 7000

# Dar permissão de execução ao script de arranque
RUN chmod +x /app/start.sh

# Comando de arranque via script
CMD ["/app/start.sh"]
