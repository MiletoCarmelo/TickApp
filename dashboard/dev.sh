#!/bin/bash
# Script pour lancer Streamlit en mode développement local
# Utilise la base de données Docker mais lance Streamlit localement

echo "🚀 Lancement de Streamlit en mode développement..."
echo "📊 Le dashboard sera accessible sur http://localhost:8501"
echo "🔄 Les changements seront détectés automatiquement (hot-reload)"
echo ""

# Aller dans le répertoire du projet
cd "$(dirname "$0")/.." || exit 1

# Vérifier que la base de données Docker est accessible
if ! docker ps | grep -q receipt-postgres; then
    echo "⚠️  La base de données Docker n'est pas démarrée."
    echo "💡 Lancez d'abord: docker-compose up -d postgres"
    exit 1
fi

# Vérifier que Poetry est installé
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry n'est pas installé."
    echo "💡 Installez Poetry: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Vérifier que les dépendances sont installées
if [ ! -d ".venv" ]; then
    echo "📦 Installation des dépendances avec Poetry..."
    poetry install --no-interaction
fi

# Lancer Streamlit avec Poetry (utilise l'environnement virtuel)
echo "🎯 Lancement de Streamlit..."
cd dashboard || exit 1
poetry run streamlit run app.py \
    --server.port 8501 \
    --server.address localhost \
    --server.headless false \
    --server.runOnSave true \
    --server.fileWatcherType poll

