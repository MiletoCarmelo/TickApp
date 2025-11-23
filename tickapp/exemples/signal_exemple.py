"""
Exemples d'utilisation du Signal Client Python

Ces exemples montrent comment utiliser le client Signal pour différents cas d'usage.
"""

from signal_client import SignalClient, SignalBot, Message, Attachment
from pathlib import Path
import json
from datetime import datetime


# =============================================================================
# EXEMPLE 1 : Client basique - Envoyer et recevoir des messages
# =============================================================================

def exemple_client_basique():
    """Utilisation basique du client Signal"""
    
    # Initialiser le client
    client = SignalClient(phone_number="+41791234567")
    
    # Envoyer un message simple
    client.send_message(
        recipient="+41797654321",
        text="Hello from Python! 👋"
    )
    
    # Envoyer un message avec pièce jointe
    client.send_message(
        recipient="+41797654321",
        text="Voici mon ticket de caisse",
        attachments=[Path("./ticket.jpg")]
    )
    
    # Recevoir les nouveaux messages
    messages = client.receive()
    
    for message in messages:
        print(f"Message de {message.sender.name}: {message.text}")
        
        # Télécharger les pièces jointes
        for attachment in message.attachments:
            output = Path(f"./downloads/{attachment.filename}")
            client.download_attachment(attachment, output)


# =============================================================================
# EXEMPLE 2 : Bot simple avec handlers
# =============================================================================

def exemple_bot_simple():
    """Bot simple qui répond aux messages"""
    
    bot = SignalBot(
        phone_number="+41791234567",
        group_filter="Tickets 🧾"  # Filtrer par groupe
    )
    
    @bot.on_message
    def echo_handler(message: Message):
        """Répond à chaque message"""
        if message.text:
            bot.client.send_to_group(
                group_id=message.group.id,
                text=f"✅ Message reçu: {message.text}"
            )
    
    bot.run(interval=30)


# =============================================================================
# EXEMPLE 3 : Bot pour tickets de caisse (cas d'usage réel)
# =============================================================================

def exemple_bot_tickets():
    """Bot complet pour gérer les tickets de caisse"""
    
    # Configuration
    PHONE_NUMBER = "+41791234567"
    GROUP_NAME = "Tickets 🧾"
    TICKETS_DIR = Path("./data/tickets")
    TICKETS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Mapping famille
    FAMILY = {
        "+41791111111": "Carmelo",
        "+41792222222": "Sophie",
        "+41793333333": "Marc"
    }
    
    # Créer le bot
    bot = SignalBot(phone_number=PHONE_NUMBER, group_filter=GROUP_NAME)
    
    @bot.on_message
    def log_message(message: Message):
        """Log tous les messages"""
        user = FAMILY.get(message.sender.number, message.sender.number)
        print(f"\n📨 Message de {user}")
        print(f"   Heure: {message.timestamp.strftime('%H:%M:%S')}")
        if message.text:
            print(f"   Texte: {message.text}")
    
    @bot.on_attachment
    def save_ticket(message: Message, attachment: Attachment, file_path: Path):
        """Sauvegarde les tickets avec metadata"""
        
        # Identifier l'utilisateur
        user = FAMILY.get(message.sender.number, "Unknown")
        
        # Créer dossier utilisateur
        user_dir = TICKETS_DIR / user
        user_dir.mkdir(exist_ok=True)
        
        # Nom de fichier
        timestamp = message.timestamp.strftime('%Y%m%d_%H%M%S')
        
        if attachment.is_image:
            ext = '.jpg'
            file_type = 'photo'
        elif attachment.is_pdf:
            ext = '.pdf'
            file_type = 'pdf'
        else:
            ext = Path(attachment.filename).suffix or '.dat'
            file_type = 'other'
        
        dest_file = user_dir / f"{timestamp}_{file_type}{ext}"
        
        # Copier le fichier
        import shutil
        shutil.copy2(file_path, dest_file)
        
        # Créer metadata JSON
        metadata = {
            'user': user,
            'sender_number': message.sender.number,
            'timestamp': message.timestamp.isoformat(),
            'file_type': file_type,
            'file_path': str(dest_file),
            'original_filename': attachment.filename,
            'size': attachment.size,
            'processed': False
        }
        
        metadata_file = dest_file.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"   ✅ Ticket sauvegardé: {dest_file.name}")
        print(f"   📊 Metadata: {metadata_file.name}")
        
        # Confirmer dans le groupe
        bot.client.send_to_group(
            group_id=message.group.id,
            text=f"✅ Ticket de {user} bien reçu et sauvegardé !"
        )
    
    # Lancer le bot
    print(f"🤖 Bot Tickets démarré")
    print(f"📱 Numéro: {PHONE_NUMBER}")
    print(f"👥 Groupe: {GROUP_NAME}")
    print(f"💾 Dossier: {TICKETS_DIR}\n")
    
    bot.run(interval=30)


# =============================================================================
# EXEMPLE 4 : Gestion des groupes
# =============================================================================

def exemple_gestion_groupes():
    """Exemples de gestion des groupes"""
    
    client = SignalClient(phone_number="+41791234567")
    
    # Lister tous les groupes
    groups = client.list_groups()
    
    for group in groups:
        print(f"Groupe: {group.name}")
        print(f"  ID: {group.id}")
        print(f"  Membres: {len(group.members)}")
    
    # Trouver un groupe par nom
    tickets_group = client.find_group_by_name("Tickets")
    
    if tickets_group:
        print(f"\nGroupe trouvé: {tickets_group.name}")
        print(f"ID: {tickets_group.id}")
        
        # Envoyer un message au groupe
        client.send_to_group(
            group_id=tickets_group.id,
            text="Hello du bot! 🤖"
        )


