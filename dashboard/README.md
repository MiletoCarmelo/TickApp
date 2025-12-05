# 🎨 TickApp Dashboard - Structure Modulaire

## 📁 Structure du projet

Le dashboard est maintenant organisé en modules pour une meilleure maintenabilité :

```
dashboard/
├── app.py                 # Point d'entrée principal
├── config.py              # Configuration (DB, couleurs)
├── data.py                # Fonctions de récupération des données
├── components/            # Composants réutilisables
│   ├── __init__.py
│   ├── styles.py          # Styles CSS
│   └── sidebar.py         # Composant sidebar
├── pages/                 # Pages individuelles
│   ├── __init__.py
│   ├── dashboard.py       # Page Dashboard principale
│   ├── analytics.py       # Page Analytics
│   ├── stores.py          # Page Stores
│   ├── categories.py      # Page Categories
│   ├── history.py         # Page History
│   ├── transactions.py    # Page Transactions
│   └── settings.py        # Page Settings
├── assets/                # Assets statiques
│   └── Styles.css
├── dev.sh                 # Script de développement local
├── Dockerfile
└── README.md
```

## 🚀 Utilisation

### Option 1 : Développement local (Recommandé pour le dev)

**Avantages** : Hot-reload automatique, pas besoin de rebuild Docker

1. **Démarrer uniquement la base de données** :
```bash
docker-compose up -d postgres
```

2. **Lancer Streamlit localement** :
```bash
cd dashboard
chmod +x dev.sh
./dev.sh
```

Ou directement :
```bash
streamlit run app.py
```

Le dashboard sera accessible sur `http://localhost:8501` avec **hot-reload automatique** ! 🎉

### Option 2 : Avec Docker (Production)

```bash
docker-compose up dashboard
```

Le volume mount (`./dashboard:/app`) permet déjà le hot-reload, mais un rebuild peut être nécessaire pour certaines dépendances.

## 🔥 Hot-Reload

Streamlit détecte automatiquement les changements dans :
- ✅ Fichiers Python (`.py`)
- ✅ Fichiers de configuration
- ✅ Fichiers Markdown

**Les changements sont appliqués automatiquement** - pas besoin de redémarrer !

### Forcer un refresh

Si le hot-reload ne fonctionne pas :
1. Cliquer sur "Always rerun" dans le menu (⋮) de Streamlit
2. Ou appuyer sur `R` dans le navigateur
3. Ou utiliser le bouton refresh (↻) dans l'interface

## 📝 Ajouter une nouvelle page

1. Créer un nouveau fichier dans `pages/` :
```python
# pages/ma_nouvelle_page.py
import streamlit as st

def render():
    """Affiche la nouvelle page"""
    st.markdown("# Ma Nouvelle Page")
    st.caption("Description de la page")
    # Votre contenu ici
```

2. Importer dans `app.py` :
```python
from pages import ma_nouvelle_page
```

3. Ajouter le routage :
```python
elif "Ma Nouvelle Page" in page:
    ma_nouvelle_page.render()
```

4. Ajouter l'option dans `components/sidebar.py` :
```python
page = st.radio(
    "",
    [
        # ... autres pages
        "🆕 Ma Nouvelle Page"
    ]
)
```

## 🎨 Personnalisation

### Modifier les couleurs

Éditer `config.py` :
```python
COLORS = {
    'primary': '#6366F1',  # Votre couleur principale
    'success': '#10B981',
    # ...
}
```

### Modifier les styles

Éditer `components/styles.py` et la fonction `load_styles()`.

### Modifier la configuration DB

Éditer `config.py` ou utiliser les variables d'environnement dans `.env`.

## 🔧 Dépendances

### Installation locale

```bash
# Avec Poetry (recommandé)
poetry install

# Ou avec pip
pip install streamlit plotly pandas psycopg2-binary python-dotenv
```

### Variables d'environnement

Créer un fichier `.env` à la racine du projet :
```env
DB_HOST=localhost
DB_PORT=5434
DB_NAME=receipt_processing
DB_USER=receipt_user
DB_PASSWORD=SuperSecretPassword123!
```

## 📊 Fonctionnalités

### ✅ Implémentées
- Dashboard principal avec métriques
- Filtres par date, catégorie et magasin
- Sidebar avec navigation
- Styles premium
- Cache des données
- Hot-reload pour le développement

### 🚧 À venir
- Page Analytics complète
- Page Stores avec détails
- Page Categories avec graphiques
- Page History avec table complète
- Page Transactions avec détails
- Page Settings pour configuration

## 🐛 Dépannage

### Le dashboard ne se charge pas
1. Vérifier que la base de données est accessible
2. Vérifier les variables d'environnement dans `.env`
3. Vérifier les logs : `docker-compose logs dashboard`

### Les données ne s'affichent pas
1. Vérifier la connexion à la base de données
2. Vérifier que les tables existent
3. Utiliser le bouton refresh (↻) pour rafraîchir le cache

### Le hot-reload ne fonctionne pas
1. Vérifier que `runOnSave = true` dans la config
2. Vérifier que le fichier est sauvegardé
3. Forcer un refresh avec `R` dans le navigateur
4. Redémarrer Streamlit si nécessaire

## 💡 Astuces de développement

### Mode debug
Ajouter `--logger.level=debug` pour plus de logs :
```bash
streamlit run app.py --logger.level=debug
```

### Voir les erreurs Python
Les erreurs s'affichent directement dans le terminal où Streamlit tourne.

### Clear le cache
```python
# Dans le code
st.cache_data.clear()

# Ou via l'interface
Menu (⋮) > Clear cache
```

## 📚 Documentation

Pour plus de détails sur chaque module, consulter les docstrings dans les fichiers Python.
