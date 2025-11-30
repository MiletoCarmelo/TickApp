"""
Signal Client Python - Interface moderne pour signal-cli

Ce client fournit une interface Python propre pour interagir avec Signal
via signal-cli. Support complet pour messages, groupes, et pièces jointes.

Auteur: Carmelo
License: MIT
"""

import json
import subprocess
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
import platform
import os


# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types de messages Signal"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    STICKER = "sticker"


@dataclass
class Attachment:
    """Représente une pièce jointe Signal"""
    id: str
    content_type: str
    filename: str
    size: int
    upload_timestamp_ms: int
    path: Optional[Path] = None
    
    @property
    def is_image(self) -> bool:
        return self.content_type.startswith('image/')
    
    @property
    def is_pdf(self) -> bool:
        return self.content_type == 'application/pdf' or self.filename.endswith('.pdf')
    
    @property
    def is_video(self) -> bool:
        return self.content_type.startswith('video/')


@dataclass
class Contact:
    """Représente un contact Signal"""
    number: str
    name: Optional[str] = None
    uuid: Optional[str] = None
    
    def __str__(self):
        return self.name or self.number


@dataclass
class Group:
    """Représente un groupe Signal"""
    id: str
    name: str
    
    def __str__(self):
        return f"{self.name}"


@dataclass
class Message:
    """Représente un message Signal reçu"""
    sender: Contact
    timestamp: datetime
    text: Optional[str] = None
    attachments: List[Attachment] = None
    group: Optional[Group] = None
    is_group_message: bool = False
    account: Optional[str] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
    
    @property
    def has_attachments(self) -> bool:
        return len(self.attachments) > 0
    
    @property
    def message_type(self) -> MessageType:
        if self.attachments:
            att = self.attachments[0]
            if att.is_image:
                return MessageType.IMAGE
            elif att.is_pdf:
                return MessageType.DOCUMENT
            elif att.is_video:
                return MessageType.VIDEO
        return MessageType.TEXT


class SignalException(Exception):
    """Exception de base pour le client Signal"""
    pass


class SignalCLINotFound(SignalException):
    """signal-cli n'est pas installé ou introuvable"""
    pass


class SignalAuthException(SignalException):
    """Problème d'authentification"""
    pass


