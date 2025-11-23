# Signal Client Python 🐍📱

Client Python moderne et complet pour Signal Messenger via signal-cli.

## ✨ Features

- ✅ **Interface Python propre** - Pas de manipulation JSON manuelle
- ✅ **Support messages texte** - Envoi et réception
- ✅ **Support pièces jointes** - Photos, PDFs, vidéos, etc.
- ✅ **Support groupes** - Envoi et réception dans les groupes
- ✅ **Bot framework** - Créer des bots avec des handlers
- ✅ **Type hints complets** - Excellent support IDE
- ✅ **Logging intégré** - Debug facile
- ✅ **Tests unitaires** - Code testé et fiable
- ✅ **E2EE natif** - Chiffrement bout-en-bout de Signal

## 📋 Prérequis

### 1. Installer signal-cli

**macOS:**
```bash
brew install signal-cli
```

**Linux (Ubuntu/Debian):**
```bash
# Télécharger dernière version
wget https://github.com/AsamK/signal-cli/releases/download/v0.13.1/signal-cli-0.13.1-Linux.tar.gz
tar xf signal-cli-0.13.1-Linux.tar.gz -C /opt
sudo ln -sf /opt/signal-cli-0.13.1/bin/signal-cli /usr/local/bin/

# Vérifier
signal-cli --version
```

**Raspberry Pi:**
```bash
# Version ARM
wget https://github.com/AsamK/signal-cli/releases/download/v0.13.1/signal-cli-0.13.1-Linux-arm64.tar.gz
tar xf signal-cli-0.13.1-Linux-arm64.tar.gz -C /opt
sudo ln -sf /opt/signal-cli-0.13.1/bin/signal-cli /usr/local/bin/
```

### 2. Installer dépendances Python

```bash
pip install python-dotenv
```

## 🚀 Quick Start

### 1. Enregistrer un bot

```python
from signal_client import SignalClient

# Créer le client
client = SignalClient(phone_number="+41791234567")

# Enregistrer le numéro
client.register()

# Vérifier avec le code SMS reçu
client.verify("123456")

# Configurer le profil
client.update_profile(name="Mon Bot", emoji="🤖")
```

### 2. Envoyer un message

```python
from signal_client import SignalClient

client = SignalClient(phone_number="+41791234567")

# Message simple
client.send_message(
    recipient="+41797654321",
    text="Hello! 👋"
)

# Message avec pièce jointe
from pathlib import Path
client.send_message(
    recipient="+41797654321",
    text="Voici une photo",
    attachments=[Path("./photo.jpg")]
)
```

### 3. Recevoir des messages

```python
from signal_client import SignalClient

client = SignalClient(phone_number="+41791234567")

# Recevoir nouveaux messages
messages = client.receive()

for message in messages:
    print(f"De: {message.sender.name}")
    print(f"Texte: {message.text}")
    
    # Télécharger pièces jointes
    for attachment in message.attachments:
        client.download_attachment(
            attachment,
            Path(f"./downloads/{attachment.filename}")
        )
```

### 4. Créer un bot simple

```python
from signal_client import SignalBot

bot = SignalBot(
    phone_number="+41791234567",
    group_filter="Mon Groupe"  # Optionnel
)

@bot.on_message
def handle_message(message):
    print(f"Message reçu: {message.text}")

@bot.on_attachment
def handle_attachment(message, attachment, file_path):
    print(f"Fichier reçu: {attachment.filename}")

# Lancer le bot (vérifie toutes les 30 secondes)
bot.run(interval=30)
```

## 📚 Exemples Complets

### Bot pour tickets de caisse

```python
from signal_client import SignalBot
from pathlib import Path
import json

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

@bot.on_attachment
def save_ticket(message, attachment, file_path):
    """Sauvegarde automatique des tickets"""
    
    # Identifier l'utilisateur
    user = FAMILY.get(message.sender.number, "Unknown")
    user_dir = TICKETS_DIR / user
    user_dir.mkdir(exist_ok=True)
    
    # Copier le fichier
    timestamp = message.timestamp.strftime('%Y%m%d_%H%M%S')
    ext = '.pdf' if attachment.is_pdf else '.jpg'
    dest = user_dir / f"{timestamp}{ext}"
    
    import shutil
    shutil.copy2(file_path, dest)
    
    # Sauvegarder metadata
    metadata = {
        'user': user,
        'timestamp': message.timestamp.isoformat(),
        'file_path': str(dest),
        'processed': False
    }
    
    with open(dest.with_suffix('.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Ticket de {user} sauvegardé")
    
    # Confirmer dans le groupe
    bot.client.send_to_group(
        group_id=message.group.id,
        text=f"✅ Ticket de {user} bien reçu!"
    )

# Lancer
print("🤖 Bot démarré")
bot.run(interval=30)
```

### Gestion des groupes

