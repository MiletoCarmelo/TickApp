# Dockerfile pour le dashboard Dash - Version Moderne (Fixed)
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

# Installer les dépendances avec Poetry (sans installer le projet lui-même)
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copier le code de l'application dashboard
COPY dashboard/ ./

# Exposer le port pour Dash
EXPOSE 8050

# Commande par défaut
CMD ["python", "app.py"]