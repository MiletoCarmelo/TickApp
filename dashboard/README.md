# TickApp Dashboard

Dashboard Dash moderne pour visualiser les données de tickets/reçus.

## Fonctionnalités

- 📊 **Métriques principales** : Total dépensé, nombre de transactions, moyenne, magasins différents
- 📈 **Graphiques interactifs** :
  - Évolution des dépenses dans le temps
  - Répartition des dépenses par catégorie (camembert)
  - Top 15 magasins (graphique en barres)
- 📋 **Table des transactions récentes** avec pagination
- 🔄 **Rafraîchissement automatique** toutes les minutes

## Installation

Le dashboard est configuré pour fonctionner avec Docker Compose. Il se connecte automatiquement à la base de données PostgreSQL configurée dans `.env`.

## Utilisation

### Avec Docker Compose

```bash
# Démarrer tous les services (y compris le dashboard)
docker-compose up -d

# Le dashboard sera accessible sur http://localhost:8050
```

### Configuration

Le dashboard utilise les mêmes variables d'environnement que le reste de l'application (définies dans `.env`) :

- `DB_HOST` : Hôte PostgreSQL (défaut: localhost)
- `DB_PORT` : Port PostgreSQL (défaut: 5434)
- `DB_NAME` : Nom de la base de données (défaut: receipt_processing)
- `DB_USER` : Utilisateur PostgreSQL
- `DB_PASSWORD` : Mot de passe PostgreSQL

Le port du dashboard peut être configuré via `DASHBOARD_PORT` dans `.env` (défaut: 8050).

### Accès via Tailscale

Pour rendre le dashboard accessible via Tailscale :

1. Assurez-vous que votre machine est connectée à Tailscale
2. Le dashboard écoute sur `0.0.0.0:8050` par défaut
3. Accédez au dashboard via l'IP Tailscale de votre machine : `http://[tailscale-ip]:8050`

Pour une configuration plus sécurisée, vous pouvez :
- Ajouter une authentification au dashboard
- Utiliser un reverse proxy (nginx) avec SSL
- Restreindre l'accès par IP dans le code

## Développement

Pour développer localement sans Docker :

```bash
# Installer les dépendances avec Poetry (depuis la racine du projet)
poetry install

# Lancer le dashboard
cd dashboard
poetry run python app.py
```

## Structure

- `app.py` : Application Dash principale
- `Dockerfile` : Image Docker pour le dashboard (utilise Poetry)
- `README.md` : Ce fichier

**Note** : Les dépendances sont gérées par Poetry dans le `pyproject.toml` à la racine du projet.

