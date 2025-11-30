# tickapp/assets_checks/claude.py
"""
Asset checks pour les assets Claude
"""
from dagster import AssetCheckResult, AssetCheckSeverity, asset_check
from typing import List, Dict


@asset_check(asset="claude_extractions_from_messages")
def check_claude_extractions(result: List[Dict]) -> AssetCheckResult:
    """
    Vérifie que les extractions Claude ont réussi
    """
    if result is None:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Aucune extraction Claude retournée"
        )
    
    if not isinstance(result, list):
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.ERROR,
            description="❌ Échec: Le résultat n'est pas une liste d'extractions"
        )
    
    if len(result) == 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description="⚠️  Avertissement: Aucune extraction Claude effectuée"
        )
    
    # Vérifier la qualité des extractions
    valid_extractions = 0
    invalid_extractions = 0
    
    for extraction_data in result:
        if not isinstance(extraction_data, dict):
            invalid_extractions += 1
            continue
        
        extraction = extraction_data.get("extraction", {})
        if not extraction:
            invalid_extractions += 1
            continue
        
        # Vérifier qu'il y a des articles
        articles = extraction.get("articles", [])
        if not articles or len(articles) == 0:
            invalid_extractions += 1
            continue
        
        valid_extractions += 1
    
    if invalid_extractions > 0:
        return AssetCheckResult(
            passed=False,
            severity=AssetCheckSeverity.WARN,
            description=f"⚠️  Avertissement: {invalid_extractions}/{len(result)} extraction(s) invalide(s)"
        )
    
    return AssetCheckResult(
        passed=True,
        description=f"✅ {valid_extractions} extraction(s) Claude réussie(s)"
    )

