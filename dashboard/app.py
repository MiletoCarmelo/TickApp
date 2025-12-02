"""
Dashboard Dash pour visualiser les données de tickets/reçus
Version modernisée avec design épuré
"""
import os
from dotenv import load_dotenv
import dash
from dash import dcc, html, Input, Output, State, dash_table
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
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'receipt_processing'),
    'user': os.getenv('DB_USER', 'receipt_user'),
    'password': os.getenv('DB_PASSWORD', 'SuperSecretPassword123!')
}

# Initialiser l'application Dash avec thème moderne
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True
)

app.title = "TickApp Dashboard - Analyse des Dépenses"

# Fonction pour récupérer les données depuis PostgreSQL
def get_db_connection():
    """Établit une connexion à la base de données"""
    return psycopg2.connect(**DB_CONFIG)

def get_transactions_data():
    """Récupère les données des transactions (base pour tous les graphiques)."""
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
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    return df

def filter_transactions(df: pd.DataFrame, start_date: str | None, end_date: str | None, categories: list | None):
    """Applique les filtres de date et de catégorie sur le DataFrame."""
    if start_date:
        df = df[df["transaction_date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["transaction_date"] <= pd.to_datetime(end_date)]
    if categories:
        df = df[df["transaction_category"].isin(categories)]
    return df

# Palette de couleurs moderne
COLORS = {
    'primary': '#4F46E5',
    'secondary': '#06B6D4',
    'success': '#10B981',
    'warning': '#F59E0B',
    'categories': ['#4F46E5', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
}

# Layout de l'application
app.layout = dbc.Container(
    [
        # Header avec style moderne
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            [
                                html.I(className="fas fa-receipt me-3"),
                                "TickApp Dashboard"
                            ],
                            className="text-center mb-2 mt-4",
                            style={'fontWeight': '700', 'letterSpacing': '-0.025em'}
                        ),
                        html.P(
                            "Analyse moderne des dépenses par personne, magasin et catégorie",
                            className="text-center mb-4",
                            style={'color': '#64748B', 'fontSize': '1.1rem'}
                        ),
                    ]
                )
            ]
        ),
        
        # Filtres dans une card moderne
        dbc.Card(
            dbc.CardBody(
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("PÉRIODE", className="fw-bold small"),
                                dcc.DatePickerRange(
                                    id="date-range",
                                    display_format="DD/MM/YYYY",
                                    minimum_nights=0,
                                    start_date=(datetime.now() - timedelta(days=30)).date(),
                                    end_date=datetime.now().date(),
                                    style={'width': '100%'}
                                ),
                            ],
                            md=4,
                            className="mb-3 mb-md-0",
                        ),
                        dbc.Col(
                            [
                                html.Label("CATÉGORIES", className="fw-bold small"),
                                dcc.Dropdown(
                                    id="category-filter",
                                    options=[
                                        {"label": "🔵 Carmelo", "value": "carmelo"},
                                        {"label": "🟠 Heather", "value": "heather"},
                                        {"label": "🟢 Neon", "value": "neon"},
                                    ],
                                    placeholder="Toutes les catégories",
                                    multi=True,
                                    style={'borderRadius': '8px'}
                                ),
                            ],
                            md=4,
                            className="mb-3 mb-md-0",
                        ),
                        dbc.Col(
                            [
                                html.Label("DERNIÈRE MISE À JOUR", className="fw-bold small"),
                                html.Div(
                                    id="last-update",
                                    style={
                                        'padding': '0.5rem 1rem',
                                        'background': 'rgba(79, 70, 229, 0.05)',
                                        'borderRadius': '8px',
                                        'fontSize': '0.875rem',
                                        'fontWeight': '500',
                                        'color': '#64748B'
                                    }
                                ),
                            ],
                            md=4,
                        ),
                    ],
                ),
            ),
            className="mb-4",
            style={'borderRadius': '16px', 'border': '1px solid #E2E8F0'}
        ),
        
        # Métriques principales avec design moderne
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.I(className="fas fa-wallet me-2", style={'color': COLORS['primary']}),
                                        "Total dépensé"
                                    ],
                                    className="small mb-2",
                                    style={'color': '#64748B', 'fontWeight': '600'}
                                ),
                                html.H3(
                                    id="total-spent",
                                    className="mb-0",
                                    style={'color': COLORS['primary'], 'fontWeight': '700'}
                                ),
                            ],
                            style={'padding': '1.5rem'}
                        ),
                        className="h-100",
                        style={'borderRadius': '16px', 'border': '1px solid #E2E8F0', 'borderTop': f'4px solid {COLORS["primary"]}'}
                    ),
                    md=3,
                    className="mb-3",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.I(className="fas fa-shopping-cart me-2", style={'color': COLORS['success']}),
                                        "Transactions"
                                    ],
                                    className="small mb-2",
                                    style={'color': '#64748B', 'fontWeight': '600'}
                                ),
                                html.H3(
                                    id="total-transactions",
                                    className="mb-0",
                                    style={'color': COLORS['success'], 'fontWeight': '700'}
                                ),
                            ],
                            style={'padding': '1.5rem'}
                        ),
                        className="h-100",
                        style={'borderRadius': '16px', 'border': '1px solid #E2E8F0', 'borderTop': f'4px solid {COLORS["success"]}'}
                    ),
                    md=3,
                    className="mb-3",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.I(className="fas fa-chart-line me-2", style={'color': COLORS['secondary']}),
                                        "Moyenne"
                                    ],
                                    className="small mb-2",
                                    style={'color': '#64748B', 'fontWeight': '600'}
                                ),
                                html.H3(
                                    id="avg-transaction",
                                    className="mb-0",
                                    style={'color': COLORS['secondary'], 'fontWeight': '700'}
                                ),
                            ],
                            style={'padding': '1.5rem'}
                        ),
                        className="h-100",
                        style={'borderRadius': '16px', 'border': '1px solid #E2E8F0', 'borderTop': f'4px solid {COLORS["secondary"]}'}
                    ),
                    md=3,
                    className="mb-3",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.I(className="fas fa-store me-2", style={'color': COLORS['warning']}),
                                        "Magasins"
                                    ],
                                    className="small mb-2",
                                    style={'color': '#64748B', 'fontWeight': '600'}
                                ),
                                html.H3(
                                    id="total-stores",
                                    className="mb-0",
                                    style={'color': COLORS['warning'], 'fontWeight': '700'}
                                ),
                            ],
                            style={'padding': '1.5rem'}
                        ),
                        className="h-100",
                        style={'borderRadius': '16px', 'border': '1px solid #E2E8F0', 'borderTop': f'4px solid {COLORS["warning"]}'}
                    ),
                    md=3,
                    className="mb-3",
                ),
            ],
        ),
        
        # Graphique d'évolution en pleine largeur
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.I(className="fas fa-chart-area me-2"),
                                    "Évolution des dépenses"
                                ],
                                style={'background': 'linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)'}
                            ),
                            dbc.CardBody(
                                [dcc.Graph(id="spending-timeline", config={"displayModeBar": False})],
                                style={'padding': '1.5rem'}
                            ),
                        ],
                        style={'borderRadius': '16px', 'border': '1px solid #E2E8F0'}
                    ),
                    md=12,
                    className="mb-4"
                )
            ]
        ),
        
        # Graphiques côte à côte
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.I(className="fas fa-chart-pie me-2"),
                                    "Dépenses par catégorie"
                                ],
                                style={'background': 'linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)'}
                            ),
                            dbc.CardBody(
                                [dcc.Graph(id="spending-by-category", config={"displayModeBar": False})],
                                style={'padding': '1.5rem'}
                            ),
                        ],
                        style={'borderRadius': '16px', 'border': '1px solid #E2E8F0'}
                    ),
                    md=6,
                    className="mb-4",
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [
                                    html.I(className="fas fa-store me-2"),
                                    "Top 15 magasins"
                                ],
                                style={'background': 'linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)'}
                            ),
                            dbc.CardBody(
                                [dcc.Graph(id="spending-by-store", config={"displayModeBar": False})],
                                style={'padding': '1.5rem'}
                            ),
                        ],
                        style={'borderRadius': '16px', 'border': '1px solid #E2E8F0'}
                    ),
                    md=6,
                    className="mb-4",
                ),
            ]
        ),
        
        # Table des transactions récentes
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.I(className="fas fa-list me-2"),
                                "Transactions récentes"
                            ],
                            style={'background': 'linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)'}
                        ),
                        dbc.CardBody(
                            [html.Div(id="transactions-table")],
                            style={'padding': '1.5rem'}
                        ),
                    ],
                    style={'borderRadius': '16px', 'border': '1px solid #E2E8F0'}
                ),
                md=12,
                className="mb-4"
            )
        ),
        
        # Intervalle de rafraîchissement
        dcc.Interval(id="interval-component", interval=60 * 1000, n_intervals=0),
    ],
    fluid=True,
    style={'maxWidth': '1400px', 'padding': '2rem 1.5rem'}
)

