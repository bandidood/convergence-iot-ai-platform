FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements et installation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Créer utilisateur non-privilégié
RUN useradd -m -u 1001 iotgen && chown -R iotgen:iotgen /app
USER iotgen

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import paho.mqtt.client as mqtt; print('OK')"

CMD ["python", "iot_data_generator.py"]