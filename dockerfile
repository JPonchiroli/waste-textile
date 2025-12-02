# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# instala dependências do sistema (se matplotlib precisar de gcc etc.)
RUN apt-get update && apt-get install -y gcc g++ gfortran && rm -rf /var/lib/apt/lists/*

# copia requirements primeiro → cache de camadas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia o restante do código
COPY . .

# garante que o Flask escute em 0.0.0.0
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5001

EXPOSE 5001

CMD ["python", "app.py"]   # ou gunicorn -b 0.0.0.0:5001 app:app