"""
Fonctions de récupération et traitement des données
"""
import streamlit as st
import pandas as pd
import psycopg2
from config import DB_CONFIG


@st.cache_data(ttl=60)
def get_transactions_data():
    """Récupère les données de transactions depuis la base de données"""
    query = """
    SELECT t.transaction_id, t.transaction_date, t.transaction_time, t.total, t.currency,
           t.payment_method, s.store_name, s.city, tc.name as transaction_category,
           COUNT(DISTINCT i.item_id) as item_count
    FROM transaction t
    JOIN store s ON t.store_id = s.store_id
    LEFT JOIN transaction_category tc ON t.transaction_category_id = tc.category_id
    LEFT JOIN transaction_item_mapping tim ON t.transaction_id = tim.transaction_id
    LEFT JOIN item i ON tim.item_id = i.item_id
    GROUP BY t.transaction_id, s.store_id, tc.category_id
    ORDER BY t.transaction_date DESC, t.transaction_time DESC
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql_query(query, conn)
        conn.close()
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        return df
    except Exception as e:
        st.error(f"Error fetching transactions: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def get_items_by_category():
    """Récupère les données d'items par catégorie"""
    query = """
    SELECT ic.category_main, ic.category_sub, i.product_name, i.brand,
           SUM(i.quantity) as total_quantity, SUM(i.total_price) as total_spent,
           COUNT(DISTINCT t.transaction_id) as transaction_count
    FROM item i
    JOIN item_category ic ON i.category_id = ic.category_id
    JOIN transaction_item_mapping tim ON i.item_id = tim.item_id
    JOIN transaction t ON tim.transaction_id = t.transaction_id
    GROUP BY ic.category_main, ic.category_sub, i.product_name, i.brand
    ORDER BY total_spent DESC
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching items: {e}")
        return pd.DataFrame()


def filter_data(df, start_date, end_date, categories, stores=None):
    """
    Filtre les données selon les critères
    
    Args:
        df: DataFrame à filtrer
        start_date: Date de début
        end_date: Date de fin
        categories: Liste de catégories
        stores: Liste de magasins (optionnel)
    
    Returns:
        DataFrame filtré
    """
    df_filtered = df.copy()
    
    if start_date:
        df_filtered = df_filtered[df_filtered["transaction_date"] >= pd.to_datetime(start_date)]
    if end_date:
        df_filtered = df_filtered[df_filtered["transaction_date"] <= pd.to_datetime(end_date)]
    if categories:
        df_filtered = df_filtered[df_filtered["transaction_category"].isin(categories)]
    if stores:
        df_filtered = df_filtered[df_filtered["store_name"].isin(stores)]
    
    return df_filtered

