# tickapp/assets/message_pipeline.py
"""
Assets Dagster pour traiter un seul message Signal (pipeline par message)
Utilise la nouvelle API @asset au lieu de @op
"""
from dagster import asset, AssetExecutionContext, Config, define_asset_job
from typing import Optional, Dict
from datetime import datetime
import os
from dotenv import load_dotenv
from pydantic import Field

from tickapp.clients.signal_client import SignalClient, Message, Attachment, Contact, Group
from pathlib import Path
import json
from tickapp.clients.database_client import DatabaseClient
from tickapp.clients.claude_client import ClaudeClient
from tickapp.clients.prompt_client import PromptClient
from tickapp.transformers.receipt_transformer import ReceiptTransformer
from tickapp.models import ReceiptData

load_dotenv()


# ============================================================================
# ASSETS
# ============================================================================

class MessageConfig(Config):
    """Configuration pour un message Signal"""
    message_timestamp: str = Field(description="Timestamp ISO du message")
    sender_uuid: Optional[str] = Field(default=None, description="UUID du sender")
    sender_number: Optional[str] = Field(default=None, description="Numéro de téléphone du sender")


@asset
def message_from_signal(context: AssetExecutionContext) -> Message:
    """
    Asset pour récupérer un message Signal spécifique depuis Signal
    
    Utilise les tags du run pour identifier le message à traiter
    """
    # Récupérer la config depuis les run tags (passés par le sensor)
    tags = {}
    if hasattr(context, 'run') and context.run:
        tags = context.run.tags
    elif hasattr(context, 'dagster_run') and context.dagster_run:
        tags = context.dagster_run.tags
    
    # Essayer aussi depuis op_execution_context si disponible
    if not tags and hasattr(context, 'op_execution_context') and context.op_execution_context:
        op_config = context.op_execution_context.op_config or {}
        if op_config:
            tags = {
                "message_timestamp": op_config.get("message_timestamp", ""),
                "sender_uuid": op_config.get("sender_uuid"),
                "sender_number": op_config.get("sender_number")
            }
    
    # Extraire les valeurs depuis les tags
    config = {
        "message_timestamp": tags.get("message_timestamp", ""),
        "sender_uuid": tags.get("sender_uuid"),
        "sender_number": tags.get("sender_number")
    }
    
    message_timestamp = config.get("message_timestamp", "")
    sender_uuid = config.get("sender_uuid")
    sender_number = config.get("sender_number")
    
    # Valider que message_timestamp n'est pas vide
    if not message_timestamp:
        raise ValueError(
            "message_timestamp manquant dans les tags du run. "
            "Assurez-vous que le sensor passe 'message_timestamp' dans les tags."
        )
    
    # Reconstruire le message depuis les tags (méthode simplifiée)
    context.log.info(f"📱 Reconstruction du message Signal depuis les tags (timestamp: {message_timestamp})...")
    
    # Parser le timestamp
    try:
        if 'Z' in message_timestamp or '+' in message_timestamp:
            target_timestamp = datetime.fromisoformat(message_timestamp.replace('Z', '+00:00'))
        else:
            target_timestamp = datetime.fromisoformat(message_timestamp)
    except ValueError as e:
        try:
            target_timestamp = datetime.fromisoformat(message_timestamp.replace('Z', ''))
        except ValueError:
            raise ValueError(
                f"Impossible de parser le timestamp '{message_timestamp}': {e}. "
                f"Format attendu: ISO 8601"
            )
    
    # Normaliser pour comparaison (enlever timezone si présent)
    if target_timestamp.tzinfo:
        target_timestamp = target_timestamp.replace(tzinfo=None)
    
    # Reconstruire les attachments depuis les tags
    attachment_paths_json = tags.get("attachment_paths", "[]")
    try:
        attachment_paths = json.loads(attachment_paths_json)
    except json.JSONDecodeError:
        attachment_paths = []
    
    attachments = []
    for att_data in attachment_paths:
        if Path(att_data.get("path", "")).exists():
            attachments.append(Attachment(
                id=att_data.get("id", ""),
                content_type=att_data.get("content_type", ""),
                filename=att_data.get("filename", ""),
                size=0,
                upload_timestamp_ms=0,
                path=Path(att_data.get("path", ""))
            ))
    
    if not attachments:
        raise ValueError("Aucun attachment trouvé dans les tags. Le message doit avoir des images.")
    
    # Reconstruire le contact
    sender_name = tags.get("sender_name", "")
    contact = Contact(
        number=sender_number or "",
        name=sender_name if sender_name else None,
        uuid=sender_uuid if sender_uuid else None
    )
    
    # Reconstruire le groupe si disponible
    group = None
    group_id = tags.get("group_id", "")
    group_name = tags.get("group_name", "")
    if group_id:
        group = Group(id=group_id, name=group_name)
    
    # Reconstruire le message
    message_text = tags.get("message_text", "")
    is_group_message = tags.get("is_group_message", "False").lower() == "true"
    
    message = Message(
        sender=contact,
        timestamp=target_timestamp,
        text=message_text if message_text else None,
        attachments=attachments,
        group=group,
        is_group_message=is_group_message,
        account=None
    )
    
    context.log.info(f"✅ Message reconstruit depuis tags avec {len(attachments)} attachment(s)")
    
    # Vérifier qu'il y a des images
    has_images = any(
        att.content_type and att.content_type.startswith("image/") 
        for att in message.attachments
    )
    
    if not has_images:
        raise ValueError("Le message n'a pas d'images de ticket")
    
    context.log.info(f"✅ Message trouvé avec {len(message.attachments)} attachment(s)")
    return message


