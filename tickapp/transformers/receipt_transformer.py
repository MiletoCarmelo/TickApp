# tickapp/transformers/receipt_transformer.py
from datetime import datetime
from decimal import Decimal
from ..models import Store, Transaction, Item, ReceiptData

class ReceiptTransformer:
    """Transforme le JSON Claude en objets de données"""
    
    @staticmethod
    def transform_claude_json(claude_json: dict, message_id: int = None) -> ReceiptData:
        """
        Transforme le JSON de Claude en objets Python
        
        Args:
            claude_json: Le JSON retourné par Claude
            message_id: ID du message Signal (optionnel)
            
        Returns:
            ReceiptData avec store, transaction, items
        """
        
        # 1. Transformer le magasin
        store = Store(
            store_name=claude_json["magasin"]["nom"],
            address=claude_json["magasin"].get("adresse"),
            postal_code=claude_json["magasin"].get("code_postal"),
            city=claude_json["magasin"].get("ville"),
            country_code=claude_json["magasin"].get("pays"),
            phone=claude_json["magasin"].get("telephone")
        )
        
        # 2. Parser l'heure (gestion de plusieurs formats possibles)
        transaction_time = None
        if claude_json["transaction"].get("heure"):
            heure_str = claude_json["transaction"]["heure"]
            # Essayer avec secondes d'abord (HH:MM:SS)
            try:
                transaction_time = datetime.strptime(heure_str, "%H:%M:%S").time()
            except ValueError:
                # Si ça échoue, essayer sans secondes (HH:MM)
                try:
                    transaction_time = datetime.strptime(heure_str, "%H:%M").time()
                except ValueError:
                    # Si ça échoue encore, laisser None
                    print(f"⚠️  Format d'heure non reconnu: {heure_str}")
                    transaction_time = None
        
        # 3. Transformer la transaction
        transaction = Transaction(
            store_id=0,  # Sera rempli après insertion du store
            message_id=message_id,
            transaction_category_id=claude_json["transaction"].get("category_id"),
            receipt_number=claude_json["transaction"].get("numero_ticket"),
            transaction_date=datetime.strptime(
                claude_json["transaction"]["date"], 
                "%Y-%m-%d"
            ).date(),
            transaction_time=transaction_time,
            currency=claude_json["devise"],
            total=Decimal(str(claude_json["total"])),
            payment_method=claude_json["transaction"].get("mode_paiement"),
            source="signal"
        )
        
        # 4. Transformer les items
        items = []
        for idx, article in enumerate(claude_json["articles"], start=1):
            item = Item(
                transaction_id=0,  # Sera rempli après insertion de la transaction
                product_name=article["nom"],
                product_reference=article.get("reference"),
                brand=article.get("marque"),
                quantity=Decimal(str(article["quantite"])),
                unit_price=Decimal(str(article["prix_unitaire"])),
                total_price=Decimal(str(article["prix_total"])),
                vat_rate=article.get("tva"),
                category_main=article["categorie"],
                category_sub=article["sous_categorie"],
                line_number=idx
            )
            items.append(item)
        
        return ReceiptData(
            store=store,
            transaction=transaction,
            items=items
        )