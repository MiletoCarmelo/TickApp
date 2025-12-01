# tickapp/assets/db.py
"""
Asset Dagster pour insérer les données transformées dans la base de données
"""
from dagster import asset, AssetExecutionContext
from typing import List, Dict
import os
from dotenv import load_dotenv

from tickapp.models import ReceiptData
from tickapp.clients.database_client import DatabaseClient

load_dotenv()


@asset(deps=["transformed_receipts", "signal_messages_in_db"])
def receipts_in_db(
    context: AssetExecutionContext,
    transformed_receipts: List[Dict],
    signal_messages_in_db: dict
) -> dict:
    """
    Asset pour insérer les tickets transformés dans la base de données
    
    Args:
        transformed_receipts: Liste des ReceiptData transformés (depuis transformed_receipts)
        signal_messages_in_db: Statistiques d'insertion des messages (pour récupérer les attachment_ids)
    
    Returns:
        Dictionnaire avec les statistiques d'insertion
    """
    context.log.info("💾 Insertion des tickets dans la base de données...")
    
    db_client = DatabaseClient(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5434")),
        database=os.getenv("DB_NAME", "receipt_processing"),
        user=os.getenv("DB_USER", "receipt_user"),
        password=os.getenv("DB_PASSWORD", "SuperSecretPassword123!")
    )
    
    inserted_count = 0
    transaction_ids = []
    attachment_ids_map = signal_messages_in_db.get("attachment_ids_map", {})
    
    for transformed_data in transformed_receipts:
        try:
            receipt_data: ReceiptData = transformed_data["receipt_data"]
            message = transformed_data.get("message")
            message_id = transformed_data.get("message_id")
            
            # Récupérer les attachment_ids si message_id est disponible
            attachment_ids = None
            if message_id:
                attachment_ids = attachment_ids_map.get(message_id, None)
            
            # Helper function pour connexion avec retry
            def get_db_connection(max_retries=3, retry_delay=1.0):
                import psycopg2
                import time
                last_error = None
                conn_params = {
                    "host": os.getenv("DB_HOST", "localhost"),
                    "port": int(os.getenv("DB_PORT", "5434")),
                    "database": os.getenv("DB_NAME", "receipt_processing"),
                    "user": os.getenv("DB_USER", "receipt_user"),
                    "password": os.getenv("DB_PASSWORD", "SuperSecretPassword123!"),
                    "connect_timeout": 10
                }
                for attempt in range(max_retries):
                    try:
                        return psycopg2.connect(**conn_params)
                    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (attempt + 1))
                            continue
                        else:
                            raise
                raise last_error
            
            # Si pas de message_id mais qu'on a un message, essayer de le récupérer depuis la base
            # en cherchant par timestamp et sender
            if not message_id and message:
                try:
                    import psycopg2
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT m.message_id 
                        FROM signal_message m
                        JOIN signal_sender s ON m.sender_id = s.sender_id
                        WHERE m.timestamp = %s 
                        AND s.signal_uuid = %s
                        ORDER BY m.message_id DESC
                        LIMIT 1
                    """, (message.timestamp, str(message.sender.uuid) if message.sender.uuid else None))
                    result = cursor.fetchone()
                    if result:
                        message_id = result[0]
                        attachment_ids = attachment_ids_map.get(message_id, None)
                    cursor.close()
                    conn.close()
                except Exception as e:
                    context.log.warning(f"   ⚠️  Impossible de récupérer message_id depuis la base: {e}")
            
            # Insérer le ticket
            transaction_id = db_client.insert_receipt(
                receipt_data=receipt_data,
                message_id=message_id,
                attachment_ids=attachment_ids
            )
            
            transaction_ids.append(transaction_id)
            inserted_count += 1
            
            context.log.info(
                f"   ✅ Transaction {transaction_id} insérée: "
                f"{receipt_data.store.store_name} - {len(receipt_data.items)} articles"
            )
            
        except Exception as e:
            context.log.error(f"   ❌ Erreur lors de l'insertion: {e}")
            continue
    
    stats = {
        "total_receipts": len(transformed_receipts),
        "inserted_receipts": inserted_count,
        "transaction_ids": transaction_ids
    }
    
    context.log.info(f"✅ {inserted_count}/{len(transformed_receipts)} tickets insérés")
    
    return stats

