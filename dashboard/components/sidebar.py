"""
Composant Sidebar du dashboard

"""
import streamlit as st
from datetime import datetime, timedelta
from data import get_transactions_data


def render_sidebar():
    """Affiche la sidebar avec navigation et statistiques"""
    with st.sidebar:
        
        # Main navigation
        page = st.radio(
            "",
            [
                "🏠 Dashboard",
                "📊 Analytics", 
                "🏪 Stores",
                "📂 Categories",
                "📋 History",
                "💳 Transactions",
                "⚙️ Settings"
            ]
        )
        
        # Stats card
        try:
            df_quick = get_transactions_data()
            month_total = df_quick[df_quick["transaction_date"] >= datetime.now() - timedelta(days=30)]["total"].sum()
            week_total = df_quick[df_quick["transaction_date"] >= datetime.now() - timedelta(days=7)]["total"].sum()
            
            st.markdown(f"""
            <div class="sidebar-stats">
                <div class="stat-label">This Month</div>
                <div class="stat-value">{month_total:.0f} CHF</div>
                <div class="stat-secondary">Last 7 days: {week_total:.0f} CHF</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            pass
    
    return page

