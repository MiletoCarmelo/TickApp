#!/bin/bash

echo "🗑️  Suppression de la base de données..."
docker-compose down -v

echo "🚀 Recréation de la base de données..."
docker-compose up -d

echo "⏳ Attente de l'initialisation..."
sleep 5

# Attendre que PostgreSQL soit prêt
echo "⏳ Attente que PostgreSQL soit prêt..."
until docker exec receipt-postgres pg_isready -U receipt_user -d receipt_processing > /dev/null 2>&1; do
    echo "   En attente..."
    sleep 2
done

echo ""
echo "📝 Exécution des scripts SQL d'initialisation..."
echo ""

# Exécuter les scripts SQL dans l'ordre
echo "1️⃣  Création des tables..."
docker exec -i receipt-postgres psql -U receipt_user -d receipt_processing < pg/init_scripts/01-creation-tables.sql

echo "2️⃣  Insertion des données de référence..."
docker exec -i receipt-postgres psql -U receipt_user -d receipt_processing < pg/init_scripts/02-post-creation.sql

# Vérifier si le fichier de vues existe avant de l'exécuter
if [ -f "pg/init_scripts/03-creation-views.sql" ]; then
    echo "3️⃣  Création des vues..."
    docker exec -i receipt-postgres psql -U receipt_user -d receipt_processing < pg/init_scripts/03-creation-views.sql
else
    echo "3️⃣  Fichier de vues non trouvé, ignoré."
fi

echo ""
echo "✅ Base de données réinitialisée !"
echo ""
echo "📊 Vérification des tables:"
docker exec -it receipt-postgres psql -U receipt_user -d receipt_processing -c "\dt"
echo ""
echo "📊 Nombre de catégories:"
docker exec -it receipt-postgres psql -U receipt_user -d receipt_processing -c "SELECT COUNT(*) FROM item_category;"