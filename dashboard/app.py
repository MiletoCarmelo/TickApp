"""
TickApp - Premium Sidebar Design
Inspired by modern hosting dashboards
Point d'entrée principal de l'application
"""
import streamlit as st

# Import des composants
from components.styles import load_styles
from components.sidebar import render_sidebar
from pages import dashboard, analytics, stores, categories, history, transactions, settings

# Configuration de la page
st.set_page_config(
    page_title="TickApp",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger les styles
load_styles()

# Afficher la sidebar et récupérer la page sélectionnée
page = render_sidebar()

# Router vers la page appropriée
if "Dashboard" in page:
    dashboard.render()
elif "Analytics" in page:
    analytics.render()
elif "Stores" in page:
    stores.render()
elif "Categories" in page:
    categories.render()
elif "History" in page:
    history.render()
elif "Transactions" in page:
    transactions.render()
elif "Settings" in page:
    settings.render()
