# tickapp/assets/__init__.py
"""
Assets Dagster pour le pipeline de traitement des tickets
"""
from pathlib import Path
from dotenv import load_dotenv
from dagster import Definitions, load_assets_from_modules

# Charger le fichier .env automatiquement
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)

from . import message_pipeline
from .message_pipeline import (
    process_signal_message,
    notify_signal_success_sensor,
    notify_signal_failure_sensor
)

# Charger uniquement les assets du pipeline par message (utilisé par le sensor)
# L'ancien pipeline batch (signal, claude, transform, db) n'est plus utilisé
all_assets = load_assets_from_modules([message_pipeline])

# Importer les sensors
from tickapp.sensors import signal_message_sensor, signal_message_sensor_test

# Définitions Dagster
defs = Definitions(
    assets=all_assets,
    jobs=[process_signal_message],
    sensors=[
        signal_message_sensor, 
        signal_message_sensor_test,
        notify_signal_success_sensor,  # Notification de succès (une seule fois à la fin)
        notify_signal_failure_sensor   # Notification d'échec (une seule fois à la fin)
    ]
)

