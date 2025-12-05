"""
Page Dashboard principale
"""
import streamlit as st
from datetime import datetime, timedelta
from data import get_daily_spending_summary
from components.styles import load_styles

# Charger les styles
load_styles()

st.markdown("# This month's spending overview")
st.caption("Monthly spending overview")

# Filtrer par défaut sur le mois en cours
start_of_month = datetime.now().replace(day=1)
today = datetime.now()

try:        

        ############################ Inputs ############################
        
        # Filtres
        cols = st.columns([4, 4, 4, 2, 1])
        with cols[0]:
            date_range = st.date_input(
                "Period", 
                value=(start_of_month, today), 
                label_visibility="collapsed"
            )

        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range[0]   

        from_date_last_month = start_date.replace(month=start_date.month - 1)
        to_date_last_month = end_date.replace(month=end_date.month - 1)

        df_daily_spending_summary = get_daily_spending_summary(
            from_date=start_date, 
            to_date=end_date)

        if df_daily_spending_summary.empty:
            st.warning("No daily spending summary data available")
        
        df_daily_spending_summary_last_month = get_daily_spending_summary(
            from_date=from_date_last_month,
            to_date=to_date_last_month
        )

        if df_daily_spending_summary_last_month.empty:
            st.warning("No daily spending summary data available for last month")


        with cols[1]:
            # Vérifier si la colonne existe
            groups = df_daily_spending_summary["group"].dropna().unique()
            if "group" in df_daily_spending_summary.columns:
                groups = st.multiselect(
                    "Groups", 
                    groups, 
                    default=None, 
                    label_visibility="collapsed", 
                    placeholder="All groups"
                )
            else:   
                groups = None
                st.info("No groups available")

        with cols[2]:
            stores = df_daily_spending_summary["store_name"].dropna().unique()
            stores_filter = st.multiselect(
                "Stores", 
                stores, 
                default=None, 
                label_visibility="collapsed", 
                placeholder="All stores"
            )

        with cols[3]:
            # selector cumulated spending or daily spending
            cumulated_spending = st.radio(
                "Cumulated Spending",
                ["Yes", "No"],
                index=1,
                label_visibility="collapsed",
                horizontal=True
            )


        with cols[4]:
            if st.button("↻"):
                st.cache_data.clear()
                st.rerun()
        
        
        df_daily_spending_summary_filtered = df_daily_spending_summary
        df_daily_spending_summary_last_month_filtered = df_daily_spending_summary_last_month
        
        if groups:
            df_daily_spending_summary_filtered = df_daily_spending_summary_filtered[df_daily_spending_summary_filtered["group"].isin(groups)]
            df_daily_spending_summary_last_month_filtered = df_daily_spending_summary_last_month_filtered[df_daily_spending_summary_last_month_filtered["group"].isin(groups)]
        if stores_filter:
            df_daily_spending_summary_filtered = df_daily_spending_summary_filtered[df_daily_spending_summary_filtered["store_name"].isin(stores_filter)]
            df_daily_spending_summary_last_month_filtered = df_daily_spending_summary_last_month_filtered[df_daily_spending_summary_last_month_filtered["store_name"].isin(stores_filter)]

        ############################ KPIs ############################################
        
        # mettre un espace vertical pour séparer les charts
        st.space(20)

        cols_kpis = st.columns(4)
        
        total = df_daily_spending_summary_filtered["amout"].sum()
        total_last_month = df_daily_spending_summary_last_month_filtered["amout"].sum()
        cols_kpis[0].metric(
            label ="Total Spent", 
            value = f"{total:.0f} CHF",
            delta = f"{total - total_last_month:.0f} CHF",
            delta_color = "inverse",
            help = "Total amount spent this month",
            border=True,
        )
        
        transactions = len(df_daily_spending_summary_filtered)
        transactions_last_month = len(df_daily_spending_summary_last_month_filtered)
        cols_kpis[1].metric(
            "Transactions", f"{transactions:,}",
            delta = f"{transactions - transactions_last_month:,}",
            delta_color = "off",
            help = "Total number of transactions this month",
            border=True,
        )
        
        avg = df_daily_spending_summary_filtered["amout"].mean() if len(df_daily_spending_summary_filtered) > 0 else 0
        avg_last_month = df_daily_spending_summary_last_month_filtered["amout"].mean() if len(df_daily_spending_summary_last_month_filtered) > 0 else 0
        cols_kpis[2].metric(
            "Average", f"{avg:.0f} CHF",
            delta = f"{avg - avg_last_month:.0f} CHF",
            delta_color = "inverse",
            help = "Average amount spent per transaction this month",
            border=True,
        )
        
        stores = df_daily_spending_summary_filtered["store_name"].nunique()
        stores_last_month = df_daily_spending_summary_last_month_filtered["store_name"].nunique()
        cols_kpis[3].metric(
            "Stores", f"{stores}",
            delta = f"{stores - stores_last_month}",
            delta_color = "off",
            help = "Total number of stores this month",
            border=True,
        )
        

        ############################ Stats card in the sidebar ############################################ 
        
        with st.sidebar:
            st.markdown(f"""
            <div class="sidebar-stats">
                <div class="stat-label">This Month</div>
                <div class="stat-value">{total:.0f} CHF</div>
                <div class="stat-secondary">Last Month: {total_last_month:.0f} CHF</div>
            </div>
            """, unsafe_allow_html=True)

        ############################ Charts ############################################

        # mettre un espace vertical pour séparer les charts
        st.space(20)

        charts_cols = st.columns(2)
        # Chart of the total spending by group
        charts_cols[0].line_chart(
            df_daily_spending_summary_filtered, 
            x="transaction_date", 
            y="amout", 
            color="group"
        )

        # Chart of the total spending by store
        charts_cols[1].bar_chart(
            df_daily_spending_summary_filtered, 
            x="store_name", 
            y="amout", 
            color="store_name"
        )
    
except Exception as e:
    st.error(f"Error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())