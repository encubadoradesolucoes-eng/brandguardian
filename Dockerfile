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

# Criar pastas persistentes
RUN mkdir -p database uploads

# Definir porta
ENV PORT=7000
EXPOSE 7000

# Comando de arranque
CMD ["gunicorn", "--bind", "0.0.0.0:7000", "--timeout", "120", "app:app"]
