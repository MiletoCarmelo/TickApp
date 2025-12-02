"""
Dashboard Dash pour visualiser les données de tickets/reçus
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
    # Par défaut, dans Docker on se connecte au service postgres sur le port interne 5432
    # En local (hors Docker), tu peux surcharger via .env (ex: DB_HOST=localhost, DB_PORT=5434)
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': int(os.getenv('DB_PORT', '5432')),
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
    # Normaliser les dates
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
app.layout = dbc.Container(
    [
        # Header
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            [html.I(className="fas fa-receipt me-2"), "TickApp Dashboard"],
                            className="text-center mb-1 mt-4",
                        ),
                        html.P(
                            "Analyse moderne des dépenses par personne, magasin et catégorie",
                            className="text-center text-muted mb-4",
                        ),
                    ]
                )
            ]
        ),
        # Filtres globaux
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Période", className="fw-bold small text-muted"),
                        dcc.DatePickerRange(
                            id="date-range",
                            display_format="YYYY-MM-DD",
                            minimum_nights=0,
                            start_date=(datetime.now() - timedelta(days=30)).date(),
                            end_date=datetime.now().date(),
                            className="w-100",
                        ),
                    ],
                    md=4,
                    className="mb-2",
                ),
                dbc.Col(
                    [
                        html.Label("Catégories (transaction_category)", className="fw-bold small text-muted"),
                        dcc.Dropdown(
                            id="category-filter",
                            options=[
                                {"label": "Carmelo", "value": "carmelo"},
                                {"label": "Heather", "value": "heather"},
                                {"label": "Neon", "value": "neon"},
                            ],
                            placeholder="Toutes les catégories",
                            multi=True,
                        ),
                    ],
                    md=4,
                    className="mb-2",
                ),
                dbc.Col(
                    [
                        html.Label("Dernière mise à jour", className="fw-bold small text-muted"),
                        html.Div(id="last-update", className="text-muted"),
                    ],
                    md=4,
                    className="mb-2 text-md-end",
                ),
            ],
            className="mb-3",
        ),
        # Métriques principales
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div("Total dépensé", className="text-muted small"),
                                html.H3(id="total-spent", className="text-primary mb-0"),
                            ]
                        ),
                        className="shadow-sm h-100",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div("Transactions", className="text-muted small"),
                                html.H3(id="total-transactions", className="text-success mb-0"),
                            ]
                        ),
                        className="shadow-sm h-100",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div("Moyenne par transaction", className="text-muted small"),
                                html.H3(id="avg-transaction", className="text-info mb-0"),
                            ]
                        ),
                        className="shadow-sm h-100",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div("Magasins différents", className="text-muted small"),
                                html.H3(id="total-stores", className="text-warning mb-0"),
                            ]
                        ),
                        className="shadow-sm h-100",
                    ),
                    md=3,
                ),
            ],
            className="mb-4 g-2",
        ),
        # Graphiques principaux
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Évolution des dépenses"),
                            dbc.CardBody([dcc.Graph(id="spending-timeline", config={"displayModeBar": False})]),
                        ],
                        className="shadow-sm mb-4",
                    ),
                    md=12,
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Dépenses par catégorie"),
                            dbc.CardBody([dcc.Graph(id="spending-by-category", config={"displayModeBar": False})]),
                        ],
                        className="shadow-sm mb-4",
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Top 15 magasins"),
                            dbc.CardBody([dcc.Graph(id="spending-by-store", config={"displayModeBar": False})]),
                        ],
                        className="shadow-sm mb-4",
                    ),
                    md=6,
                ),
            ]
        ),
        # Table des transactions récentes
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Transactions récentes"),
                        dbc.CardBody([html.Div(id="transactions-table")]),
                    ],
                    className="shadow-sm mb-4",
                ),
                md=12,
            )
        ),
        # Intervalle de rafraîchissement automatique
        dcc.Interval(id="interval-component", interval=60 * 1000, n_intervals=0),
    ],
    fluid=True,
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
            return "0.00 CHF", 0, "0.00 CHF", 0, "Aucune donnée"
        total_spent = f"{df['total'].sum():.2f} CHF"
        total_transactions = len(df)
        avg_transaction = f"{df['total'].mean():.2f} CHF"
        total_stores = df["store_name"].nunique()
        last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        fig.update_traces(line_color="#0d6efd", line_width=3)
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
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
            hole=0.45,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
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
            color="total_spent",
            color_continuous_scale="Blues",
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis={"categoryorder": "total ascending"},
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
        df = df.head(50)  # Limiter à 50 transactions récentes
        if df.empty:
            return html.Div("Aucune transaction pour les filtres sélectionnés.", className="text-muted")
        df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")
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
            style_cell={"textAlign": "left", "padding": "10px", "fontFamily": "system-ui"},
            style_header={
                "backgroundColor": "#0d6efd",
                "color": "white",
                "fontWeight": "bold",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f8f9fa"},
            ],
            page_size=10,
        )
        return table
    except Exception as e:
        return html.Div(f"Erreur: {str(e)}", className="text-danger")

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)

