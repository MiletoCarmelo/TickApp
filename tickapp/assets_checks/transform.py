# tickapp/assets_checks/transform.py
"""
Asset checks pour les assets de transformation
"""
from dagster import AssetCheckResult, AssetCheckSeverity, asset_check
from typing import List, Dict


@asset_check(asset="transformed_receipts")
def check_transformed_receipts(result: List[Dict]) -> AssetCheckResult:
    """
    Vérifie que les transformations ont réussi
    """
    if result is None:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Aucune transformation retournée"
        )
    
    if not isinstance(result, list):
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Le résultat n'est pas une liste de transformations"
        )
    
    if len(result) == 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description="⚠️  Avertissement: Aucune transformation effectuée"
        )
    
    # Vérifier la qualité des transformations
    valid_transformations = 0
    invalid_transformations = 0
    
    for transformed_data in result:
        if not isinstance(transformed_data, dict):
            invalid_transformations += 1
            continue
        
        receipt_data = transformed_data.get("receipt_data")
        if not receipt_data:
            invalid_transformations += 1
            continue
        
        # Vérifier qu'il y a des items
        if not hasattr(receipt_data, 'items') or not receipt_data.items or len(receipt_data.items) == 0:
            invalid_transformations += 1
            continue
        
        # Vérifier qu'il y a un store
        if not hasattr(receipt_data, 'store') or not receipt_data.store:
            invalid_transformations += 1
            continue
        
        # Vérifier qu'il y a une transaction
        if not hasattr(receipt_data, 'transaction') or not receipt_data.transaction:
            invalid_transformations += 1
            continue
        
        valid_transformations += 1
    
    if invalid_transformations > 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description=f"⚠️  Avertissement: {invalid_transformations}/{len(result)} transformation(s) invalide(s)"
        )
    
    return AssetCheckResult(
        passed=True,
        description=f"✅ {valid_transformations} transformation(s) réussie(s)"
    )

