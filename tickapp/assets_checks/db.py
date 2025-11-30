# tickapp/assets_checks/db.py
"""
Asset checks pour les assets de base de données
"""
from dagster import AssetCheckResult, AssetCheckSeverity, asset_check
from typing import Dict


@asset_check(asset="receipts_in_db")
def check_receipts_in_db(result: Dict) -> AssetCheckResult:
    """
    Vérifie que les tickets ont été insérés en base de données
    """
    if not result or not isinstance(result, dict):
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Résultat d'insertion invalide"
        )
    
    total_receipts = result.get("total_receipts", 0)
    inserted_receipts = result.get("inserted_receipts", 0)
    transaction_ids = result.get("transaction_ids", [])
    
    if total_receipts == 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description="⚠️  Avertissement: Aucun ticket à insérer"
        )
    
    if inserted_receipts == 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Aucun ticket inséré en base de données"
        )
    
    if inserted_receipts < total_receipts:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description=f"⚠️  Avertissement: Seulement {inserted_receipts}/{total_receipts} ticket(s) inséré(s)"
        )
    
    if len(transaction_ids) != inserted_receipts:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description=f"⚠️  Avertissement: Nombre de transaction_ids ({len(transaction_ids)}) ne correspond pas au nombre d'insertions ({inserted_receipts})"
        )
    
    return AssetCheckResult(
        passed=True,
        description=f"✅ {inserted_receipts}/{total_receipts} ticket(s) inséré(s) avec succès"
    )

