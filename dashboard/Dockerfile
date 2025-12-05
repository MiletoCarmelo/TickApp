# Dockerfile pour le dashboard Streamlit
FROM python:3.11-slim

# Installer les dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer Poetry
RUN pip install poetry

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de configuration Poetry
COPY pyproject.toml poetry.lock* ./

# Installer les dépendances avec Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copier le code de l'application dashboard
# Note: Le volume mount dans docker-compose.yml monte ./dashboard dans /app
# donc on ne copie que pour le build initial, le volume mount écrase ensuite
COPY dashboard/ ./

# Créer le dossier assets s'il n'existe pas déjà
RUN mkdir -p assets

# Exposer le port pour Streamlit
EXPOSE 8501

# Commande par défaut pour Streamlit avec hot-reload
# Le WORKDIR est /app, donc app.py est directement accessible
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true", "--server.runOnSave", "true", "--server.fileWatcherType", "poll"]