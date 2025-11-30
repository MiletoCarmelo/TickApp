# tickapp/assets/transform.py
"""
Asset Dagster pour transformer les extractions Claude en objets Python
"""
from dagster import asset, AssetExecutionContext
from typing import List, Dict
import os
from dotenv import load_dotenv

from tickapp.transformers.receipt_transformer import ReceiptTransformer

load_dotenv()


@asset(deps=["claude_extractions_from_messages"])
def transformed_receipts(
    context: AssetExecutionContext,
    claude_extractions_from_messages: List[Dict]
) -> List[Dict]:
    """
    Asset pour transformer les extractions JSON de Claude en objets ReceiptData
    
    Args:
        claude_extractions_from_messages: Liste des extractions Claude (depuis claude_extractions_from_messages)
    
    Returns:
        Liste des objets ReceiptData transformés
    """
    context.log.info("🔄 Transformation des extractions Claude en objets Python...")
    
    transformed = []
    
    for extraction_data in claude_extractions_from_messages:
        try:
            claude_json = extraction_data["extraction"]
            message = extraction_data.get("message")
            
            # Récupérer le message_id si disponible (depuis la base)
            message_id = extraction_data.get("message_id")
            if message_id is None and message:
                # On pourrait récupérer le message_id depuis la base si nécessaire
                message_id = None
            
            # Transformer le JSON Claude en ReceiptData
            receipt_data = ReceiptTransformer.transform_claude_json(
                claude_json=claude_json,
                message_id=message_id
            )
            
            transformed.append({
                "receipt_data": receipt_data,
                "message": message,
                "message_id": message_id,
                "claude_json": claude_json
            })
            
            context.log.info(
                f"   ✅ Transformé: {receipt_data.store.store_name} - "
                f"{len(receipt_data.items)} articles"
            )
            
        except Exception as e:
            context.log.error(f"   ❌ Erreur lors de la transformation: {e}")
            continue
    
    context.log.info(f"✅ {len(transformed)}/{len(claude_extractions_from_messages)} transformations réussies")
    
    return transformed

