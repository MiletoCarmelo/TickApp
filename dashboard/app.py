"""
TickApp Dashboard - Page principale
"""
import streamlit as st
from components.styles import load_styles

# Configuration
st.set_page_config(
    page_title="TickApp",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger les styles
load_styles()

# Redirection automatique vers Dashboard
st.switch_page("pages/1_🏠_Dashboard.py")
