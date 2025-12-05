"""
Fonctions de récupération et traitement des données
"""
import streamlit as st
import pandas as pd
import psycopg2
from config import DB_CONFIG


@st.cache_data(ttl=60)
def get_daily_spending_summary(from_date=None, to_date=None):
    """Récupère les données de récapitulatif des dépenses quotidiennes depuis la base de données"""
    query = """
    SELECT * FROM daily_spending_summary
    WHERE transaction_date >= %s AND transaction_date <= %s
    ORDER BY transaction_date DESC
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql_query(query, conn, params=(from_date, to_date))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching daily spending summary: {e}")
        return pd.DataFrame()
