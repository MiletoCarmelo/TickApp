"""
Dashboard Streamlit pour visualiser les données de tickets/reçus
Version moderne et simple
"""
import os
from dotenv import load_dotenv
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import psycopg2
from datetime import datetime, timedelta

# Configuration de la page (doit être la première commande Streamlit)
st.set_page_config(
    page_title="TickApp Dashboard",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'receipt_processing'),
    'user': os.getenv('DB_USER', 'receipt_user'),
    'password': os.getenv('DB_PASSWORD', 'SuperSecretPassword123!')
}

# Palette de couleurs moderne
COLORS = {
    'primary': '#4F46E5',
    'secondary': '#06B6D4',
    'success': '#10B981',
    'warning': '#F59E0B',
    'categories': ['#4F46E5', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
}

# CSS personnalisé pour un look moderne
st.markdown("""
<style>
    /* Import de la police Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Appliquer Inter partout */
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Réduire les espacements */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 1400px !important;
    }
    
    /* Titre principal */
    h1 {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        margin-bottom: 0.25rem !important;
    }
    
    /* Sous-titre */
    .subtitle {
        color: #64748B;
        font-size: 0.85rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* Cartes métriques */
    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600 !important;
    }
    
    /* Réduire l'espace entre les graphiques */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    
    /* Style des filtres */
    .stDateInput label, .stMultiSelect label {
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600 !important;
        color: #64748B !important;
    }
    
    /* Hauteur réduite pour les graphiques */
    .js-plotly-plot {
        height: 180px !important;
    }
</style>
""", unsafe_allow_html=True)

# Fonction pour récupérer les données depuis PostgreSQL
@st.cache_data(ttl=60)
def get_transactions_data():
    """Récupère les données des transactions avec cache de 60 secondes."""
    query = """
    SELECT 
        t.transaction_id,
        t.transaction_date,
        t.transaction_time,
        t.total,
        t.currency,
        t.payment_method,
        s.store_name,
        s.city,
        tc.name as transaction_category,
        COUNT(DISTINCT i.item_id) as item_count
    FROM transaction t
    JOIN store s ON t.store_id = s.store_id
    LEFT JOIN transaction_category tc ON t.transaction_category_id = tc.category_id
    LEFT JOIN transaction_item_mapping tim ON t.transaction_id = tim.transaction_id
    LEFT JOIN item i ON tim.item_id = i.item_id
    GROUP BY t.transaction_id, s.store_id, tc.category_id
    ORDER BY t.transaction_date DESC, t.transaction_time DESC
    """
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    return df

def filter_transactions(df, start_date, end_date, categories):
    """Applique les filtres de date et de catégorie."""
    df_filtered = df.copy()
    if start_date:
        df_filtered = df_filtered[df_filtered["transaction_date"] >= pd.to_datetime(start_date)]
    if end_date:
        df_filtered = df_filtered[df_filtered["transaction_date"] <= pd.to_datetime(end_date)]
    if categories:
        df_filtered = df_filtered[df_filtered["transaction_category"].isin(categories)]
    return df_filtered

# Header
st.markdown("# 🧾 TickApp Dashboard")
st.markdown('<p class="subtitle">Analyse moderne des dépenses</p>', unsafe_allow_html=True)

# Charger les données
try:
    df = get_transactions_data()
    
    # Filtres dans une ligne compacte
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    
    with col_f1:
        date_range = st.date_input(
            "Période",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )
    
    with col_f2:
        categories = st.multiselect(
            "Catégories",
            options=df["transaction_category"].dropna().unique().tolist(),
            default=None,
            placeholder="Toutes les catégories"
        )
    
    with col_f3:
        st.markdown(f"""
        <div style='margin-top: 1.5rem; font-size: 0.75rem; color: #64748B;'>
            <strong>MàJ:</strong> {datetime.now().strftime('%H:%M')}
        </div>
        """, unsafe_allow_html=True)
    
    # Appliquer les filtres
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0] if date_range else None
    
    df_filtered = filter_transactions(df, start_date, end_date, categories)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total = df_filtered["total"].sum()
        st.metric("💰 Total dépensé", f"{total:.2f} CHF")
    
    with col2:
        transactions = len(df_filtered)
        st.metric("🛒 Transactions", f"{transactions}")
    
    with col3:
        avg = df_filtered["total"].mean() if len(df_filtered) > 0 else 0
        st.metric("📊 Moyenne", f"{avg:.2f} CHF")
    
    with col4:
        stores = df_filtered["store_name"].nunique()
        st.metric("🏪 Magasins", f"{stores}")
    
    # Graphique d'évolution (pleine largeur)
    st.markdown("### 📈 Évolution des dépenses")
    timeline = (
        df_filtered.groupby(df_filtered["transaction_date"].dt.date)["total"]
        .sum()
        .reset_index(name="total_spent")
        .sort_values("transaction_date")
    )
    
    fig_timeline = px.line(
        timeline,
        x="transaction_date",
        y="total_spent",
        labels={"transaction_date": "Date", "total_spent": "Montant (CHF)"}
    )
    fig_timeline.update_traces(
        line_color=COLORS['primary'],
        line_width=3,
        fill='tozeroy',
        fillcolor=f'rgba(79, 70, 229, 0.1)'
    )
    fig_timeline.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=180,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        font=dict(family="Inter", size=10),
        xaxis=dict(gridcolor='rgba(226, 232, 240, 0.5)'),
        yaxis=dict(gridcolor='rgba(226, 232, 240, 0.5)')
    )
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Graphiques côte à côte
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("### 🥧 Dépenses par catégorie")
        cat = (
            df_filtered.groupby("transaction_category")["total"]
            .sum()
            .reset_index(name="total_spent")
            .sort_values("total_spent", ascending=False)
        )
        
        fig_cat = px.pie(
            cat,
            values="total_spent",
            names="transaction_category",
            hole=0.5,
            color_discrete_sequence=COLORS['categories']
        )
        fig_cat.update_traces(
            textposition="outside",
            textinfo="percent+label",
            marker=dict(line=dict(color='white', width=2))
        )
        fig_cat.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=180,
            showlegend=True,
            font=dict(family="Inter", size=10)
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col_g2:
        st.markdown("### 🏪 Top 15 magasins")
        store = (
            df_filtered.groupby(["store_name", "city"])["total"]
            .sum()
            .reset_index(name="total_spent")
            .sort_values("total_spent", ascending=False)
            .head(15)
        )
        store["label"] = store["store_name"] + " (" + store["city"].fillna("") + ")"
        
        fig_store = px.bar(
            store,
            x="total_spent",
            y="label",
            orientation="h",
            labels={"total_spent": "Montant (CHF)", "label": "Magasin"}
        )
        fig_store.update_traces(
            marker_color=COLORS['secondary'],
            marker_line_width=0
        )
        fig_store.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=180,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis={"categoryorder": "total ascending"},
            yaxis_title="",
            font=dict(family="Inter", size=10),
            xaxis=dict(gridcolor='rgba(226, 232, 240, 0.5)')
        )
        st.plotly_chart(fig_store, use_container_width=True)
    
    # Table des transactions récentes
    st.markdown("### 📋 Transactions récentes")
    df_table = df_filtered.head(20).copy()
    df_table["Date"] = df_table["transaction_date"].dt.strftime("%d/%m/%Y")
    df_table["Montant"] = df_table["total"].apply(lambda x: f"{x:.2f} CHF")
    
    st.dataframe(
        df_table[["Date", "store_name", "city", "transaction_category", "Montant", "payment_method", "item_count"]]
        .rename(columns={
            "store_name": "Magasin",
            "city": "Ville",
            "transaction_category": "Catégorie",
            "payment_method": "Paiement",
            "item_count": "Articles"
        }),
        use_container_width=True,
        height=250,
        hide_index=True
    )

except Exception as e:
    st.error(f"Erreur de connexion à la base de données: {str(e)}")
    st.info("Vérifiez que PostgreSQL est accessible et que les variables d'environnement sont correctes.")