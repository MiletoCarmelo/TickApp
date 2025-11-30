# tickapp/clients/prompt_client.py
"""
Client pour générer des prompts dynamiques à partir de la base de données
"""
import psycopg2
from pathlib import Path
from typing import Dict, Optional


class PromptClient:
    """
    Client pour générer des prompts dynamiques en remplaçant des placeholders
    par des données de la base de données
    """
    
    def __init__(self, host: str = "localhost", port: int = 5433, 
                 database: str = "receipt_processing", 
                 user: str = "receipt_user", 
                 password: str = "SuperSecretPassword123!"):
        """
        Initialise le client de prompt
        
        Args:
            host: Host PostgreSQL
            port: Port PostgreSQL
            database: Nom de la base de données
            user: Utilisateur PostgreSQL
            password: Mot de passe PostgreSQL
        """
        self.conn_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
    
    def _get_item_categories(self) -> str:
        """
        Récupère toutes les catégories d'items formatées pour le prompt
        
        Returns:
            String formatée avec toutes les catégories d'items
        """
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        
        try:
            # Récupérer toutes les catégories actives, groupées par category_main
            cursor.execute("""
                SELECT category_main, category_sub, description
                FROM item_category
                WHERE active = TRUE
                ORDER BY category_main, category_sub
            """)
            
            categories = cursor.fetchall()
            
            if not categories:
                return "Aucune catégorie disponible."
            
            # Grouper par category_main
            grouped = {}
            for main, sub, desc in categories:
                if main not in grouped:
                    grouped[main] = []
                grouped[main].append((sub, desc))
            
            # Formater pour le prompt
            lines = []
            current_group = None
            for main in sorted(grouped.keys()):
                # Ajouter un saut de ligne entre les groupes principaux
                if current_group is not None:
                    lines.append("")
                lines.append(f"   {main}:")
                for sub, desc in grouped[main]:
                    lines.append(f"      - {sub}")
                current_group = main
            
            return "\n".join(lines)
            
        finally:
            cursor.close()
            conn.close()
    
    def _get_transaction_categories(self) -> str:
        """
        Récupère toutes les catégories de transaction formatées pour le prompt
        
        Returns:
            String formatée avec toutes les catégories de transaction (ID et nom)
        """
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT category_id, name
                FROM transaction_category
                ORDER BY category_id
            """)
            
            categories = cursor.fetchall()
            
            if not categories:
                return "Aucune catégorie de transaction disponible."
            
            # Formater pour le prompt
            lines = []
            for cat_id, name in categories:
                lines.append(f"   - ID {cat_id}: {name}")
            
            return "\n".join(lines)
            
        finally:
            cursor.close()
            conn.close()
    
    def generate_prompt(self, prompt_template_path: Optional[Path] = None) -> str:
        """
        Génère un prompt en remplaçant les placeholders par les données de la base
        
        Args:
            prompt_template_path: Chemin vers le fichier template (défaut: tickets.txt)
        
        Returns:
            Le prompt avec les placeholders remplacés
        """
        if prompt_template_path is None:
            # Chemin par défaut
            prompt_template_path = Path(__file__).parent.parent / "prompts" / "tickets.txt"
        
        # Lire le template
        with open(prompt_template_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        # Remplacer les placeholders
        item_categories = self._get_item_categories()
        transaction_categories = self._get_transaction_categories()
        
        prompt = template.replace("[item_categories]", item_categories)
        prompt = prompt.replace("[transaction_categories]", transaction_categories)
        
        return prompt
    
    def get_item_categories_list(self) -> list:
        """
        Récupère la liste des catégories d'items pour validation/matching
        
        Returns:
            Liste de tuples (category_main, category_sub)
        """
        conn = psycopg2.connect(**self.conn_params)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT category_main, category_sub
                FROM item_category
                WHERE active = TRUE
                ORDER BY category_main, category_sub
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
    
    def find_closest_category(self, category_name: str, subcategory_name: Optional[str] = None) -> Optional[tuple]:
        """
        Trouve la catégorie la plus proche/similaire
        
        Args:
            category_name: Nom de la catégorie recherchée
            subcategory_name: Nom de la sous-catégorie recherchée (optionnel)
        
        Returns:
            Tuple (category_main, category_sub) ou None si aucune correspondance
        """
        import difflib
        
        categories = self.get_item_categories_list()
        
        if not categories:
            return None
        
        # Normaliser les noms
        category_name_lower = category_name.lower().strip()
        subcategory_name_lower = subcategory_name.lower().strip() if subcategory_name else None
        
        # Chercher une correspondance exacte d'abord
        for main, sub in categories:
            if main.lower() == category_name_lower:
                if subcategory_name_lower and sub.lower() == subcategory_name_lower:
                    return (main, sub)
                elif not subcategory_name_lower:
                    # Si pas de sous-catégorie spécifiée, retourner la première correspondance
                    return (main, sub)
        
        # Si pas de correspondance exacte, chercher la plus similaire
        best_match = None
        best_score = 0.0
        
        for main, sub in categories:
            # Score pour category_main
            main_score = difflib.SequenceMatcher(None, category_name_lower, main.lower()).ratio()
            
            # Score pour category_sub si fourni
            if subcategory_name_lower:
                sub_score = difflib.SequenceMatcher(None, subcategory_name_lower, sub.lower()).ratio()
                total_score = (main_score * 0.6) + (sub_score * 0.4)  # Poids pour main et sub
            else:
                total_score = main_score
            
            if total_score > best_score:
                best_score = total_score
                best_match = (main, sub)
        
        # Retourner seulement si le score est raisonnable (> 0.5)
        if best_score > 0.5:
            return best_match
        
        return None

