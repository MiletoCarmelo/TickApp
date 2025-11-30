# tickapp/assets/claude.py
"""
Asset Dagster pour appeler Claude API et extraire les données des tickets
"""
from dagster import asset, AssetExecutionContext
from typing import List, Dict, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

from tickapp.clients.signal_client import Message
from tickapp.clients.claude_client import ClaudeClient
from tickapp.clients.prompt_client import PromptClient

load_dotenv()


@asset(deps=["signal_messages"])
def claude_extractions_from_messages(
    context: AssetExecutionContext,
    signal_messages: List[Message]
) -> List[Dict]:
    """
    Asset alternatif pour appeler Claude API directement depuis les messages Signal
    
    Args:
        signal_messages: Liste des messages Signal avec attachments (depuis signal_messages)
    
    Returns:
        Liste des extractions JSON de Claude pour chaque message avec attachment
    """
    context.log.info("🤖 Appel à Claude API pour extraire les données des tickets...")
    
    # Initialiser les clients
    claude_client = ClaudeClient(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt_client = PromptClient(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5434")),
        database=os.getenv("DB_NAME", "receipt_processing"),
        user=os.getenv("DB_USER", "receipt_user"),
        password=os.getenv("DB_PASSWORD", "SuperSecretPassword123!")
    )
    
    # Générer le prompt dynamique
    prompt = prompt_client.generate_prompt()
    context.log.info("   📝 Prompt généré avec les catégories de la base")
    
    extractions = []
    
    # Filtrer les messages avec attachments (images de tickets)
    messages_with_attachments = [
        msg for msg in signal_messages 
        if msg.has_attachments and any(
            att.content_type and att.content_type.startswith("image/") 
            for att in msg.attachments
        )
    ]
    
    context.log.info(f"   📎 {len(messages_with_attachments)} messages avec images de tickets")
    
    for message in messages_with_attachments:
        try:
            # Ajouter le prompt
            claude_client.add_prompt(prompt)
            
            # Ajouter les images (attachments)
            for attachment in message.attachments:
                if attachment.path and attachment.content_type and attachment.content_type.startswith("image/"):
                    claude_client.add_image(str(attachment.path))
            
            # Appeler Claude
            json_response = claude_client.call_json()
            
            # Essayer de récupérer le message_id depuis la base
            message_id = None
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", "5434")),
                    database=os.getenv("DB_NAME", "receipt_processing"),
                    user=os.getenv("DB_USER", "receipt_user"),
                    password=os.getenv("DB_PASSWORD", "SuperSecretPassword123!")
                )
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
                cursor.close()
                conn.close()
            except Exception as e:
                context.log.warning(f"   ⚠️  Impossible de récupérer message_id: {e}")
            
            extractions.append({
                "message_id": message_id,
                "message": message,
                "extraction": json_response
            })
            
            context.log.info(f"   ✅ Extraction réussie pour le message du {message.timestamp}")
            
        except Exception as e:
            context.log.error(f"   ❌ Erreur lors de l'extraction Claude: {e}")
            continue
    
    context.log.info(f"✅ {len(extractions)}/{len(messages_with_attachments)} extractions réussies")
    
    return extractions