class SignalClient:
    """
    Client Python pour Signal via signal-cli
    
    Usage:
        client = SignalClient(phone_number="+41791234567")
        
        # Recevoir messages
        messages = client.receive()
        
        # Envoyer message
        client.send_message(recipient="+41797654321", text="Hello!")
        
        # Envoyer à un groupe
        client.send_to_group(group_id="xyz", text="Hello group!")
    """
    
    def __init__(
            self,
            phone_number: str,
            signal_cli_path: str = "signal-cli",
            attachment_dir: Optional[Path] = None
        ):
            """
            Initialise le client Signal
            
            Args:
                phone_number: Numéro de téléphone du bot (format international)
                signal_cli_path: Chemin vers signal-cli (par défaut dans PATH)
                attachment_dir: Dossier pour sauvegarder les pièces jointes
            """
            self.phone_number = phone_number
            self.signal_cli_path = signal_cli_path
            
            # Dossier pour attachments
            if attachment_dir is None:
                self.attachment_dir = Path.home() / ".local/share/signal-cli/attachments"
            else:
                self.attachment_dir = Path(attachment_dir)
            
            self.attachment_dir.mkdir(parents=True, exist_ok=True)
            
            # Vérifier que signal-cli est installé
            if not self._check_signal_cli():
                raise SignalCLINotFound(
                    f"signal-cli introuvable. Installez-le avec: brew install signal-cli"
                )
            
            logger.info(f"✅ Signal Client initialisé pour {phone_number}")
    
    def _check_signal_cli(self) -> bool:
        """Vérifie que signal-cli est installé"""
        try:
            result = subprocess.run(
                [self.signal_cli_path, "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _run_command(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        Exécute une commande signal-cli
        
        Args:
            args: Arguments de la commande
            check: Raise exception si erreur
        
        Returns:
            CompletedProcess avec stdout/stderr
        """
        cmd = [self.signal_cli_path, "-a", self.phone_number] + args
        
        logger.debug(f"🔧 Commande: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if check and result.returncode != 0:
            logger.error(f"❌ Erreur signal-cli: {result.stderr}")
            raise SignalException(f"signal-cli error: {result.stderr}")
        
        return result
    
    def register(self, captcha: Optional[str] = None) -> str:
        """
        Enregistre le numéro auprès de Signal
        
        Args:
            captcha: Token captcha (si nécessaire)
        
        Returns:
            Message de confirmation
        """
        args = ["register"]
        if captcha:
            args.extend(["--captcha", captcha])
        
        result = self._run_command(args)
        logger.info(f"📝 Enregistrement initié. Vérifiez votre SMS.")
        return result.stdout
    
    def verify(self, code: str) -> str:
        """
        Vérifie le numéro avec le code SMS reçu
        
        Args:
            code: Code de vérification reçu par SMS
        
        Returns:
            Message de confirmation
        """
        result = self._run_command(["verify", code])
        logger.info(f"✅ Numéro vérifié avec succès")
        return result.stdout
    
    def update_profile(
            self,
            name: Optional[str] = None,
            about: Optional[str] = None,
            emoji: Optional[str] = None
        ) -> None:
            """
            Met à jour le profil Signal
            
            Args:
                name: Nom d'affichage
                about: Description
                emoji: Emoji de profil
            """
            args = ["updateProfile"]
            
            if name:
                args.extend(["--name", name])
            if about:
                args.extend(["--about", about])
            if emoji:
                args.extend(["--about-emoji", emoji])
            
            self._run_command(args)
            logger.info(f"✅ Profil mis à jour")


    def receive(self, number_of_messages: int = 100000, output_format: str = "json") -> List[Message]:
            """
            Reçoit les nouveaux messages d'un groupe
            
            Args:
                group_id: ID du groupe
                number_of_messages: Nombre de messages à reçu
            
            Returns:
                Liste des messages reçus
            """
            if output_format == "json":
                args = ["-o", "json"]
            elif output_format == "plain-text":
                args = ["-o", "plain-text"]
            else:
                raise ValueError(f"Format de sortie non valide: {output_format}")

            args.extend(["-a", self.phone_number, "receive" , "--max-messages", str(number_of_messages), "--send-read-receipts"])

            result = self._run_command(args)

            return result.stdout

    def _convert_to_json(self, data: str) -> Dict:
        """Convertit une chaîne de caractères en JSON"""
        if isinstance(data, str) and data != '': 
            return json.loads(data)
        else :
            return {}

    def _parse_message(self, data: str) -> Optional[Message]:
            """Parse un message JSON de signal-cli"""

            messages = []
            for line in data.strip().split('\n'):
                if line.strip():
                    msg_json = json.loads(line)
                    messages.append(msg_json)
            messages

            output = []
            for msg_json in messages:
            
                if msg_json == {}:
                    output.append(Message(
                        sender=Contact(number='', name='', uuid=''),
                        timestamp=datetime.now(),
                        text=None,
                        attachments=[],
                        group=None,
                        is_group_message=False
                    ))

                envelope = msg_json.get('envelope', {})
                data_message = envelope.get('dataMessage', {})
                
                if 'remoteDelete' in data_message:
                    remote_delete = data_message['remoteDelete']
                    logger.info(f"🗑️  Message supprimé (timestamp: {remote_delete.get('timestamp')})")
                    continue
                
                account = envelope.get('account', '')
                
                # Extract source and sourceUuid - Signal peut mettre l'UUID dans 'source' parfois
                source = envelope.get('source') or envelope.get('sourceNumber')
                source_uuid = envelope.get('sourceUuid')
                
                # Détecter si 'source' est un UUID ou un numéro de téléphone
                # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (avec ou sans tirets)
                uuid_pattern = re.compile(r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$', re.IGNORECASE)
                
                if source and uuid_pattern.match(source):
                    # 'source' est un UUID, pas un numéro
                    sender_uuid = source
                    sender_number = None  # Pas de numéro disponible
                else:
                    # 'source' est un numéro de téléphone
                    sender_number = source
                    sender_uuid = source_uuid  # Utiliser sourceUuid si disponible
                
                sender_name = envelope.get('sourceName')
                
                sender = Contact(
                    number=sender_number or '',  # Utiliser string vide si pas de numéro
                    name=sender_name,
                    uuid=sender_uuid
                )
                
                timestamp_ms = envelope.get('timestamp', 0)
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                
                text = data_message.get('message')

                attachments = []
                for att_data in data_message.get('attachments', []):
                    attachment = Attachment(
                        content_type=att_data.get('contentType', ''),
                        id=att_data.get('id', ''),
                        filename=att_data.get('filename', ''),
                        size=att_data.get('size', 0),
                        upload_timestamp_ms=att_data.get('uploadTimestamp', 0)
                    )
                    attachments.append(attachment)  

                group = None
                is_group = False
                group_info = data_message.get('groupInfo')

                if group_info:
                    is_group = True
                    group = Group(
                        id=group_info.get('groupId', ''),
                        name=group_info.get('name', 'Unknown')
                    )

                output.append(Message(
                    sender=sender,
                    timestamp=timestamp,
                    text=text,
                    attachments=attachments,
                    group=group,
                    is_group_message=is_group,
                    account=account
                ))

            return output
    

    def send_message(
            self,
            recipient: str,
            text: str,
            attachments: Optional[List[Path]] = None
        ) -> None:
            """
            Envoie un message à un contact
            
            Args:
                recipient: Numéro du destinataire (format international)
                text: Texte du message
                attachments: Liste de fichiers à envoyer
            """
            args = ["send", "-m", text]
            
            if attachments:
                for attachment in attachments:
                    args.extend(["-a", str(attachment)])
            
            args.append(recipient)
            
            self._run_command(args)
            logger.info(f"✅ Message envoyé à {recipient}")
    
    def send_to_group(
            self,
            group_id: str,
            text: str,
            attachments: Optional[List[Path]] = None
        ) -> None:
            """
            Envoie un message à un groupe
            
            Args:
                group_id: ID du groupe
                text: Texte du message
                attachments: Liste de fichiers à envoyer
            """
            args = ["send", "-m", text, "-g", group_id]
            
            if attachments:
                for attachment in attachments:
                    args.extend(["-a", str(attachment)])
            
            self._run_command(args)
            logger.info(f"✅ Message envoyé au groupe {group_id}")
    
    def list_groups(self) -> List[Group]:
        """
        Liste tous les groupes
        
        Returns:
            Liste des groupes
        """
        result = self._run_command(["listGroups", "-d"])
        
        groups = []
        current_group = None
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            if line.startswith('Id:'):
                # Nouvelle groupe
                if current_group:
                    groups.append(current_group)
                
                parts = line.split()
                group_id = parts[1] if len(parts) > 1 else ""
                
                # Extraire le nom
                name_start = line.find('Name:')
                if name_start != -1:
                    name = line[name_start+5:].split()[0].strip()
                else:
                    name = "Unknown"
                
                current_group = Group(
                    id=group_id,
                    name=name,
                    members=[],
                    admins=[]
                )
        
        if current_group:
            groups.append(current_group)
        
        logger.info(f"📋 {len(groups)} groupe(s) trouvé(s)")
        return groups

    def _get_signal_cli_attachments_dir(self) -> Path:
        """
        Retourne le dossier des attachments signal-cli selon l'OS
        """
        system = platform.system()
        
        if system == "Windows":
            # Windows : %USERPROFILE%\.local\share\signal-cli\attachments
            base = Path(os.environ.get("USERPROFILE", "~"))
            return base / ".local" / "share" / "signal-cli" / "attachments"
        
        else:  # macOS et Linux
            # Unix-like : ~/.local/share/signal-cli/attachments
            return Path.home() / ".local" / "share" / "signal-cli" / "attachments" 
    
    def download_attachment(self, phone_number: str,   messages: list[Message]) -> str:
        """
        Télécharge une pièce jointe
        
        Args:
            attachment_id: ID de la pièce jointe à télécharger
            output_path: Chemin de destination
        """

        messages_with_attachments_paths = []
        for message in messages:

            attachments_output = []

            for attachment in message.attachments:
                args = ["-a", phone_number, "getAttachment", "--id", attachment.id, "--group", message.group.id]
                self._run_command(args)
                output_path = self._get_signal_cli_attachments_dir() / attachment.id
                attachment.path = output_path
                attachments_output.append(attachment)

            message.attachments = attachments_output
            messages_with_attachments_paths.append(message)


        return messages_with_attachments_paths
            

    def daemon_start(self) -> subprocess.Popen:
        """
        Démarre signal-cli en mode daemon pour écoute continue
        
        Returns:
            Process du daemon
        """
        cmd = [self.signal_cli_path, "-a", self.phone_number, "daemon", "--json"]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"🔄 Daemon démarré (PID: {process.pid})")
        return process


class SignalBot:
    """
    Bot Signal avec handlers pour messages
    
    Usage:
        bot = SignalBot(phone_number="+41791234567")
        
        @bot.on_message
        def handle(message):
            print(f"Message from {message.sender}: {message.text}")
        
        bot.run()
    """
    
    def __init__(
        self,
        phone_number: str,
        group_filter: Optional[str] = None
    ):
        """
        Initialise le bot
        
        Args:
            phone_number: Numéro du bot
            group_filter: Filtrer par nom de groupe (optionnel)
        """
        self.client = SignalClient(phone_number)
        self.group_filter = group_filter
        self.message_handlers: List[Callable] = []
        self.attachment_handlers: List[Callable] = []
        self.processed_timestamps = set()
        
        # Trouver le groupe si filter spécifié
        self.target_group = None
        if group_filter:
            self.target_group = self.client.find_group_by_name(group_filter)
            if self.target_group:
                logger.info(f"🎯 Groupe cible: {self.target_group}")
            else:
                logger.warning(f"⚠️  Groupe '{group_filter}' introuvable")
    
    def on_message(self, handler: Callable[[Message], None]):
        """Décore une fonction comme handler de message"""
        self.message_handlers.append(handler)
        return handler
    
    def on_attachment(self, handler: Callable[[Message, Attachment, Path], None]):
        """Décore une fonction comme handler de pièce jointe"""
        self.attachment_handlers.append(handler)
        return handler
    
    def _should_process(self, message: Message) -> bool:
        """Vérifie si un message doit être traité"""
        # Éviter duplicata
        timestamp = message.timestamp.timestamp()
        if timestamp in self.processed_timestamps:
            return False
        
        # Filtrer par groupe si spécifié
        if self.target_group and message.group:
            if message.group.id != self.target_group.id:
                return False
        
        self.processed_timestamps.add(timestamp)
        return True
    
    def run(self, interval: int = 30, max_messages: Optional[int] = None):
        """
        Lance le bot en mode polling
        
        Args:
            interval: Intervalle entre vérifications (secondes)
            max_messages: Nombre max de messages à traiter (None = infini)
        """
        logger.info(f"🤖 Bot démarré (intervalle: {interval}s)")
        
        processed_count = 0
        
        try:
            while True:
                messages = self.client.receive()
                
                for message in messages:
                    if not self._should_process(message):
                        continue
                    
                    # Handlers de message
                    for handler in self.message_handlers:
                        try:
                            handler(message)
                        except Exception as e:
                            logger.error(f"❌ Erreur handler: {e}")
                    
                    # Handlers de pièces jointes
                    if message.has_attachments:
                        for attachment in message.attachments:
                            for handler in self.attachment_handlers:
                                try:
                                    # Télécharger temporairement
                                    temp_path = Path(f"/tmp/{attachment.filename}")
                                    self.client.download_attachment(attachment, temp_path)
                                    
                                    handler(message, attachment, temp_path)
                                except Exception as e:
                                    logger.error(f"❌ Erreur attachment handler: {e}")
                    
                    processed_count += 1
                    
                    if max_messages and processed_count >= max_messages:
                        logger.info(f"✅ {processed_count} messages traités, arrêt")
                        return
                
                # Attendre avant prochaine vérification
                import time
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info(f"\n🛑 Bot arrêté ({processed_count} messages traités)")


# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration
    PHONE_NUMBER = "+41791234567"  # Remplacer par ton numéro
    GROUP_NAME = "Tickets 🧾"      # Nom du groupe à surveiller
    
    # Créer le bot
    bot = SignalBot(phone_number=PHONE_NUMBER, group_filter=GROUP_NAME)
    
    # Handler pour tous les messages
    @bot.on_message
    def handle_message(message: Message):
        print(f"\n📨 Message de {message.sender.name or message.sender.number}")
        print(f"   Timestamp: {message.timestamp}")
        if message.text:
            print(f"   Texte: {message.text}")
        if message.has_attachments:
            print(f"   📎 {len(message.attachments)} pièce(s) jointe(s)")
    
    # Handler pour les pièces jointes
    @bot.on_attachment
    def handle_attachment(message: Message, attachment: Attachment, file_path: Path):
        print(f"\n📎 Pièce jointe reçue:")
        print(f"   Nom: {attachment.filename}")
        print(f"   Type: {attachment.content_type}")
        print(f"   Taille: {attachment.size} bytes")
        print(f"   Sauvegardé: {file_path}")
        
        # Exemple: copier vers dossier tickets
        tickets_dir = Path("./data/tickets")
        tickets_dir.mkdir(exist_ok=True, parents=True)
        
        user = message.sender.name or message.sender.number.replace('+', '')
        timestamp = message.timestamp.strftime('%Y%m%d_%H%M%S')
        
        ext = Path(attachment.filename).suffix or '.jpg'
        dest = tickets_dir / f"{user}_{timestamp}{ext}"
        
        import shutil
        shutil.copy2(file_path, dest)
        print(f"   ✅ Copié vers: {dest}")
    
    # Lancer le bot
    print(f"🚀 Lancement du bot pour le groupe '{GROUP_NAME}'")
    print(f"📱 Numéro: {PHONE_NUMBER}\n")
    
    bot.run(interval=30)