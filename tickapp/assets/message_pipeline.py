# tickapp/assets/message_pipeline.py
"""
Assets Dagster pour traiter un seul message Signal (pipeline par message)
Utilise la nouvelle API @asset au lieu de @op
"""
from dagster import asset, AssetExecutionContext, Config, HookContext, failure_hook, success_hook, define_asset_job
from typing import Optional, Dict
from datetime import datetime
import os
from dotenv import load_dotenv
from pydantic import Field

from tickapp.clients.signal_client import SignalClient, Message
from tickapp.clients.database_client import DatabaseClient
from tickapp.clients.claude_client import ClaudeClient
from tickapp.clients.prompt_client import PromptClient
from tickapp.transformers.receipt_transformer import ReceiptTransformer
from tickapp.models import ReceiptData

load_dotenv()


def send_signal_notification(
    context: HookContext,
    text: str = "",
    is_error: bool = False
) -> None:
    """
    Envoie une notification Signal
    
    Args:
        context: Contexte du hook Dagster
        text: Texte à envoyer
        is_error: Si True, préfixe avec ❌, sinon ✅
    """
    try:
        phone_number = os.getenv("SIGNAL_PHONE_NUMBER")
        if not phone_number:
            context.log.warning("⚠️  SIGNAL_PHONE_NUMBER non défini, notification non envoyée")
            return
        
        client = SignalClient(phone_number=phone_number)
        
        # Récupérer les infos depuis les run tags
        tags = {}
        if hasattr(context, 'run') and context.run:
            tags = context.run.tags
        elif hasattr(context, 'dagster_run') and context.dagster_run:
            tags = context.dagster_run.tags
        
        message_timestamp = tags.get("message_timestamp", "N/A")
        sender = tags.get("sender", "unknown")
        group_id = tags.get("group_id", "")
        group_name = tags.get("group_name", "")
        
        # Construire le message
        emoji = "❌" if is_error else "✅"
        full_text = f"{emoji} {text}\n\n📅 {message_timestamp}\n👤 {sender}"
        
        # Priorité 1: Utiliser le group_id depuis les tags (le plus fiable)
        if group_id:
            client.send_to_group(group_id=group_id, text=full_text)
            context.log.info(f"✅ Notification Signal envoyée au groupe {group_name or group_id}")
            return
        
        # Priorité 2: Essayer d'envoyer au groupe par défaut si configuré (via group_id dans env)
        # Note: find_group_by_name n'existe pas, donc on ne peut pas chercher par nom
        # Si besoin, passer directement group_id via variable d'environnement
        
        # Si aucun groupe trouvé, log un avertissement
        context.log.warning("⚠️  Aucun groupe Signal trouvé pour envoyer la notification")
            
    except Exception as e:
        # Ne pas faire échouer le pipeline si l'envoi de notification échoue
        context.log.warning(f"⚠️  Erreur lors de l'envoi de notification Signal: {e}")


@failure_hook(required_resource_keys=set())
def notify_signal_failure(context: HookContext):
    """
    Hook appelé en cas d'échec d'un asset
    """
    # Récupérer l'asset qui a échoué
    failed_asset = "unknown"
    if hasattr(context, 'step') and context.step:
        failed_asset = context.step.asset_key.to_user_string() if hasattr(context.step, 'asset_key') else "unknown"
    elif hasattr(context, 'asset_key'):
        failed_asset = context.asset_key.to_user_string()
    
    # Récupérer l'erreur
    error = "Unknown error"
    if hasattr(context, 'failure_exception') and context.failure_exception:
        error = str(context.failure_exception)
    elif hasattr(context, 'step_exception') and context.step_exception:
        error = str(context.step_exception)
    
    # Limiter la taille de l'erreur pour le message
    if len(error) > 200:
        error = error[:200] + "..."
    
    message = f"Échec du traitement du ticket\n\n🔧 Asset: {failed_asset}\n❌ Erreur: {error}"
    
    send_signal_notification(
        context=context,
        text=message,
        is_error=True
    )


@success_hook(required_resource_keys=set())
def notify_signal_success(context: HookContext):
    """
    Hook appelé en cas de succès du job complet
    """
    # Récupérer les infos depuis les métadonnées du run
    tags = {}
    
    if hasattr(context, 'run') and context.run:
        tags = context.run.tags
    elif hasattr(context, 'dagster_run') and context.dagster_run:
        tags = context.dagster_run.tags
    
    # Construire le message de succès
    message = (
        f"Ticket traité avec succès ! 🎉\n\n"
        f"✅ Pipeline terminé\n"
        f"📎 {tags.get('has_attachments', '0')} attachment(s) traité(s)"
    )
    
    send_signal_notification(
        context=context,
        text=message,
        is_error=False
    )


