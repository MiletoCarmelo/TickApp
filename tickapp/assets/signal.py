# tickapp/assets/signal.py
"""
Asset Dagster pour recevoir et traiter les messages Signal
"""
from dagster import asset, AssetExecutionContext
from typing import List
import os
from dotenv import load_dotenv

from tickapp.clients.signal_client import SignalClient, Message
from tickapp.clients.database_client import DatabaseClient

load_dotenv()


@asset
def signal_messages(context: AssetExecutionContext) -> List[Message]:
    """
    Asset pour recevoir les messages Signal et télécharger les attachments
    
    Returns:
        Liste des messages Signal avec attachments téléchargés
    """
    context.log.info("📱 Réception des messages Signal...")
    
    # Initialiser le client Signal
    phone_number = os.getenv("SIGNAL_PHONE_NUMBER")
    if not phone_number:
        raise ValueError("SIGNAL_PHONE_NUMBER non défini dans les variables d'environnement")
    
    client = SignalClient(phone_number=phone_number)
    
    # Recevoir les messages
    raw_messages = client.receive(number_of_messages=100)
    context.log.info(f"   📨 {len(raw_messages)} messages bruts reçus")
    
    # Parser les messages
    messages = client._parse_message(raw_messages)
    context.log.info(f"   ✅ {len(messages)} messages parsés")
    
    # Télécharger les attachments
    messages_with_attachments = client.download_attachment(
        phone_number=client.phone_number,
        messages=messages
    )
    
    # Compter les messages avec attachments
    messages_with_att = [msg for msg in messages_with_attachments if msg.has_attachments]
    context.log.info(f"   📎 {len(messages_with_att)} messages avec attachments")
    
    return messages_with_attachments


@asset(deps=[signal_messages])
def signal_messages_in_db(context: AssetExecutionContext, signal_messages: List[Message]) -> dict:
    """
    Asset pour insérer les messages Signal dans la base de données
    
    Args:
        signal_messages: Liste des messages Signal (depuis l'asset signal_messages)
    
    Returns:
        Dictionnaire avec les statistiques d'insertion
    """
    context.log.info("💾 Insertion des messages Signal en base de données...")
    
    db_client = DatabaseClient(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5434")),
        database=os.getenv("DB_NAME", "receipt_processing"),
        user=os.getenv("DB_USER", "receipt_user"),
        password=os.getenv("DB_PASSWORD", "SuperSecretPassword123!")
    )
    
    inserted_count = 0
    message_ids = []
    attachment_ids_map = {}
    
    for message in signal_messages:
        try:
            message_id, attachment_ids = db_client.insert_signal_message(message)
            message_ids.append(message_id)
            attachment_ids_map[message_id] = attachment_ids
            inserted_count += 1
            context.log.info(f"   ✅ Message {message_id} inséré avec {len(attachment_ids)} attachments")
        except Exception as e:
            context.log.error(f"   ❌ Erreur lors de l'insertion du message: {e}")
    
    stats = {
        "total_messages": len(signal_messages),
        "inserted_messages": inserted_count,
        "message_ids": message_ids,
        "attachment_ids_map": attachment_ids_map
    }
    
    context.log.info(f"✅ {inserted_count}/{len(signal_messages)} messages insérés")
    
    return stats