# =============================================================================
# EXEMPLE 5 : Bot avec statistiques en temps réel
# =============================================================================

def exemple_bot_stats():
    """Bot qui affiche des statistiques"""
    
    PHONE_NUMBER = "+41791234567"
    GROUP_NAME = "Tickets 🧾"
    
    # Stats
    stats = {
        'total_messages': 0,
        'total_photos': 0,
        'total_pdfs': 0,
        'by_user': {}
    }
    
    bot = SignalBot(phone_number=PHONE_NUMBER, group_filter=GROUP_NAME)
    
    @bot.on_message
    def count_message(message: Message):
        """Compte les messages"""
        stats['total_messages'] += 1
        
        user = message.sender.name or message.sender.number
        stats['by_user'][user] = stats['by_user'].get(user, 0) + 1
        
        print(f"\n📊 Stats:")
        print(f"   Messages: {stats['total_messages']}")
        print(f"   Photos: {stats['total_photos']}")
        print(f"   PDFs: {stats['total_pdfs']}")
    
    @bot.on_attachment
    def count_attachment(message: Message, attachment: Attachment, file_path: Path):
        """Compte les pièces jointes"""
        if attachment.is_image:
            stats['total_photos'] += 1
        elif attachment.is_pdf:
            stats['total_pdfs'] += 1
    
    bot.run(interval=30)


# =============================================================================
# EXEMPLE 6 : Enregistrement initial du bot
# =============================================================================

def exemple_enregistrement():
    """Enregistrer un nouveau numéro avec Signal"""
    
    client = SignalClient(phone_number="+41791234567")
    
    # Étape 1: Demander l'enregistrement
    print("📝 Envoi de la demande d'enregistrement...")
    client.register()
    
    # Tu recevras un SMS avec un code
    print("\n⏳ Attendre le SMS avec le code de vérification...")
    code = input("Code reçu par SMS: ")
    
    # Étape 2: Vérifier avec le code
    print(f"\n🔐 Vérification avec le code {code}...")
    client.verify(code)
    
    # Étape 3: Configurer le profil
    print("\n✏️  Configuration du profil...")
    client.update_profile(
        name="Tickets Bot",
        about="Bot pour gérer les tickets de caisse",
        emoji="🧾"
    )
    
    print("\n✅ Bot enregistré avec succès!")


# =============================================================================
# EXEMPLE 7 : Bot avec traitement asynchrone
# =============================================================================

def exemple_bot_async():
    """Bot qui traite les messages de manière asynchrone"""
    
    import queue
    import threading
    
    PHONE_NUMBER = "+41791234567"
    GROUP_NAME = "Tickets 🧾"
    
    # Queue pour traitement asynchrone
    message_queue = queue.Queue()
    
    def worker():
        """Thread worker pour traiter les messages"""
        while True:
            message = message_queue.get()
            
            # Traitement lourd ici (OCR, etc.)
            print(f"🔄 Traitement de {message.sender.name}...")
            import time
            time.sleep(2)  # Simuler traitement
            print(f"✅ Traitement terminé")
            
            message_queue.task_done()
    
    # Démarrer le worker thread
    threading.Thread(target=worker, daemon=True).start()
    
    # Bot
    bot = SignalBot(phone_number=PHONE_NUMBER, group_filter=GROUP_NAME)
    
    @bot.on_message
    def queue_message(message: Message):
        """Ajoute à la queue au lieu de traiter directement"""
        message_queue.put(message)
        print(f"📥 Message en queue ({message_queue.qsize()} en attente)")
    
    bot.run(interval=30)


# =============================================================================
# EXEMPLE 8 : Mode daemon pour écoute continue
# =============================================================================

def exemple_daemon():
    """Utiliser signal-cli en mode daemon"""
    
    client = SignalClient(phone_number="+41791234567")
    
    # Démarrer le daemon
    daemon = client.daemon_start()
    
    print("🔄 Daemon démarré, écoute des messages...")
    
    try:
        # Lire stdout en continu
        for line in daemon.stdout:
            if line.strip():
                try:
                    data = json.loads(line)
                    print(f"📨 Message reçu: {data}")
                except json.JSONDecodeError:
                    pass
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du daemon")
        daemon.terminate()


# =============================================================================
# Main - Choix de l'exemple à lancer
# =============================================================================

if __name__ == "__main__":
    print("Signal Client Python - Exemples\n")
    print("1. Client basique")
    print("2. Bot simple")
    print("3. Bot tickets (RECOMMANDÉ)")
    print("4. Gestion groupes")
    print("5. Bot avec stats")
    print("6. Enregistrement bot")
    print("7. Bot async")
    print("8. Mode daemon")
    
    choix = input("\nChoisir un exemple (1-8): ")
    
    exemples = {
        '1': exemple_client_basique,
        '2': exemple_bot_simple,
        '3': exemple_bot_tickets,
        '4': exemple_gestion_groupes,
        '5': exemple_bot_stats,
        '6': exemple_enregistrement,
        '7': exemple_bot_async,
        '8': exemple_daemon
    }
    
    if choix in exemples:
        print(f"\n{'='*60}")
        print(f"Lancement de l'exemple {choix}")
        print(f"{'='*60}\n")
        exemples[choix]()
    else:
        print("❌ Choix invalide")