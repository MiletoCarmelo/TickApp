#!/bin/bash
# Script pour tester le container Docker

echo "🔍 Test du container Docker..."
echo ""

# Démarrer le container en mode détaché
docker-compose up -d dashboard

# Attendre que le container démarre
sleep 3

# Vérifier les logs
echo "📋 Logs du container:"
docker-compose logs dashboard | tail -20

echo ""
echo "📁 Contenu de /app dans le container:"
docker-compose exec dashboard ls -la /app/ 2>/dev/null || echo "❌ Container non accessible"

echo ""
echo "🔍 Vérification du fichier app.py:"
docker-compose exec dashboard test -f /app/app.py && echo "✅ app.py existe" || echo "❌ app.py n'existe pas"

echo ""
echo "🔍 Vérification du WORKDIR:"
docker-compose exec dashboard pwd

