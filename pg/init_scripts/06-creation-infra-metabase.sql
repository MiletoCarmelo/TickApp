-- ============================================
-- Création de la base Metabase
-- ============================================
-- Ce script est exécuté automatiquement au premier démarrage de PostgreSQL
-- via le volume /docker-entrypoint-initdb.d

-- Créer la base de données Metabase
CREATE DATABASE metabase;

-- Donner tous les privilèges à l'utilisateur principal
GRANT ALL PRIVILEGES ON DATABASE metabase TO receipt_user;

-- Se connecter à la base metabase pour configurer les permissions
\c metabase

-- Donner les permissions sur le schéma public
GRANT ALL PRIVILEGES ON SCHEMA public TO receipt_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO receipt_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO receipt_user;

-- S'assurer que les futurs objets auront aussi les bonnes permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO receipt_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO receipt_user;