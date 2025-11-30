# tickapp/transformers/normalizers.py
from typing import Optional

class DataNormalizer:
    """Helpers pour normaliser les données"""
    
    @staticmethod
    def normalize_phone(phone: Optional[str]) -> Optional[str]:
        """Normalise un numéro de téléphone"""
        if not phone:
            return None
        # Supprimer espaces, tirets, etc.
        return phone.replace(" ", "").replace("-", "").replace(".", "")
    
    @staticmethod
    def normalize_postal_code(postal_code: Optional[str], country: str) -> Optional[str]:
        """Normalise un code postal selon le pays"""
        if not postal_code:
            return None
        
        # Suisse : 4 chiffres
        if country == "CH":
            return postal_code.zfill(4)
        
        # Autres pays...
        return postal_code