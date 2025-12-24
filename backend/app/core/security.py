import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional
from collections import defaultdict
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.database import Agent

security = HTTPBearer()

# In-memory rate limiting (use Redis for production)
rate_limit_store = defaultdict(list)


def generate_id() -> str:
    """Generate agent ID"""
    return f"agent_{secrets.token_urlsafe(16)}"


def generate_api_key() -> str:
    """Generate API key"""
    return f"ak_{secrets.token_urlsafe(32)}"


def generate_secret_token() -> str:
    """Generate secret token for webhook verification"""
    return secrets.token_urlsafe(32)


def generate_message_id() -> str:
    """Generate message ID"""
    return f"msg_{secrets.token_urlsafe(16)}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, db: Session) -> Optional[Agent]:
    """Verify API key and return agent"""
    api_key_hash = hash_api_key(api_key)
    return db.query(Agent).filter(Agent.api_key_hash == api_key_hash).first()


def generate_webhook_signature(payload: str, secret_token: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload"""
    return hmac.new(
        secret_token.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_webhook_signature(payload: str, signature: str, secret_token: str) -> bool:
    """Verify webhook signature"""
    expected_signature = f"sha256={generate_webhook_signature(payload, secret_token)}"
    return hmac.compare_digest(signature, expected_signature)


def check_rate_limit(api_key: str, limit: int = 100, window_seconds: int = 3600) -> bool:
    """
    Check if API key has exceeded rate limit.
    limit: max requests allowed
    window_seconds: time window in seconds (default 1 hour)
    Returns True if within limit, False if exceeded
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=window_seconds)
    
    # Clean old requests
    rate_limit_store[api_key] = [
        timestamp for timestamp in rate_limit_store[api_key]
        if timestamp > cutoff
    ]
    
    # Check limit
    if len(rate_limit_store[api_key]) >= limit:
        return False
    
    # Add current request
    rate_limit_store[api_key].append(now)
    return True


def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Agent:
    """
    Dependency to get current authenticated agent.
    Verifies API key and applies rate limiting.
    """
    api_key = credentials.credentials
    
    # Verify API key
    agent = verify_api_key(api_key, db)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check rate limit
    if not check_rate_limit(api_key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 100 requests per hour.",
            headers={"Retry-After": "3600"}
        )
    
    return agent