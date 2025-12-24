from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum

from app.core.database import Base

class AgentStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    # PAUSED = "paused"

class MessageStatus(str, Enum):
    QUEUED = "queued"
    DELIVERED = "delivered"
    FAILED = "failed"

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    webhook_url = Column(String, nullable=False)
    api_key_hash = Column(String, nullable=False)
    secret_token = Column(String, nullable=False)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.OFFLINE, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)
    from_agent_id = Column(String, nullable=False)
    to_agent_id = Column(String, nullable=False)
    message_content = Column(String, nullable=False)  # JSON string
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.QUEUED, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    last_retry_at = Column(DateTime, nullable=True)