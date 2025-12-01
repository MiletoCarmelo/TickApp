# tickapp/sensors/signal.py
"""
Sensor Dagster pour détecter les nouveaux messages Signal et déclencher le pipeline
"""
from dagster import sensor, SensorEvaluationContext, RunRequest, SkipReason
from typing import List, Optional
import os
from datetime import datetime
from dotenv import load_dotenv

from tickapp.clients.signal_client import SignalClient, Message
from tickapp.clients.database_client import DatabaseClient

load_dotenv()


def is_within_schedule() -> bool:
    """
    Vérifie si on est dans les heures d'exécution autorisées
    
    Planning :
    - Lundi à samedi : 8h à 18h
    - Jeudi : 8h à 20h
    - Dimanche : pas d'exécution
    
    Returns:
        True si on est dans les heures autorisées, False sinon
    """
    now = datetime.now()
    weekday = now.weekday()  # 0 = lundi, 6 = dimanche
    hour = now.hour
    
    # Dimanche : pas d'exécution
    if weekday == 6:
        return False
    
    # Jeudi (3) : 8h à 20h
    if weekday == 3:
        return 8 <= hour < 20
    
    # Lundi à samedi (sauf jeudi) : 8h à 18h
    # weekday 0-2 (lundi-mercredi) et 4-5 (vendredi-samedi)
    return 8 <= hour < 18


