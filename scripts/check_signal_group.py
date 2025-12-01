#!/usr/bin/env python3
"""
Script pour vérifier et diagnostiquer les problèmes de permissions Signal
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tickapp.clients.signal_client import SignalClient

# Charger le .env
load_dotenv()

def main():
    phone_number = os.getenv("SIGNAL_PHONE_NUMBER")
    group_id = os.getenv("SIGNAL_GROUP_ID")
    
    if not phone_number:
        print("❌ SIGNAL_PHONE_NUMBER non défini dans .env")
        return
    
    print(f"📱 Numéro du bot: {phone_number}")
    print()
    
    client = SignalClient(phone_number=phone_number)
    
    # Lister tous les groupes
    print("📋 Groupes disponibles:")
    print("-" * 60)
    groups = client.list_groups()
    
    if not groups:
        print("⚠️  Aucun groupe trouvé. Le bot n'est dans aucun groupe.")
        print()
        print("💡 Solution:")
        print("   1. Ouvrez Signal sur votre téléphone")
        print(f"   2. Ajoutez le numéro {phone_number} au groupe 'Tickets 🧾'")
        print("   3. Relancez ce script pour vérifier")
        return
    
    for i, group in enumerate(groups, 1):
        marker = "✅" if group_id and group.id == group_id else "  "
        print(f"{marker} {i}. {group.name}")
        print(f"   ID: {group.id}")
        print()
    
    # Vérifier si le group_id du .env correspond à un groupe
    if group_id:
        print(f"🔍 Recherche du groupe configuré (ID: {group_id})...")
        found = False
        for group in groups:
            if group.id == group_id:
                found = True
                print(f"✅ Groupe trouvé: {group.name}")
                print()
                print("🧪 Test d'envoi d'un message de test...")
                try:
                    client.send_to_group(
                        group_id=group_id,
                        text="🧪 Message de test - Si vous voyez ce message, tout fonctionne !"
                    )
                    print("✅ Message envoyé avec succès !")
                except Exception as e:
                    print(f"❌ Erreur lors de l'envoi: {e}")
                    print()
                    print("💡 Solutions possibles:")
                    print("   1. Vérifiez que le bot est bien membre du groupe")
                    print("   2. Vérifiez que le groupe n'a pas de restrictions d'envoi")
                    print("   3. Essayez d'envoyer un message depuis Signal pour vérifier")
                break
        
        if not found:
            print(f"❌ Groupe avec ID '{group_id}' non trouvé dans la liste")
            print()
            print("💡 Solutions:")
            print("   1. Vérifiez que SIGNAL_GROUP_ID dans .env correspond à un groupe existant")
            print("   2. Utilisez l'un des IDs listés ci-dessus")
    else:
        print("⚠️  SIGNAL_GROUP_ID non défini dans .env")
        print()
        print("💡 Pour définir le groupe par défaut:")
        print("   Ajoutez SIGNAL_GROUP_ID=<group_id> dans votre .env")
        print("   Utilisez l'un des IDs listés ci-dessus")

if __name__ == "__main__":
    main()

