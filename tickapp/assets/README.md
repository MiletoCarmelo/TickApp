# Assets Dagster - Pipeline de traitement des tickets

Ce dossier contient les assets Dagster qui orchestrent le pipeline complet de traitement des tickets de caisse.

## Architecture du pipeline

```
signal_messages
    ↓
signal_messages_in_db
    ↓
claude_extractions_from_messages
    ↓
transformed_receipts
    ↓
receipts_in_db
```

## Assets

### 1. `signal.py`

- **`signal_messages`** : Reçoit les messages Signal et télécharge les attachments
- **`signal_messages_in_db`** : Insère les messages Signal dans la base de données

### 2. `claude.py`

- **`claude_extractions_from_messages`** : Appelle Claude API pour extraire les données des tickets depuis les images

### 3. `transform.py`

- **`transformed_receipts`** : Transforme les extractions JSON de Claude en objets `ReceiptData`

### 4. `db.py`

- **`receipts_in_db`** : Insère les tickets transformés dans la base de données

## Variables d'environnement requises

Créez un fichier `.env` à la racine du projet avec :

```bash
# Signal
SIGNAL_PHONE_NUMBER=+33695071416

# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# Base de données
DB_HOST=localhost
DB_PORT=5434
DB_NAME=receipt_processing
DB_USER=receipt_user
DB_PASSWORD=SuperSecretPassword123!
```

## Configuration Dagster

Le fichier `.env` est automatiquement chargé dans `tickapp/assets/__init__.py` lors de l'import du module, donc les variables d'environnement sont disponibles pour vos assets Python.

## Utilisation

### Lancer Dagster (méthode classique)

```bash
# Activer l'environnement
poetry shell

# Lancer le serveur Dagster
dagster dev -m tickapp.assets
```

Ou avec `dagster-webserver` :

```bash
dagster-webserver -m tickapp.assets
```

### Exécuter le pipeline

1. Ouvrir l'interface Dagster : http://localhost:3000
2. Sélectionner les assets à exécuter
3. Cliquer sur "Materialize"

### Exécuter via code

```python
from tickapp.assets import defs

# Exécuter tous les assets
result = defs.get_implicit_global_asset_job_def().execute_in_process()
```

## Notes

- Les assets sont configurés pour fonctionner en séquence avec des dépendances automatiques
- Chaque asset log ses actions via `context.log`
- Les erreurs sont gérées et loggées sans interrompre le pipeline complet
- Le fichier `.env` est chargé automatiquement dans `__init__.py` pour les assets Python
- Le fichier `dagster.yaml` utilise les variables d'environnement pour la configuration PostgreSQL