@asset(
    deps=[message_from_signal]
)
def message_in_db(context: AssetExecutionContext, message_from_signal: Message) -> Dict:
    """
    Asset pour insérer un message Signal dans la base de données
    
    Args:
        message_from_signal: Message Signal récupéré (depuis l'asset message_from_signal)
    
    Returns:
        Dictionnaire avec message_id et attachment_ids
    """
    context.log.info("💾 Insertion du message Signal en base de données...")
    
    db_client = DatabaseClient(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5434")),
        database=os.getenv("DB_NAME", "receipt_processing"),
        user=os.getenv("DB_USER", "receipt_user"),
        password=os.getenv("DB_PASSWORD", "SuperSecretPassword123!")
    )
    
    try:
        message_id, attachment_ids = db_client.insert_signal_message(message_from_signal)
        context.log.info(f"✅ Message {message_id} inséré avec {len(attachment_ids)} attachments")
        return {
            "message_id": message_id,
            "attachment_ids": attachment_ids
        }
    except Exception as e:
        context.log.error(f"❌ Erreur lors de l'insertion: {e}")
        raise


@asset(
    deps=[message_from_signal]
)
def claude_extraction(context: AssetExecutionContext, message_from_signal: Message) -> Dict:
    """
    Asset pour extraire les données du ticket avec Claude API
    
    Args:
        message_from_signal: Message Signal avec attachments (depuis l'asset message_from_signal)
    
    Returns:
        Dictionnaire avec l'extraction JSON de Claude
    """
    context.log.info("🤖 Extraction des données avec Claude API...")
    
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
    context.log.info("📝 Prompt généré avec les catégories de la base")
    
    # Ajouter le prompt
    claude_client.add_prompt(prompt)
    
    # Ajouter les images
    for attachment in message_from_signal.attachments:
        if attachment.path and attachment.content_type and attachment.content_type.startswith("image/"):
            claude_client.add_image(str(attachment.path))
    
    # Appeler Claude
    json_response = claude_client.call_json()
    
    context.log.info("✅ Extraction Claude réussie")
    
    return {
        "message": message_from_signal,
        "extraction": json_response
    }


@asset(
    deps=[claude_extraction, message_in_db]
)
def transformed_receipt(
    context: AssetExecutionContext,
    claude_extraction: Dict,
    message_in_db: Dict
) -> ReceiptData:
    """
    Asset pour transformer l'extraction Claude en ReceiptData
    
    Args:
        claude_extraction: Extraction JSON de Claude (depuis l'asset claude_extraction)
        message_in_db: Informations du message en base (depuis l'asset message_in_db)
    
    Returns:
        ReceiptData transformé
    """
    context.log.info("🔄 Transformation de l'extraction Claude...")
    
    claude_json = claude_extraction["extraction"]
    message_id = message_in_db.get("message_id")
    
    receipt_data = ReceiptTransformer.transform_claude_json(
        claude_json=claude_json,
        message_id=message_id
    )
    
    context.log.info(
        f"✅ Transformé: {receipt_data.store.store_name} - "
        f"{len(receipt_data.items)} articles"
    )
    
    return receipt_data


