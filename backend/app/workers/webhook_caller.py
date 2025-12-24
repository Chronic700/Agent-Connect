import json
import requests
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.database import Message, Agent, MessageStatus
from app.core.security import generate_webhook_signature


def call_webhook(message: Message, recipient: Agent, db: Session) -> Tuple[bool, Optional[str]]:
    """
    Call recipient's webhook with message.
    Returns (success: bool, error_message: Optional[str])
    """
    payload = {
        "message_id": message.id,
        "from_agent_id": message.from_agent_id,
        "to_agent_id": message.to_agent_id,
        "message_content": json.loads(message.message_content),
        "timestamp": message.created_at.isoformat()
    }
    
    payload_str = json.dumps(payload)
    signature = generate_webhook_signature(payload_str, recipient.secret_token)
    
    headers = {
        "Content-Type": "application/json",
        "X-Signature": f"sha256={signature}",
        "User-Agent": "AgentConnect/1.0"
    }
    
    try:
        response = requests.post(
            recipient.webhook_url,
            data=payload_str,
            headers=headers,
            timeout=30
        )
        
        if 200 <= response.status_code < 300:
            message.status = MessageStatus.DELIVERED
            message.delivered_at = datetime.utcnow()
            message.error_message = None
            db.commit()
            return True, None
        
        elif 400 <= response.status_code < 500:
            error_msg = f"Webhook returned {response.status_code}: {response.text[:200]}"
            message.status = MessageStatus.FAILED
            message.error_message = error_msg
            db.commit()
            return False, error_msg
        
        else:
            error_msg = f"Webhook returned {response.status_code}: {response.text[:200]}"
            return False, error_msg
    
    except requests.exceptions.Timeout:
        return False, "Webhook request timed out"
    
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to webhook URL"
    
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"