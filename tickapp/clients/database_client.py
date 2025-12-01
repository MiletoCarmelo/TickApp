# tickapp/clients/database_client.py
import psycopg2
import time
from typing import List, Optional
from ..models import ReceiptData
from ..clients.signal_client import Message

class DatabaseClient:
    """Client pour interagir avec PostgreSQL"""
    
    def __init__(self, host: str = "localhost", port: int = 5433, 
                 database: str = "receipt_processing", 
                 user: str = "receipt_user", 
                 password: str = "SuperSecretPassword123!"):
        self.conn_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
            "connect_timeout": 10  # Timeout de connexion de 10 secondes
        }
    
    def _get_connection(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Obtient une connexion à la base de données avec retry
        
        Args:
            max_retries: Nombre maximum de tentatives
            retry_delay: Délai entre les tentatives (secondes)
        
        Returns:
            Connection object
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(**self.conn_params)
                return conn
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Backoff exponentiel
                    continue
                else:
                    raise
        raise last_error
    
    def insert_signal_message(self, message: Message) -> tuple[int, List[int]]:
        """
        Insère un message Signal complet dans la base de données
        
        Args:
            message: Object Message de SignalClient (Message class)
        
        Returns:
            (message_id, [attachment_ids])
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Insérer le sender (ou récupérer s'il existe déjà)
            sender_id = None
            if message.sender.uuid:
                cursor.execute("""
                    INSERT INTO signal_sender (signal_uuid, phone_number, contact_name, last_seen)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (signal_uuid) 
                    DO UPDATE SET 
                        phone_number = COALESCE(EXCLUDED.phone_number, signal_sender.phone_number),
                        contact_name = COALESCE(EXCLUDED.contact_name, signal_sender.contact_name),
                        last_seen = CURRENT_TIMESTAMP
                    RETURNING sender_id
                """, (
                    message.sender.uuid,  # Pass as string directly (psycopg2 handles UUID conversion)
                    message.sender.number if message.sender.number else None,  # NULL si pas de numéro
                    message.sender.name
                ))
                sender_id = cursor.fetchone()[0]
            
            # 2. Insérer le group
            group_id = None
            if message.is_group_message and message.group:
                cursor.execute("""
                    INSERT INTO signal_group (signal_group_id, group_name)
                    VALUES (%s, %s)
                    ON CONFLICT (signal_group_id) 
                    DO UPDATE SET group_name = EXCLUDED.group_name
                    RETURNING group_id
                """, (
                    message.group.id,
                    message.group.name
                ))
                group_id = cursor.fetchone()[0]
            
            # 3. Insérer le message (avec sender_id et group_id directement)
            cursor.execute("""
                INSERT INTO signal_message (
                    sender_id, group_id, timestamp, text_content, 
                    is_group_message, signal_account
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING message_id
            """, (
                sender_id,
                group_id,
                message.timestamp,
                message.text,
                message.is_group_message,
                message.account or ""
            ))
            message_id = cursor.fetchone()[0]
            
            # 4. Insérer les attachments (sans message_id)
            attachment_ids = []
            for att in message.attachments:
                cursor.execute("""
                    INSERT INTO attachment (
                        signal_attachment_id, content_type, 
                        filename, file_size, upload_timestamp_ms, file_path
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING attachment_id
                """, (
                    att.id,
                    att.content_type,
                    att.filename,
                    att.size,
                    att.upload_timestamp_ms,
                    str(att.path) if att.path else None
                ))
                attachment_id = cursor.fetchone()[0]
                attachment_ids.append(attachment_id)
                
                # 4b. Créer le mapping message -> attachment
                cursor.execute("""
                    INSERT INTO message_attachment_mapping (message_id, attachment_id)
                    VALUES (%s, %s)
                """, (message_id, attachment_id))
            
            conn.commit()
            print(f"✅ Message Signal inséré : message_id={message_id}, {len(attachment_ids)} attachments")
            return message_id, attachment_ids
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur : {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def insert_receipt(self, receipt_data: ReceiptData, message_id: int = None, 
                      attachment_ids: List[int] = None) -> int:
        """
        Insère un ticket complet dans la base de données
        
        Returns:
            transaction_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Insérer le magasin (ou récupérer s'il existe déjà)
            cursor.execute("""
                INSERT INTO store (store_name, address, postal_code, city, country_code, phone)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (store_name, city, postal_code)
                DO UPDATE SET 
                    address = COALESCE(EXCLUDED.address, store.address),
                    phone = COALESCE(EXCLUDED.phone, store.phone),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING store_id
            """, (
                receipt_data.store.store_name,
                receipt_data.store.address,
                receipt_data.store.postal_code,
                receipt_data.store.city,
                receipt_data.store.country_code,
                receipt_data.store.phone
            ))
            store_id = cursor.fetchone()[0]
            
            # 1b. Récupérer ou créer la catégorie de transaction (si nom fourni)
            transaction_category_id = receipt_data.transaction.transaction_category_id
            if receipt_data.transaction.transaction_category_name:
                category_name_lower = receipt_data.transaction.transaction_category_name.lower().strip()
                cursor.execute("""
                    INSERT INTO transaction_category (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO NOTHING
                    RETURNING category_id
                """, (category_name_lower,))
                result = cursor.fetchone()
                if result:
                    transaction_category_id = result[0]
                else:
                    # Récupérer l'ID si la catégorie existait déjà
                    cursor.execute("""
                        SELECT category_id FROM transaction_category WHERE name = %s
                    """, (category_name_lower,))
                    transaction_category_id = cursor.fetchone()[0]
            
            # 2. Insérer la transaction (avec message_id et transaction_category_id)
            cursor.execute("""
                INSERT INTO transaction (
                    message_id, store_id, transaction_category_id, receipt_number, 
                    transaction_date, transaction_time, currency, total, 
                    payment_method, source, processed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING transaction_id
            """, (
                message_id,
                store_id,
                transaction_category_id,
                receipt_data.transaction.receipt_number,
                receipt_data.transaction.transaction_date,
                receipt_data.transaction.transaction_time,
                receipt_data.transaction.currency,
                receipt_data.transaction.total,
                receipt_data.transaction.payment_method,
                receipt_data.transaction.source
            ))
            transaction_id = cursor.fetchone()[0]
            
            # 3. Insérer les items
            for item in receipt_data.items:
                # 3a. Récupérer ou créer la catégorie (retourne toujours l'ID)
                cursor.execute("""
                    WITH new_category AS (
                        INSERT INTO item_category (category_main, category_sub)
                        VALUES (%s, %s)
                        ON CONFLICT (category_main, category_sub) DO NOTHING
                        RETURNING category_id
                    )
                    SELECT category_id FROM new_category
                    UNION ALL
                    SELECT category_id FROM item_category 
                    WHERE category_main = %s AND category_sub = %s
                    LIMIT 1
                """, (item.category_main, item.category_sub, item.category_main, item.category_sub))
                category_id = cursor.fetchone()[0]
                
                # 3b. Insérer l'item (sans transaction_id)
                cursor.execute("""
                    INSERT INTO item (
                        product_name, product_reference, brand,
                        quantity, unit_price, total_price, vat_rate,
                        category_id, line_number
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING item_id
                """, (
                    item.product_name,
                    item.product_reference,
                    item.brand,
                    item.quantity,
                    item.unit_price,
                    item.total_price,
                    item.vat_rate,
                    category_id,
                    item.line_number
                ))
                item_id = cursor.fetchone()[0]
                
                # 3c. Créer le mapping transaction -> item
                cursor.execute("""
                    INSERT INTO transaction_item_mapping (transaction_id, item_id)
                    VALUES (%s, %s)
                """, (transaction_id, item_id))
            
            # 4. Lier les attachments
            # Si attachment_ids n'est pas fourni mais message_id l'est, récupérer les attachments du message
            if not attachment_ids and message_id:
                cursor.execute("""
                    SELECT attachment_id 
                    FROM message_attachment_mapping 
                    WHERE message_id = %s
                """, (message_id,))
                attachment_ids = [row[0] for row in cursor.fetchall()]
            
            # Insérer les liens transaction_attachment_mapping
            if attachment_ids:
                for attachment_id in attachment_ids:
                    cursor.execute("""
                        INSERT INTO transaction_attachment_mapping (transaction_id, attachment_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (transaction_id, attachment_id))
                print(f"   📎 {len(attachment_ids)} attachment(s) lié(s) à la transaction")
            
            conn.commit()
            print(f"✅ Ticket inséré : transaction_id={transaction_id}, {len(receipt_data.items)} articles")
            return transaction_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur lors de l'insertion du ticket : {e}")
            raise
        finally:
            cursor.close()
            conn.close()