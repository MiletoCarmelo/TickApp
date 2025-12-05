"""
Configuration du dashboard TickApp
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('POSTGRE_HOST', 'localhost'),  # Changé DB_HOST → POSTGRE_HOST
    'port': int(os.getenv('POSTGRES_PORT', '5434')),  # Changé DB_PORT → POSTGRES_PORT
    'database': os.getenv('POSTGRES_DB', 'receipt_processing'),  # Changé DB_NAME → POSTGRES_DB
    'user': os.getenv('POSTGRES_USER', 'receipt_user'),  # Changé DB_USER → POSTGRES_USER
    'password': os.getenv('POSTGRES_PASSWORD', 'SuperSecretPassword123!')  # Changé DB_PASSWORD → POSTGRES_PASSWORD
}

# Palette de couleurs
COLORS = {
    'primary': '#6366F1',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'chart': ['#6366F1', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B']
}

