"""
Dashboard Dash pour visualiser les données de tickets/reçus
"""
import os
from dotenv import load_dotenv
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import psycopg2
from datetime import datetime, timedelta

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5434')),
    'database': os.getenv('DB_NAME', 'receipt_processing'),
    'user': os.getenv('DB_USER', 'receipt_user'),
    'password': os.getenv('DB_PASSWORD', 'SuperSecretPassword123!')
}

# Initialiser l'application Dash avec un thème Bootstrap moderne
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True
)

app.title = "TickApp Dashboard - Analyse des Dépenses"

# Fonction pour récupérer les données depuis PostgreSQL
def get_db_connection():
    """Établit une connexion à la base de données"""
    return psycopg2.connect(**DB_CONFIG)

def get_transactions_data():
    """Récupère les données des transactions"""
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
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_spending_by_category():
    """Récupère les dépenses par catégorie"""
    query = """
    SELECT 
        tc.name as category,
        SUM(t.total) as total_spent,
        COUNT(t.transaction_id) as transaction_count
    FROM transaction t
    LEFT JOIN transaction_category tc ON t.transaction_category_id = tc.category_id
    GROUP BY tc.name
    ORDER BY total_spent DESC
    """
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_spending_by_store():
    """Récupère les dépenses par magasin"""
    query = """
    SELECT 
        s.store_name,
        s.city,
        SUM(t.total) as total_spent,
        COUNT(t.transaction_id) as transaction_count
    FROM transaction t
    JOIN store s ON t.store_id = s.store_id
    GROUP BY s.store_id, s.store_name, s.city
    ORDER BY total_spent DESC
    LIMIT 15
    """
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_spending_timeline():
    """Récupère l'évolution des dépenses dans le temps"""
    query = """
    SELECT 
        DATE(t.transaction_date) as date,
        SUM(t.total) as total_spent,
        COUNT(t.transaction_id) as transaction_count
    FROM transaction t
    GROUP BY DATE(t.transaction_date)
    ORDER BY date DESC
    """
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_top_items():
    """Récupère les articles les plus achetés"""
    query = """
    SELECT 
        i.product_name,
        i.brand,
        COUNT(DISTINCT tim.transaction_id) as purchase_count,
        SUM(i.total_price) as total_spent
    FROM item i
    JOIN transaction_item_mapping tim ON i.item_id = tim.item_id
    GROUP BY i.product_name, i.brand
    ORDER BY purchase_count DESC
    LIMIT 20
    """
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Layout de l'application
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-receipt me-2"),
                "TickApp Dashboard"
            ], className="text-center mb-4 mt-4"),
            html.P("Analyse des dépenses et tickets", className="text-center text-muted mb-4")
        ])
    ]),
    
    # Métriques principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="total-spent", className="text-primary"),
                    html.P("Total dépensé", className="text-muted mb-0")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="total-transactions", className="text-success"),
                    html.P("Transactions", className="text-muted mb-0")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="avg-transaction", className="text-info"),
                    html.P("Moyenne par transaction", className="text-muted mb-0")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id="total-stores", className="text-warning"),
                    html.P("Magasins différents", className="text-muted mb-0")
                ])
            ], className="text-center shadow-sm")
        ], md=3),
    ], className="mb-4"),
    
    # Graphiques principaux
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Évolution des dépenses"),
                dbc.CardBody([
                    dcc.Graph(id="spending-timeline")
                ])
            ], className="shadow-sm mb-4")
        ], md=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Dépenses par catégorie"),
                dbc.CardBody([
                    dcc.Graph(id="spending-by-category")
                ])
            ], className="shadow-sm mb-4")
        ], md=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Top 15 magasins"),
                dbc.CardBody([
                    dcc.Graph(id="spending-by-store")
                ])
            ], className="shadow-sm mb-4")
        ], md=6)
    ]),
    
    # Table des transactions récentes
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Transactions récentes"),
                dbc.CardBody([
                    html.Div(id="transactions-table")
                ])
            ], className="shadow-sm mb-4")
        ], md=12)
    ]),
    
    # Intervalle de rafraîchissement automatique
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Rafraîchir toutes les minutes
        n_intervals=0
    )
], fluid=True)

# Callbacks pour les métriques
@app.callback(
    [Output('total-spent', 'children'),
     Output('total-transactions', 'children'),
     Output('avg-transaction', 'children'),
     Output('total-stores', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics(n):
    try:
        df = get_transactions_data()
        total_spent = f"{df['total'].sum():.2f} CHF"
        total_transactions = len(df)
        avg_transaction = f"{df['total'].mean():.2f} CHF" if total_transactions > 0 else "0.00 CHF"
        total_stores = df['store_name'].nunique()
        return total_spent, total_transactions, avg_transaction, total_stores
    except Exception as e:
        return "Erreur", "Erreur", "Erreur", "Erreur"

# Callback pour le graphique d'évolution
@app.callback(
    Output('spending-timeline', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_timeline(n):
    try:
        df = get_spending_timeline()
        fig = px.line(
            df, 
            x='date', 
            y='total_spent',
            title='',
            labels={'date': 'Date', 'total_spent': 'Montant (CHF)'}
        )
        fig.update_traces(line_color='#0d6efd', line_width=3)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified'
        )
        return fig
    except Exception as e:
        return go.Figure()

# Callback pour le graphique par catégorie
@app.callback(
    Output('spending-by-category', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_category_chart(n):
    try:
        df = get_spending_by_category()
        fig = px.pie(
            df,
            values='total_spent',
            names='category',
            title='',
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    except Exception as e:
        return go.Figure()

# Callback pour le graphique par magasin
@app.callback(
    Output('spending-by-store', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_store_chart(n):
    try:
        df = get_spending_by_store()
        fig = px.bar(
            df,
            x='total_spent',
            y='store_name',
            orientation='h',
            title='',
            labels={'total_spent': 'Montant (CHF)', 'store_name': 'Magasin'},
            color='total_spent',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis={'categoryorder': 'total ascending'}
        )
        return fig
    except Exception as e:
        return go.Figure()

# Callback pour la table des transactions
@app.callback(
    Output('transactions-table', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_transactions_table(n):
    try:
        df = get_transactions_data()
        df = df.head(20)  # Limiter à 20 transactions récentes
        df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.strftime('%Y-%m-%d')
        df['total'] = df['total'].apply(lambda x: f"{x:.2f} CHF")
        
        table = dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {'name': 'Date', 'id': 'transaction_date'},
                {'name': 'Magasin', 'id': 'store_name'},
                {'name': 'Ville', 'id': 'city'},
                {'name': 'Catégorie', 'id': 'transaction_category'},
                {'name': 'Montant', 'id': 'total'},
                {'name': 'Paiement', 'id': 'payment_method'},
                {'name': 'Articles', 'id': 'item_count'}
            ],
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={
                'backgroundColor': '#0d6efd',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ],
            page_size=10
        )
        return table
    except Exception as e:
        return html.Div(f"Erreur: {str(e)}", className="text-danger")

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)