def get_new_messages(context: SensorEvaluationContext) -> List[tuple]:
    """
    Récupère les nouveaux messages Signal non encore traités
    
    Returns:
        Liste de tuples (Message, JSON brut) pour chaque nouveau message
    """
    phone_number = os.getenv("SIGNAL_PHONE_NUMBER")
    if not phone_number:
        context.log.error("SIGNAL_PHONE_NUMBER non défini")
        return []
    
    client = SignalClient(phone_number=phone_number)
    
    # Recevoir les messages récents
    raw_messages = client.receive(number_of_messages=10)  # Limiter pour éviter de surcharger
    if not raw_messages:
        return []
    
    # Parser les messages ET garder le JSON brut pour chaque message
    # On parse ligne par ligne pour faire correspondre Message -> JSON brut
    import json
    raw_json_lines = [line.strip() for line in raw_messages.strip().split('\n') if line.strip()]
    parsed_messages = client._parse_message(raw_messages)
    
    # Créer un mapping (timestamp_ms, sender_uuid) -> JSON brut
    # Note: On utilise le timestamp + sender_uuid comme clé car Message n'est pas hashable
    message_json_map = {}
    for line in raw_json_lines:
        try:
            msg_json = json.loads(line)
            envelope = msg_json.get('envelope', {})
            timestamp_ms = envelope.get('timestamp', 0)
            source_uuid = envelope.get('sourceUuid') or envelope.get('source')
            # Utiliser (timestamp_ms, sender_uuid) comme clé
            key = (timestamp_ms, str(source_uuid) if source_uuid else None)
            message_json_map[key] = msg_json
        except (json.JSONDecodeError, KeyError):
            continue
    
    # Télécharger les attachments
    messages_with_attachments = client.download_attachment(
        phone_number=client.phone_number,
        messages=parsed_messages
    )
    
    # Filtrer les messages avec attachments (images de tickets)
    messages_with_images = [
        msg for msg in messages_with_attachments 
        if msg.has_attachments and any(
            att.content_type and att.content_type.startswith("image/") 
            for att in msg.attachments
        )
    ]
    
    # Vérifier quels messages sont déjà en base de données
    db_client = DatabaseClient(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5434")),
        database=os.getenv("DB_NAME", "receipt_processing"),
        user=os.getenv("DB_USER", "receipt_user"),
        password=os.getenv("DB_PASSWORD", "SuperSecretPassword123!")
    )
    
    # Helper function pour connexion avec retry
    def get_db_connection(max_retries=3, retry_delay=1.0):
        import psycopg2
        import time
        last_error = None
        conn_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5434")),
            "database": os.getenv("DB_NAME", "receipt_processing"),
            "user": os.getenv("DB_USER", "receipt_user"),
            "password": os.getenv("DB_PASSWORD", "SuperSecretPassword123!"),
            "connect_timeout": 10
        }
        for attempt in range(max_retries):
            try:
                return psycopg2.connect(**conn_params)
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise
        raise last_error
    
    # Retourner une liste de tuples (Message, JSON brut)
    new_messages = []
    for message in messages_with_images:
        # Vérifier si le message existe déjà en base
        try:
            import psycopg2
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM signal_message m
                JOIN signal_sender s ON m.sender_id = s.sender_id
                WHERE m.timestamp = %s 
                AND s.signal_uuid = %s
            """, (message.timestamp, str(message.sender.uuid) if message.sender.uuid else None))
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            if count == 0:
                # Récupérer le JSON brut correspondant en utilisant la clé (timestamp_ms, sender_uuid)
                timestamp_ms = int(message.timestamp.timestamp() * 1000)
                sender_uuid = str(message.sender.uuid) if message.sender.uuid else None
                key = (timestamp_ms, sender_uuid)
                message_json = message_json_map.get(key, {})
                new_messages.append((message, message_json))
        except Exception as e:
            context.log.warning(f"Erreur lors de la vérification du message: {e}")
            # En cas d'erreur, considérer comme nouveau pour éviter de perdre des messages
            timestamp_ms = int(message.timestamp.timestamp() * 1000)
            sender_uuid = str(message.sender.uuid) if message.sender.uuid else None
            key = (timestamp_ms, sender_uuid)
            message_json = message_json_map.get(key, {})
            new_messages.append((message, message_json))
    
    return new_messages


@sensor(
    name="signal_message_sensor",
    job_name="process_signal_message",
    minimum_interval_seconds=1200  # Vérifier toutes les 20 minutes (20 * 60 = 1200 secondes)
)
def signal_message_sensor(context: SensorEvaluationContext):
    """
    Sensor qui détecte les nouveaux messages Signal avec images de tickets
    et déclenche un pipeline pour chaque nouveau message
    
    Planning d'exécution :
    - Lundi à samedi : 8h à 18h
    - Jeudi : 8h à 20h
    - Dimanche : pas d'exécution
    """
    # Vérifier si on est dans les heures autorisées
    if not is_within_schedule():
        now = datetime.now()
        weekday_name = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"][now.weekday()]
        return SkipReason(
            f"⏰ Hors des heures d'exécution ({weekday_name} {now.hour:02d}h) - "
            f"Planning: Lun-Sam 8h-18h, Jeudi 8h-20h, Dimanche fermé"
        )
    
    context.log.info("🔍 Vérification des nouveaux messages Signal...")
    
    new_messages = get_new_messages(context)
    
    if not new_messages:
        return SkipReason("Aucun nouveau message avec image de ticket trouvé")
    
    context.log.info(f"📨 {len(new_messages)} nouveau(x) message(s) détecté(s)")
    
    # Créer un RunRequest pour chaque nouveau message
    import json
    run_requests = []
    for message, message_json in new_messages:
        # Créer un identifiant unique pour ce message (basé sur timestamp + sender)
        message_id = f"{message.timestamp.isoformat()}_{message.sender.uuid or message.sender.number or 'unknown'}"
        
        # Récupérer le groupe si disponible
        group_id = None
        group_name = None
        if message.group:
            group_id = message.group.id
            group_name = message.group.name
        
        # Sérialiser les chemins des attachments (le message a déjà été téléchargé par le sensor)
        attachment_paths = []
        if message.attachments:
            for att in message.attachments:
                if att.path:
                    attachment_paths.append({
                        "path": str(att.path),
                        "content_type": att.content_type,
                        "filename": att.filename,
                        "id": att.id
                    })
        
        run_requests.append(
            RunRequest(
                run_key=f"signal_message_{message_id}",
                run_config={
                    "ops": {
                        "message_from_signal": {
                            "config": {
                                "message_timestamp": message.timestamp.isoformat(),
                                "sender_uuid": str(message.sender.uuid) if message.sender.uuid else None,
                                "sender_number": message.sender.number or None,
                            }
                        }
                    }
                },
                job_name="process_signal_message",
                tags={
                    # Tags essentiels pour retrouver le message
                    "message_timestamp": message.timestamp.isoformat(),
                    "sender_uuid": str(message.sender.uuid) if message.sender.uuid else "",
                    "sender_number": message.sender.number or "",
                    "sender_name": message.sender.name or "",
                    # Tags pour les notifications
                    "group_id": group_id or "",
                    "group_name": group_name or "",
                    # Tags pour les attachments
                    "attachment_paths": json.dumps(attachment_paths),
                    # Tags optionnels pour les logs
                    "message_text": message.text or "",
                    "is_group_message": str(message.is_group_message),
                }
            )
        )
    
    return run_requests


@sensor(
    name="signal_message_sensor_test",
    job_name="process_signal_message",
    minimum_interval_seconds=60  # Vérifier toutes les minutes pour les tests
)
def signal_message_sensor_test(context: SensorEvaluationContext):
    """
    Sensor de TEST qui détecte les nouveaux messages Signal avec images de tickets
    et déclenche un pipeline pour chaque nouveau message
    
    ⚠️  VERSION DE TEST : Fonctionne à tout moment, sans restrictions horaires
    Utilisez ce sensor pour tester le pipeline sans attendre les heures autorisées.
    
    Différences avec le sensor officiel :
    - Pas de vérification des heures (is_within_schedule)
    - Intervalle plus court (1 minute au lieu de 20 minutes)
    """
    context.log.info("🧪 [TEST] Vérification des nouveaux messages Signal...")
    
    new_messages = get_new_messages(context)
    
    if not new_messages:
        return SkipReason("🧪 [TEST] Aucun nouveau message avec image de ticket trouvé")
    
    context.log.info(f"🧪 [TEST] {len(new_messages)} nouveau(x) message(s) détecté(s)")
    
    # Créer un RunRequest pour chaque nouveau message
    import json
    run_requests = []
    for message, message_json in new_messages:
        # Créer un identifiant unique pour ce message (basé sur timestamp + sender)
        message_id = f"{message.timestamp.isoformat()}_{message.sender.uuid or message.sender.number or 'unknown'}"
        
        # Récupérer le groupe si disponible
        group_id = None
        group_name = None
        if message.group:
            group_id = message.group.id
            group_name = message.group.name
        
        # Sérialiser les chemins des attachments (le message a déjà été téléchargé par le sensor)
        attachment_paths = []
        if message.attachments:
            for att in message.attachments:
                if att.path:
                    attachment_paths.append({
                        "path": str(att.path),
                        "content_type": att.content_type,
                        "filename": att.filename,
                        "id": att.id
                    })
        
        run_requests.append(
            RunRequest(
                run_key=f"signal_message_test_{message_id}",
                run_config={
                    "ops": {
                        "message_from_signal": {
                            "config": {
                                "message_timestamp": message.timestamp.isoformat(),
                                "sender_uuid": str(message.sender.uuid) if message.sender.uuid else None,
                                "sender_number": message.sender.number or None,
                            }
                        }
                    }
                },
                job_name="process_signal_message",
                tags={
                    # Tags essentiels pour retrouver le message
                    "message_timestamp": message.timestamp.isoformat(),
                    "sender_uuid": str(message.sender.uuid) if message.sender.uuid else "",
                    "sender_number": message.sender.number or "",
                    "sender_name": message.sender.name or "",
                    # Tags pour les notifications
                    "group_id": group_id or "",
                    "group_name": group_name or "",
                    # Tags pour les attachments
                    "attachment_paths": json.dumps(attachment_paths),
                    # Tags optionnels pour les logs
                    "message_text": message.text or "",
                    "is_group_message": str(message.is_group_message),
                    "test_mode": "true",  # Tag pour identifier les runs de test
                }
            )
        )
    
    return run_requests

