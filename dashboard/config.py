"""
Configuration du dashboard TickApp
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'receipt_processing'),
    'user': os.getenv('DB_USER', 'receipt_user'),
    'password': os.getenv('DB_PASSWORD', 'SuperSecretPassword123!')
}

# Palette de couleurs
COLORS = {
    'primary': '#6366F1',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'chart': ['#6366F1', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B']
}