@asset(
    deps=[transformed_receipt, message_in_db]
)
def receipt_in_db(
    context: AssetExecutionContext,
    transformed_receipt: ReceiptData,
    message_in_db: Dict
) -> Dict:
    """
    Asset pour insérer le ticket dans la base de données
    
    Args:
        transformed_receipt: ReceiptData transformé (depuis l'asset transformed_receipt)
        message_in_db: Informations du message en base (depuis l'asset message_in_db)
    
    Returns:
        Dictionnaire avec les informations de la transaction insérée
    """
    context.log.info("💾 Insertion du ticket dans la base de données...")
    
    db_client = DatabaseClient(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5434")),
        database=os.getenv("DB_NAME", "receipt_processing"),
        user=os.getenv("DB_USER", "receipt_user"),
        password=os.getenv("DB_PASSWORD", "SuperSecretPassword123!")
    )
    
    message_id = message_in_db.get("message_id")
    attachment_ids = message_in_db.get("attachment_ids")
    
    transaction_id = db_client.insert_receipt(
        receipt_data=transformed_receipt,
        message_id=message_id,
        attachment_ids=attachment_ids
    )
    
    context.log.info(
        f"✅ Transaction {transaction_id} insérée: "
        f"{transformed_receipt.store.store_name} - {len(transformed_receipt.items)} articles"
    )
    
    return {
        "transaction_id": transaction_id,
        "store_name": transformed_receipt.store.store_name,
        "total": transformed_receipt.transaction.total
    }


@asset(deps=[receipt_in_db])
def notify_signal_success(
    context: AssetExecutionContext,
    receipt_in_db: Dict
) -> None:
    """
    Asset final qui envoie une notification Signal de succès à l'utilisateur.
    Il n'est exécuté que si tout le pipeline s'est bien déroulé.
    """
    phone_number = os.getenv("SIGNAL_PHONE_NUMBER")
    if not phone_number:
        context.log.warning("⚠️  SIGNAL_PHONE_NUMBER non défini, notification non envoyée")
        return

    client = SignalClient(phone_number=phone_number)

    # Récupérer les tags du run pour trouver le groupe et le sender
    tags = {}
    if hasattr(context, "run") and context.run:
        tags = context.run.tags or {}

    sender_name = tags.get("sender_name", "").strip()
    sender_number = tags.get("sender_number", "").strip()
    sender_uuid = tags.get("sender_uuid", "").strip()
    group_id = tags.get("group_id", "") or os.getenv("SIGNAL_GROUP_ID", "")
    group_name = tags.get("group_name", "")

    # Construire la mention
    mention = None
    if sender_name and sender_name.lower() not in ["unknown", "none", ""]:
        mention_name = sender_name.split()[0] if " " in sender_name else sender_name
        mention = f"@{mention_name}"
    elif sender_number:
        mention = f"@{sender_number[-4:]}" if len(sender_number) >= 4 else f"@{sender_number}"
    elif sender_uuid:
        mention = f"@{sender_uuid[:8]}"
    else:
        mention = "@utilisateur"

    # Construire le message de succès
    store_name = receipt_in_db.get("store_name", "Magasin")
    total = receipt_in_db.get("total")
    try:
        total_str = f"{float(total):.2f} CHF" if total is not None else ""
    except Exception:
        total_str = str(total) if total is not None else ""

    text = f"Ticket traité avec succès ! 🎉\n{store_name} - {total_str}"
    full_text = f"{mention} ✅ {text}"

    if not group_id:
        context.log.warning(
            "⚠️  Aucun group_id trouvé dans les tags ni dans SIGNAL_GROUP_ID, "
            "notification Signal non envoyée."
        )
        return

    try:
        client.send_to_group(group_id=group_id, text=full_text)
        context.log.info(f"✅ Notification Signal envoyée au groupe {group_name or group_id}")
    except Exception as e:
        context.log.warning(f"⚠️  Erreur lors de l'envoi de la notification Signal: {e}")


# Job pour orchestrer tous les assets
process_signal_message = define_asset_job(
    name="process_signal_message",
    selection=[
        message_from_signal,
        message_in_db,
        claude_extraction,
        transformed_receipt,
        receipt_in_db,
        notify_signal_success,
    ],
)
