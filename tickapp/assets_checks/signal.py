# tickapp/assets_checks/signal.py
"""
Asset checks pour les assets Signal
"""
from dagster import AssetCheckResult, AssetCheckSeverity, asset_check
from typing import List, Dict

from tickapp.clients.signal_client import Message


@asset_check(asset="signal_messages")
def check_signal_messages_received(result: List[Message]) -> AssetCheckResult:
    """
    Vérifie que les messages Signal ont été reçus avec succès
    """
    if result is None:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Aucun message Signal reçu"
        )
    
    if not isinstance(result, list):
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Le résultat n'est pas une liste de messages"
        )
    
    if len(result) == 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description="⚠️  Avertissement: Aucun message Signal reçu"
        )
    
    # Compter les messages avec attachments
    messages_with_att = [msg for msg in result if hasattr(msg, 'has_attachments') and msg.has_attachments]
    
    return AssetCheckResult(
        passed=True,
        description=f"✅ {len(result)} message(s) Signal reçu(s), {len(messages_with_att)} avec attachments"
    )


@asset_check(asset="signal_messages_in_db")
def check_signal_messages_in_db(result: Dict) -> AssetCheckResult:
    """
    Vérifie que les messages Signal ont été insérés en base de données
    """
    if not result or not isinstance(result, dict):
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Résultat d'insertion invalide"
        )
    
    total_messages = result.get("total_messages", 0)
    inserted_messages = result.get("inserted_messages", 0)
    message_ids = result.get("message_ids", [])
    
    if total_messages == 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description="⚠️  Avertissement: Aucun message à insérer"
        )
    
    if inserted_messages == 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Aucun message inséré en base de données"
        )
    
    if inserted_messages < total_messages:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description=f"⚠️  Avertissement: Seulement {inserted_messages}/{total_messages} messages insérés"
        )
    
    return AssetCheckResult(
        passed=True,
        description=f"✅ {inserted_messages}/{total_messages} message(s) inséré(s) avec succès"
    )