# Callbacks pour les métriques
@app.callback(
    [
        Output("total-spent", "children"),
        Output("total-transactions", "children"),
        Output("avg-transaction", "children"),
        Output("total-stores", "children"),
        Output("last-update", "children"),
    ],
    [
        Input("interval-component", "n_intervals"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("category-filter", "value"),
    ],
)
def update_metrics(n, start_date, end_date, categories):
    try:
        df = get_transactions_data()
        df = filter_transactions(df, start_date, end_date, categories)
        if df.empty:
            return "0.00 CHF", "0", "0.00 CHF", "0", "Aucune donnée"
        total_spent = f"{df['total'].sum():.2f} CHF"
        total_transactions = f"{len(df)}"
        avg_transaction = f"{df['total'].mean():.2f} CHF"
        total_stores = f"{df['store_name'].nunique()}"
        last_update = datetime.now().strftime("%d/%m/%Y %H:%M")
        return total_spent, total_transactions, avg_transaction, total_stores, last_update
    except Exception:
        return "Erreur", "Erreur", "Erreur", "Erreur", "Erreur"

# Callback pour le graphique d'évolution
@app.callback(
    Output("spending-timeline", "figure"),
    [
        Input("interval-component", "n_intervals"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("category-filter", "value"),
    ],
)
def update_timeline(n, start_date, end_date, categories):
    try:
        df = get_transactions_data()
        df = filter_transactions(df, start_date, end_date, categories)
        if df.empty:
            return go.Figure()
        timeline = (
            df.groupby(df["transaction_date"].dt.date)["total"]
            .sum()
            .reset_index(name="total_spent")
            .sort_values("transaction_date")
        )
        fig = px.line(
            timeline,
            x="transaction_date",
            y="total_spent",
            labels={"transaction_date": "Date", "total_spent": "Montant (CHF)"},
        )
        fig.update_traces(
            line_color=COLORS['primary'],
            line_width=3,
            fill='tozeroy',
            fillcolor=f'rgba(79, 70, 229, 0.1)'
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
            font=dict(family="Inter, sans-serif", size=12, color="#64748B"),
            xaxis=dict(gridcolor='rgba(226, 232, 240, 0.5)'),
            yaxis=dict(gridcolor='rgba(226, 232, 240, 0.5)'),
            height=350
        )
        return fig
    except Exception:
        return go.Figure()

# Callback pour le graphique par catégorie
@app.callback(
    Output("spending-by-category", "figure"),
    [
        Input("interval-component", "n_intervals"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("category-filter", "value"),
    ],
)
def update_category_chart(n, start_date, end_date, categories):
    try:
        df = get_transactions_data()
        df = filter_transactions(df, start_date, end_date, categories)
        if df.empty:
            return go.Figure()
        cat = (
            df.groupby("transaction_category")["total"]
            .sum()
            .reset_index(name="total_spent")
            .sort_values("total_spent", ascending=False)
        )
        fig = px.pie(
            cat,
            values="total_spent",
            names="transaction_category",
            hole=0.5,
            color_discrete_sequence=COLORS['categories']
        )
        fig.update_traces(
            textposition="outside",
            textinfo="percent+label",
            marker=dict(line=dict(color='white', width=2))
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12, color="#64748B"),
            showlegend=True,
            height=350
        )
        return fig
    except Exception:
        return go.Figure()

# Callback pour le graphique par magasin
@app.callback(
    Output("spending-by-store", "figure"),
    [
        Input("interval-component", "n_intervals"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("category-filter", "value"),
    ],
)
def update_store_chart(n, start_date, end_date, categories):
    try:
        df = get_transactions_data()
        df = filter_transactions(df, start_date, end_date, categories)
        if df.empty:
            return go.Figure()
        store = (
            df.groupby(["store_name", "city"])["total"]
            .sum()
            .reset_index(name="total_spent")
            .sort_values("total_spent", ascending=False)
            .head(15)
        )
        store["label"] = store["store_name"] + " (" + store["city"].fillna("") + ")"
        fig = px.bar(
            store,
            x="total_spent",
            y="label",
            orientation="h",
            labels={"total_spent": "Montant (CHF)", "label": "Magasin"},
        )
        fig.update_traces(
            marker_color=COLORS['secondary'],
            marker_line_color=COLORS['secondary'],
            marker_line_width=0
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis={"categoryorder": "total ascending"},
            font=dict(family="Inter, sans-serif", size=12, color="#64748B"),
            xaxis=dict(gridcolor='rgba(226, 232, 240, 0.5)'),
            yaxis_title="",
            height=350
        )
        return fig
    except Exception:
        return go.Figure()

# Callback pour la table des transactions
@app.callback(
    Output("transactions-table", "children"),
    [
        Input("interval-component", "n_intervals"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("category-filter", "value"),
    ],
)
def update_transactions_table(n, start_date, end_date, categories):
    try:
        df = get_transactions_data()
        df = filter_transactions(df, start_date, end_date, categories)
        df = df.head(50)
        if df.empty:
            return html.Div(
                "Aucune transaction pour les filtres sélectionnés.",
                style={'color': '#64748B', 'textAlign': 'center', 'padding': '2rem'}
            )
        df["transaction_date"] = df["transaction_date"].dt.strftime("%d/%m/%Y")
        df["total"] = df["total"].apply(lambda x: f"{x:.2f} CHF")

        table = dash_table.DataTable(
            data=df.to_dict("records"),
            columns=[
                {"name": "Date", "id": "transaction_date"},
                {"name": "Magasin", "id": "store_name"},
                {"name": "Ville", "id": "city"},
                {"name": "Catégorie", "id": "transaction_category"},
                {"name": "Montant", "id": "total"},
                {"name": "Paiement", "id": "payment_method"},
                {"name": "Articles", "id": "item_count"},
            ],
            style_cell={
                'textAlign': 'left',
                'padding': '1rem',
                'fontFamily': 'Inter, sans-serif',
                'fontSize': '0.875rem',
                'border': 'none',
                'borderBottom': '1px solid #E2E8F0'
            },
            style_header={
                'backgroundColor': COLORS['primary'],
                'color': 'white',
                'fontWeight': '600',
                'textTransform': 'uppercase',
                'letterSpacing': '0.05em',
                'fontSize': '0.75rem',
                'border': 'none'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgba(248, 250, 252, 0.5)'
                },
                {
                    'if': {'state': 'active'},
                    'backgroundColor': 'rgba(79, 70, 229, 0.05)',
                    'border': 'none'
                }
            ],
            page_size=10,
            style_table={'borderRadius': '12px', 'overflow': 'hidden'}
        )
        return table
    except Exception as e:
        return html.Div(
            f"Erreur: {str(e)}",
            style={'color': '#EF4444', 'textAlign': 'center', 'padding': '2rem'}
        )

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)