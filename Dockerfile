FROM python:3.11-slim

# Instalar dependências do sistema para Python, Node e Puppeteer (Chrome)
RUN apt-get update && apt-get install -y \
    python3-pip \
    curl \
    gnupg \
    libnss3 \
    libnss3-tools \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libglib2.0-0 \
    libxkbcommon0 \
    libxshmfence1 \
    libnspr4 \
    && curl -sL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
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
