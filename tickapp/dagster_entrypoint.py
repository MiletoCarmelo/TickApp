#!/usr/bin/env python
"""
Point d'entrée pour Dagster qui charge automatiquement le fichier .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger le fichier .env depuis la racine du projet
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Fichier .env chargé depuis {env_file}")
else:
    print(f"⚠️  Fichier .env non trouvé à {env_file}")

# Importer et lancer Dagster
from tickapp.assets import defs

if __name__ == "__main__":
    from dagster import DagsterInstance
    from dagster._cli import main
    
    # Lancer la CLI Dagster
    main()