class MessageConfig(Config):
    """Configuration pour un message Signal"""
    message_timestamp: str = Field(description="Timestamp ISO du message")
    sender_uuid: Optional[str] = Field(default=None, description="UUID du sender")
    sender_number: Optional[str] = Field(default=None, description="Numéro de téléphone du sender")


@asset(
    hooks={notify_signal_failure}
)
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
    
    context.log.info(f"📱 Récupération du message Signal du {message_timestamp}...")
    
    phone_number = os.getenv("SIGNAL_PHONE_NUMBER")
    if not phone_number:
        raise ValueError("SIGNAL_PHONE_NUMBER non défini")
    
    client = SignalClient(phone_number=phone_number)
    
    # Recevoir les messages récents (augmenter pour trouver le message même s'il est plus ancien)
    raw_messages = client.receive(number_of_messages=100)
    messages = client._parse_message(raw_messages)
    
    # Trouver le message correspondant
    try:
        # Essayer de parser le timestamp avec timezone
        if 'Z' in message_timestamp or '+' in message_timestamp:
            target_timestamp = datetime.fromisoformat(message_timestamp.replace('Z', '+00:00'))
        else:
            target_timestamp = datetime.fromisoformat(message_timestamp)
    except ValueError as e:
        # Si échec, essayer sans timezone
        try:
            target_timestamp = datetime.fromisoformat(message_timestamp.replace('Z', ''))
        except ValueError:
            raise ValueError(
                f"Impossible de parser le timestamp '{message_timestamp}': {e}. "
                f"Format attendu: ISO 8601 (ex: '2024-01-01T12:00:00' ou '2024-01-01T12:00:00Z')"
            )
    
    # Normaliser pour comparaison (enlever timezone si présent)
    if target_timestamp.tzinfo:
        target_timestamp = target_timestamp.replace(tzinfo=None)
    
    message = None
    best_match = None
    best_score = float('inf')
    
    for msg in messages:
        # Comparer les timestamps (avec une tolérance plus large)
        # Le message peut avoir été reçu quelques secondes/minutes avant le traitement
        time_diff = abs((msg.timestamp - target_timestamp).total_seconds())
        
        if time_diff < 300:  # Tolérance de 5 minutes (300 secondes)
            score = time_diff
            
            # Bonus si le sender correspond
            sender_match = False
            if sender_uuid and msg.sender.uuid:
                if str(msg.sender.uuid) == sender_uuid:
                    sender_match = True
                    score -= 5  # Bonus pour match sender
            elif sender_number and msg.sender.number:
                if msg.sender.number == sender_number:
                    sender_match = True
                    score -= 5  # Bonus pour match sender
            
            if score < best_score:
                best_score = score
                best_match = msg
    
    message = best_match
    
    if not message:
        # Afficher quelques informations de debug
        context.log.warning(
            f"⚠️  Message non trouvé. Timestamp recherché: {target_timestamp}, "
            f"Nombre de messages vérifiés: {len(messages)}"
        )
        if messages:
            # Afficher les timestamps des messages récents pour debug
            recent_timestamps = [msg.timestamp.isoformat() for msg in messages[:5]]
            context.log.warning(f"   Timestamps des 5 premiers messages: {recent_timestamps}")
        
        raise ValueError(
            f"Message non trouvé pour timestamp {message_timestamp} "
            f"(sender_uuid={sender_uuid}, sender_number={sender_number}). "
            f"Le message est peut-être trop ancien ou déjà traité. "
            f"Vérifié {len(messages)} message(s) récent(s)."
        )
    
    # Télécharger les attachments
    messages_with_attachments = client.download_attachment(
        phone_number=client.phone_number,
        messages=[message]
    )
    
    if not messages_with_attachments:
        raise ValueError("Aucun message avec attachments trouvé")
    
    message = messages_with_attachments[0]
    
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
    deps=[message_from_signal],
    hooks={notify_signal_failure}
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
    deps=[message_from_signal],
    hooks={notify_signal_failure}
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
    deps=[claude_extraction, message_in_db],
    hooks={notify_signal_failure}
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
    deps=[transformed_receipt, message_in_db],
    hooks={notify_signal_failure, notify_signal_success}
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


# Job pour orchestrer tous les assets
process_signal_message = define_asset_job(
    name="process_signal_message",
    selection=[
        message_from_signal,
        message_in_db,
        claude_extraction,
        transformed_receipt,
        receipt_in_db
    ],
    hooks={notify_signal_failure, notify_signal_success}
)
