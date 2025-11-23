"""
Tests unitaires pour le Signal Client Python

Run avec: python -m pytest test_signal_client.py -v
"""

import pytest
from pathlib import Path
from datetime import datetime
from signal_client import (
    SignalClient, SignalBot, Message, Attachment, Contact, Group,
    MessageType, SignalException, SignalCLINotFound
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_phone():
    """Numéro de téléphone de test"""
    return "+41791234567"


@pytest.fixture
def mock_attachment():
    """Pièce jointe de test"""
    return Attachment(
        id="abc123",
        content_type="image/jpeg",
        filename="ticket.jpg",
        size=12345
    )


@pytest.fixture
def mock_contact():
    """Contact de test"""
    return Contact(
        number="+41797654321",
        name="Test User",
        uuid="uuid-123"
    )


@pytest.fixture
def mock_group():
    """Groupe de test"""
    return Group(
        id="group-abc",
        name="Tickets 🧾",
        members=[],
        admins=[]
    )


@pytest.fixture
def mock_message(mock_contact):
    """Message de test"""
    return Message(
        sender=mock_contact,
        timestamp=datetime.now(),
        text="Hello World",
        attachments=[],
        is_group_message=False
    )


# =============================================================================
# Tests Attachment
# =============================================================================

def test_attachment_is_image():
    """Test détection type image"""
    att = Attachment(
        id="1",
        content_type="image/jpeg",
        filename="photo.jpg",
        size=100
    )
    assert att.is_image is True
    assert att.is_pdf is False


def test_attachment_is_pdf():
    """Test détection type PDF"""
    att = Attachment(
        id="1",
        content_type="application/pdf",
        filename="document.pdf",
        size=100
    )
    assert att.is_pdf is True
    assert att.is_image is False


def test_attachment_pdf_by_filename():
    """Test détection PDF par nom de fichier"""
    att = Attachment(
        id="1",
        content_type="application/octet-stream",
        filename="ticket.pdf",
        size=100
    )
    assert att.is_pdf is True


# =============================================================================
# Tests Contact
# =============================================================================

def test_contact_str_with_name():
    """Test string representation avec nom"""
    contact = Contact(number="+41791234567", name="John Doe")
    assert str(contact) == "John Doe"


def test_contact_str_without_name():
    """Test string representation sans nom"""
    contact = Contact(number="+41791234567")
    assert str(contact) == "+41791234567"


# =============================================================================
# Tests Group
# =============================================================================

def test_group_str():
    """Test string representation de groupe"""
    group = Group(
        id="abc",
        name="Test Group",
        members=[Contact(number="+1"), Contact(number="+2")],
        admins=[]
    )
    assert str(group) == "Test Group (2 members)"


# =============================================================================
# Tests Message
# =============================================================================

def test_message_has_attachments(mock_contact, mock_attachment):
    """Test détection pièces jointes"""
    msg = Message(
        sender=mock_contact,
        timestamp=datetime.now(),
        attachments=[mock_attachment]
    )
    assert msg.has_attachments is True


def test_message_no_attachments(mock_contact):
    """Test message sans pièces jointes"""
    msg = Message(
        sender=mock_contact,
        timestamp=datetime.now(),
        text="Hello"
    )
    assert msg.has_attachments is False


def test_message_type_text(mock_contact):
    """Test type de message texte"""
    msg = Message(
        sender=mock_contact,
        timestamp=datetime.now(),
        text="Hello"
    )
    assert msg.message_type == MessageType.TEXT


def test_message_type_image(mock_contact):
    """Test type de message image"""
    att = Attachment(
        id="1",
        content_type="image/jpeg",
        filename="photo.jpg",
        size=100
    )
    msg = Message(
        sender=mock_contact,
        timestamp=datetime.now(),
        attachments=[att]
    )
    assert msg.message_type == MessageType.IMAGE


def test_message_type_document(mock_contact):
    """Test type de message document"""
    att = Attachment(
        id="1",
        content_type="application/pdf",
        filename="doc.pdf",
        size=100
    )
    msg = Message(
        sender=mock_contact,
        timestamp=datetime.now(),
        attachments=[att]
    )
    assert msg.message_type == MessageType.DOCUMENT


# =============================================================================
# Tests SignalClient (nécessite signal-cli installé)
# =============================================================================

@pytest.mark.skipif(
    True,  # Skip par défaut, activer seulement si signal-cli installé
    reason="Nécessite signal-cli installé"
)
def test_signal_client_init(mock_phone):
    """Test initialisation du client"""
    client = SignalClient(phone_number=mock_phone)
    assert client.phone_number == mock_phone


@pytest.mark.skipif(True, reason="Nécessite signal-cli")
def test_signal_client_check_cli(mock_phone):
    """Test vérification signal-cli"""
    client = SignalClient(phone_number=mock_phone)
    assert client._check_signal_cli() is True


# =============================================================================
# Tests SignalBot
# =============================================================================

def test_signal_bot_should_process_new_message(mock_phone, mock_message):
    """Test qu'un nouveau message doit être traité"""
    bot = SignalBot(phone_number=mock_phone)
    assert bot._should_process(mock_message) is True


def test_signal_bot_should_not_process_duplicate(mock_phone, mock_message):
    """Test qu'un message en double n'est pas traité"""
    bot = SignalBot(phone_number=mock_phone)
    
    # Premier passage
    assert bot._should_process(mock_message) is True
    
    # Deuxième passage (duplicata)
    assert bot._should_process(mock_message) is False


def test_signal_bot_decorator_on_message(mock_phone):
    """Test décorateur on_message"""
    bot = SignalBot(phone_number=mock_phone)
    
    @bot.on_message
    def handler(msg):
        pass
    
    assert len(bot.message_handlers) == 1
    assert bot.message_handlers[0] == handler


def test_signal_bot_decorator_on_attachment(mock_phone):
    """Test décorateur on_attachment"""
    bot = SignalBot(phone_number=mock_phone)
    
    @bot.on_attachment
    def handler(msg, att, path):
        pass
    
    assert len(bot.attachment_handlers) == 1
    assert bot.attachment_handlers[0] == handler


# =============================================================================
# Tests d'intégration (nécessitent signal-cli et un compte configuré)
# =============================================================================

@pytest.mark.integration
@pytest.mark.skipif(True, reason="Tests d'intégration - activer manuellement")
class TestIntegration:
    """Tests d'intégration avec signal-cli réel"""
    
    def test_send_receive_message(self):
        """Test envoi/réception de message"""
        client = SignalClient(phone_number="+41791234567")
        
        # Envoyer
        client.send_message(
            recipient="+41797654321",
            text="Test message"
        )
        
        # Recevoir
        messages = client.receive()
        assert isinstance(messages, list)
    
    def test_list_groups(self):
        """Test listage des groupes"""
        client = SignalClient(phone_number="+41791234567")
        groups = client.list_groups()
        assert isinstance(groups, list)
    
    def test_find_group(self):
        """Test recherche de groupe"""
        client = SignalClient(phone_number="+41791234567")
        group = client.find_group_by_name("Tickets")
        assert group is None or isinstance(group, Group)


# =============================================================================
# Tests de parsing de JSON signal-cli
# =============================================================================

def test_parse_message_json():
    """Test parsing d'un message JSON signal-cli"""
    client = SignalClient(phone_number="+41791234567")
    
    # Exemple de JSON signal-cli
    json_data = {
        "envelope": {
            "source": "+41797654321",
            "sourceName": "Test User",
            "sourceUuid": "uuid-123",
            "timestamp": 1700000000000,
            "dataMessage": {
                "message": "Hello World",
                "attachments": [
                    {
                        "id": "att-123",
                        "contentType": "image/jpeg",
                        "filename": "photo.jpg",
                        "size": 12345
                    }
                ]
            }
        }
    }
    
    message = client._parse_message(json_data)
    
    assert message is not None
    assert message.sender.number == "+41797654321"
    assert message.sender.name == "Test User"
    assert message.text == "Hello World"
    assert len(message.attachments) == 1
    assert message.attachments[0].filename == "photo.jpg"


def test_parse_group_message_json():
    """Test parsing d'un message de groupe"""
    client = SignalClient(phone_number="+41791234567")
    
    json_data = {
        "envelope": {
            "source": "+41797654321",
            "timestamp": 1700000000000,
            "dataMessage": {
                "message": "Hello Group",
                "groupInfo": {
                    "groupId": "group-abc",
                    "name": "Test Group"
                }
            }
        }
    }
    
    message = client._parse_message(json_data)
    
    assert message is not None
    assert message.is_group_message is True
    assert message.group is not None
    assert message.group.name == "Test Group"


def test_parse_message_without_data():
    """Test parsing message sans dataMessage (à ignorer)"""
    client = SignalClient(phone_number="+41791234567")
    
    json_data = {
        "envelope": {
            "source": "+41797654321",
            "timestamp": 1700000000000,
            "receiptMessage": {}  # Pas un dataMessage
        }
    }
    
    message = client._parse_message(json_data)
    assert message is None


# =============================================================================
# Tests d'erreur
# =============================================================================

def test_signal_cli_not_found():
    """Test erreur si signal-cli introuvable"""
    with pytest.raises(SignalCLINotFound):
        SignalClient(
            phone_number="+41791234567",
            signal_cli_path="/path/invalid/signal-cli"
        )


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])