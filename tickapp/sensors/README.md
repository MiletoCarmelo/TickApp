# Sensors Dagster

Ce dossier contient les sensors Dagster qui détectent automatiquement les événements et déclenchent les pipelines.

## Sensor Signal

### `signal_message_sensor`

Sensor qui détecte automatiquement les nouveaux messages Signal avec des images de tickets et déclenche le pipeline de traitement pour chaque nouveau message.

**Fonctionnement :**
1. Vérifie toutes les 20 minutes s'il y a de nouveaux messages Signal
2. Filtre les messages avec des images de tickets
3. Vérifie en base de données quels messages n'ont pas encore été traités
4. Pour chaque nouveau message, déclenche un run du job `process_signal_message`

**Configuration :**
- `minimum_interval_seconds=1200` : Vérifie toutes les 20 minutes (1200 secondes)

**Pipeline déclenché :**
Le sensor déclenche le job `process_signal_message` qui exécute :
1. `get_message_from_signal` : Récupère le message depuis Signal
2. `insert_message_in_db` : Insère le message en base de données
3. `extract_with_claude` : Extrait les données avec Claude API
4. `transform_receipt` : Transforme l'extraction en ReceiptData
5. `insert_receipt_in_db` : Insère le ticket dans la base de données

**Avantages :**
- Traitement automatique des nouveaux messages
- Un pipeline par message (isolation des erreurs)
- Pas de duplication (vérifie en base avant de traiter)
- Traitement périodique (vérification toutes les 20 minutes)

## Utilisation

Le sensor est automatiquement chargé dans `tickapp/assets/__init__.py` et sera actif lorsque vous lancez Dagster :

```bash
dagster dev
```

Dans l'interface Dagster, vous verrez :
- Le sensor `signal_message_sensor` dans la section "Sensors"
- Les runs automatiques déclenchés pour chaque nouveau message
- L'historique des runs dans "Runs"

