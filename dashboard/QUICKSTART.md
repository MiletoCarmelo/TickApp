# 🚀 Guide de démarrage rapide

## Problème : L'app ne démarre pas

Si vous voyez `ModuleNotFoundError: No module named 'streamlit'`, c'est que vous n'utilisez pas l'environnement Poetry.

## ✅ Solution rapide

### Option 1 : Utiliser le script dev.sh (Recommandé)

```bash
cd dashboard
./dev.sh
```

Le script fait tout automatiquement :
- ✅ Vérifie que la DB Docker est démarrée
- ✅ Utilise Poetry pour lancer Streamlit
- ✅ Active le hot-reload

### Option 2 : Lancer manuellement avec Poetry

```bash
# Depuis la racine du projet
cd dashboard
poetry run streamlit run app.py
```

### Option 3 : Activer l'environnement Poetry d'abord

```bash
# Activer l'environnement virtuel
poetry shell

# Puis lancer Streamlit
cd dashboard
streamlit run app.py
```

## 🔍 Vérifications

### 1. Vérifier que Poetry est installé
```bash
poetry --version
```

### 2. Vérifier que les dépendances sont installées
```bash
poetry install
```

### 3. Vérifier que Streamlit est installé
```bash
poetry run python -c "import streamlit; print(streamlit.__version__)"
```

### 4. Vérifier que la DB Docker tourne
```bash
docker ps | grep receipt-postgres
```

Si elle n'est pas démarrée :
```bash
docker-compose up -d postgres
```

## 🐛 Erreurs courantes

### "ModuleNotFoundError: No module named 'streamlit'"
**Solution** : Utilisez `poetry run streamlit` au lieu de `streamlit` directement

### "No module named 'dashboard.components'"
**Solution** : Lancez depuis le dossier `dashboard/` ou utilisez le script `dev.sh`

### "Connection refused" (base de données)
**Solution** : Démarrez la DB avec `docker-compose up -d postgres`

## 💡 Astuce

Pour éviter ces problèmes, **toujours utiliser le script `dev.sh`** :
```bash
cd dashboard
./dev.sh
```

Il gère tout automatiquement ! 🎉

