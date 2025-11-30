# Se connecter à PostgreSQL
psql -U postgres

# Créer la base de données
CREATE DATABASE receipt_processing;

# Se connecter à la base
\c receipt_processing

# Exécuter le script
\i create_tables.sql

# Vérifier les tables créées
\dt