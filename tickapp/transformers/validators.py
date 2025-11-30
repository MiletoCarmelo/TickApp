# tickapp/transformers/validators.py
from decimal import Decimal
from typing import Optional

class DataValidator:
    """Helpers pour valider les données avant insertion"""
    
    @staticmethod
    def validate_currency(currency: str) -> str:
        """Valide et normalise la devise"""
        valid_currencies = ["CHF", "EUR", "USD", "GBP"]
        currency = currency.upper()
        if currency not in valid_currencies:
            raise ValueError(f"Devise invalide: {currency}")
        return currency
    
    @staticmethod
    def validate_price(price: Decimal) -> Decimal:
        """Valide qu'un prix est positif"""
        if price < 0:
            raise ValueError(f"Prix négatif: {price}")
        return price
    
    @staticmethod
    def validate_category(category_main: str, category_sub: str) -> tuple[str, str]:
        """Vérifie que la catégorie existe dans le référentiel"""
        # Ici tu pourrais vérifier contre la table categories
        return category_main, category_sub