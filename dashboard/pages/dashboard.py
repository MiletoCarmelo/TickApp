"""
Page Dashboard principale
"""
import streamlit as st
from datetime import datetime, timedelta
from data import get_transactions_data, filter_data


def render():
    """Affiche la page Dashboard"""
    st.markdown("# Dashboard")
    st.caption("Real-time expense analytics and insights")
    
    try:
        df = get_transactions_data()
        
        # Filtres
        cols = st.columns([2, 2, 2, 1])
        with cols[0]:
            date_range = st.date_input(
                "Period", 
                value=(datetime.now() - timedelta(days=30), datetime.now()), 
                label_visibility="collapsed"
            )
        with cols[1]:
            categories = st.multiselect(
                "Categories", 
                df["transaction_category"].dropna().unique(), 
                default=None, 
                label_visibility="collapsed", 
                placeholder="All categories"
            )
        with cols[2]:
            stores_f = st.multiselect(
                "Stores", 
                df["store_name"].unique(), 
                default=None, 
                label_visibility="collapsed", 
                placeholder="All stores"
            )
        with cols[3]:
            if st.button("↻"):
                st.cache_data.clear()
                st.rerun()
        
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range[0] if date_range else None
        
        df_filtered = filter_data(df, start_date, end_date, categories, stores_f)
        
        # KPIs
        cols = st.columns(4)
        
        total = df_filtered["total"].sum()
        cols[0].metric("Total Spent", f"{total:.0f} CHF")
        
        transactions = len(df_filtered)
        cols[1].metric("Transactions", f"{transactions:,}")
        
        avg = df_filtered["total"].mean() if len(df_filtered) > 0 else 0
        cols[2].metric("Average", f"{avg:.0f} CHF")
        
        stores = df_filtered["store_name"].nunique()
        cols[3].metric("Stores", f"{stores}")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")