```python
from signal_client import SignalClient

client = SignalClient(phone_number="+41791234567")

# Lister tous les groupes
groups = client.list_groups()
for group in groups:
    print(f"📁 {group.name} - {group.id}")

# Trouver un groupe par nom
tickets_group = client.find_group_by_name("Tickets")

if tickets_group:
    # Envoyer message au groupe
    client.send_to_group(
        group_id=tickets_group.id,
        text="Hello groupe! 👋"
    )
```

## 🏗️ Architecture

```python
signal_client.py           # Client principal
├── SignalClient          # Client bas niveau
├── SignalBot             # Framework bot avec handlers
├── Message               # Représentation d'un message
├── Attachment            # Pièce jointe
├── Contact               # Contact Signal
└── Group                 # Groupe Signal
```

## 🔧 API Reference

### SignalClient

```python
class SignalClient:
    def __init__(phone_number: str, signal_cli_path: str = "signal-cli")
    
    # Enregistrement
    def register(captcha: Optional[str] = None) -> str
    def verify(code: str) -> str
    def update_profile(name: str = None, about: str = None, emoji: str = None)
    
    # Messages
    def send_message(recipient: str, text: str, attachments: List[Path] = None)
    def send_to_group(group_id: str, text: str, attachments: List[Path] = None)
    def receive(timeout: int = 5) -> List[Message]
    
    # Groupes
    def list_groups() -> List[Group]
    def find_group_by_name(name: str) -> Optional[Group]
    
    # Pièces jointes
    def download_attachment(attachment: Attachment, output_path: Path) -> Path
    
    # Daemon
    def daemon_start() -> subprocess.Popen
```

### SignalBot

```python
class SignalBot:
    def __init__(phone_number: str, group_filter: Optional[str] = None)
    
    # Décorateurs
    @bot.on_message
    def handler(message: Message) -> None
    
    @bot.on_attachment
    def handler(message: Message, attachment: Attachment, file_path: Path) -> None
    
    # Lancement
    def run(interval: int = 30, max_messages: Optional[int] = None)
```

### Message

```python
@dataclass
class Message:
    sender: Contact
    timestamp: datetime
    text: Optional[str]
    attachments: List[Attachment]
    group: Optional[Group]
    is_group_message: bool
    
    # Properties
    @property
    def has_attachments() -> bool
    
    @property
    def message_type() -> MessageType  # TEXT, IMAGE, DOCUMENT, VIDEO
```

### Attachment

```python
@dataclass
class Attachment:
    id: str
    content_type: str
    filename: str
    size: int
    
    # Properties
    @property
    def is_image() -> bool
    
    @property
    def is_pdf() -> bool
    
    @property
    def is_video() -> bool
```

## 🧪 Tests

```bash
# Installer pytest
pip install pytest

# Lancer les tests
python -m pytest test_signal_client.py -v

# Tests avec coverage
pip install pytest-cov
python -m pytest test_signal_client.py --cov=signal_client --cov-report=html
```

## 🐛 Troubleshooting

### "signal-cli not found"

```bash
# Vérifier installation
which signal-cli
signal-cli --version

# Si pas installé
brew install signal-cli  # macOS
```

### "Invalid phone number"

Utiliser le format international complet:
- ✅ `+41791234567`
- ❌ `0791234567`
- ❌ `+41 79 123 45 67`

### Le bot ne reçoit pas les messages

```bash
# Vérifier que le bot est dans le groupe
signal-cli -a +41791234567 listGroups -d

# Tester réception manuelle
signal-cli -a +41791234567 receive
```

### Les pièces jointes ne se téléchargent pas

```bash
# Vérifier permissions
ls -la ~/.local/share/signal-cli/attachments/

# Donner permissions
chmod -R 755 ~/.local/share/signal-cli/
```

## 📖 Documentation signal-cli

- [GitHub signal-cli](https://github.com/AsamK/signal-cli)
- [Wiki signal-cli](https://github.com/AsamK/signal-cli/wiki)
- [Signal Protocol](https://signal.org/docs/)

## 🔒 Sécurité

- ✅ Chiffrement E2EE natif de Signal
- ✅ Pas de stockage cloud des messages
- ✅ Clés locales uniquement
- ⚠️ Protéger le fichier .env avec les credentials

## 📝 License

MIT License - Libre d'utilisation

## 🤝 Contribution

Contributions bienvenues! 

1. Fork le repo
2. Créer une branche (`git checkout -b feature/amazing`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Ouvrir une Pull Request

## 💬 Support

- 📧 Email: [ton email]
- 🐛 Issues: [GitHub Issues]
- 💡 Discussions: [GitHub Discussions]

## 🎯 Roadmap

- [ ] Support des réactions
- [ ] Support des stories
- [ ] Support des appels (voice/video)
- [ ] Interface web pour monitoring
- [ ] Docker container
- [ ] CI/CD avec GitHub Actions

## ⭐ Remerciements

- [AsamK/signal-cli](https://github.com/AsamK/signal-cli) - L'excellent CLI Signal
- [Signal Foundation](https://signal.org) - Pour le protocole E2EE

---

Made with ❤️ pour la privacy et l'automation