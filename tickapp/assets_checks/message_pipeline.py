# tickapp/assets_checks/message_pipeline.py
"""
Asset checks pour le pipeline de traitement des messages Signal

Note: Les notifications Signal sont gérées par les hooks dans message_pipeline.py.
Ces checks peuvent être utilisés pour des validations supplémentaires si nécessaire.
"""
from dagster import AssetCheckResult, AssetCheckSeverity, asset_check
from typing import Dict

# Note: Ces checks sont documentés mais ne sont pas actuellement attachés aux ops.
# Les hooks dans message_pipeline.py gèrent déjà les notifications Signal en cas d'erreur/succès.


@asset_check(asset="get_message_from_signal")
def check_message_retrieved(result) -> AssetCheckResult:
    """
    Vérifie que le message a été récupéré avec succès
    """
    if result is None:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Message Signal non récupéré"
        )
    
    if not hasattr(result, 'has_attachments') or not result.has_attachments:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Le message n'a pas d'attachments"
        )
    
    return AssetCheckResult(
        passed=True,
        description="✅ Message Signal récupéré avec succès"
    )


@asset_check(asset="insert_message_in_db")
def check_message_in_db(result: Dict) -> AssetCheckResult:
    """
    Vérifie que le message a été inséré en base de données
    """
    if not result or "message_id" not in result:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Message non inséré en base de données"
        )
    
    return AssetCheckResult(
        passed=True,
        description=f"✅ Message {result['message_id']} inséré en base"
    )


@asset_check(asset="extract_with_claude")
def check_claude_extraction(result: Dict) -> AssetCheckResult:
    """
    Vérifie que l'extraction Claude a réussi
    """
    if not result or "extraction" not in result:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Extraction Claude échouée"
        )
    
    extraction = result["extraction"]
    if "articles" not in extraction or len(extraction.get("articles", [])) == 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description="⚠️  Avertissement: Aucun article extrait"
        )
    
    return AssetCheckResult(
        passed=True,
        description=f"✅ Extraction Claude réussie: {len(extraction.get('articles', []))} articles"
    )


@asset_check(asset="transform_receipt")
def check_receipt_transformed(result) -> AssetCheckResult:
    """
    Vérifie que la transformation a réussi
    """
    if result is None:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Transformation échouée"
        )
    
    if not hasattr(result, 'items') or not result.items or len(result.items) == 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description="⚠️  Avertissement: Aucun item transformé"
        )
    
    return AssetCheckResult(
        passed=True,
        description=f"✅ Transformation réussie: {len(result.items)} items"
    )


@asset_check(asset="insert_receipt_in_db")
def check_receipt_in_db(result: Dict) -> AssetCheckResult:
    """
    Vérifie que le ticket a été inséré en base de données
    """
    if not result or "transaction_id" not in result:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Ticket non inséré en base de données"
        )
    
    return AssetCheckResult(
        passed=True,
        description=f"✅ Ticket {result['transaction_id']} inséré: {result.get('store_name', 'N/A')} - {result.get('total', 0)}"
    )

