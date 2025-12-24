from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import json
import redis

from app.core.database import engine, get_db, Base
from app.models.database import Agent, Message, AgentStatus, MessageStatus
from app.core.security import (
    generate_id,
    generate_api_key,
    generate_secret_token,
    generate_message_id,
    hash_api_key,
    get_current_agent
)

Base.metadata.create_all(bind=engine)

# Pydantic Models
class AgentRegisterRequest(BaseModel):
    name: str
    description: str
    webhook_url: HttpUrl

class AgentRegisterResponse(BaseModel):
    agent_id: str
    api_key: str
    secret_token: str

class AgentPublicInfo(BaseModel):
    agent_id: str
    name: str
    description: str
    status: AgentStatus
    created_at: datetime

class AgentListResponse(BaseModel):
    agents: List[AgentPublicInfo]
    total: int

class AgentStatusUpdateRequest(BaseModel):
    status: AgentStatus

class SendMessageRequest(BaseModel):
    to_agent_id: str
    message_content: dict

class SendMessageResponse(BaseModel):
    message_id: str
    status: MessageStatus

class MessageStatusResponse(BaseModel):
    message_id: str
    from_agent_id: str
    to_agent_id: str
    status: MessageStatus
    retry_count: int
    created_at: datetime
    delivered_at: Optional[datetime]
    error_message: Optional[str]

# FastAPI app
app = FastAPI(title="Agent Connect API")

try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()
    print("Connected to Redis")
except:
    redis_client = None
    print("Redis not available, waitlist processing will use polling only")

# Endpoints
@app.post("/api/agents/register", response_model=AgentRegisterResponse)
def register_agent(request: AgentRegisterRequest, db: Session = Depends(get_db)):
    agent_id = generate_id()
    api_key = generate_api_key()
    secret_token = generate_secret_token()
    
    agent = Agent(
        id=agent_id,
        name=request.name,
        description=request.description,
        webhook_url=str(request.webhook_url),
        api_key_hash=hash_api_key(api_key),
        secret_token=secret_token,
        status=AgentStatus.OFFLINE
    )
    
    db.add(agent)
    db.commit()
    
    return AgentRegisterResponse(
        agent_id=agent_id,
        api_key=api_key,
        secret_token=secret_token
    )

@app.get("/api/agents/{agent_id}", response_model=AgentPublicInfo)
def get_agent_info(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentPublicInfo(
        agent_id=agent.id,
        name=agent.name,
        description=agent.description,
        status=agent.status,
        created_at=agent.created_at
    )

@app.get("/api/agents", response_model=AgentListResponse)
def list_agents(
    status: Optional[AgentStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Agent)
    
    if status:
        query = query.filter(Agent.status == status)
    
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    
    return AgentListResponse(
        agents=[
            AgentPublicInfo(
                agent_id=agent.id,
                name=agent.name,
                description=agent.description,
                status=agent.status,
                created_at=agent.created_at
            )
            for agent in agents
        ],
        total=total
    )

@app.put("/api/agents/{agent_id}/status")
def update_agent_status(
    agent_id: str,
    request: AgentStatusUpdateRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    if current_agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Can only update your own status")
    
    old_status = current_agent.status
    current_agent.status = request.status
    current_agent.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    # If agent just came online, notify worker to process waitlist
    if old_status != AgentStatus.ONLINE and request.status == AgentStatus.ONLINE:
        if redis_client:
            try:
                redis_client.publish('agent_status_change', json.dumps({
                    'agent_id': agent_id,
                    'status': 'online'
                }))
            except:
                pass
    
    return {"agent_id": agent_id, "status": request.status}

@app.post("/api/messages/send", response_model=SendMessageResponse)
def send_message(
    request: SendMessageRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    # Verify recipient exists
    recipient = db.query(Agent).filter(Agent.id == request.to_agent_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient agent not found")
    
    message_id = generate_message_id()
    
    message = Message(
        id=message_id,
        from_agent_id=current_agent.id,
        to_agent_id=request.to_agent_id,
        message_content=json.dumps(request.message_content),
        status=MessageStatus.QUEUED
    )
    
    db.add(message)
    db.commit()
    
    # TODO: Trigger background worker to deliver message
    
    return SendMessageResponse(
        message_id=message_id,
        status=MessageStatus.QUEUED
    )

@app.get("/api/messages/{message_id}", response_model=MessageStatusResponse)
def get_message_status(
    message_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only sender or recipient can view message
    if message.from_agent_id != current_agent.id and message.to_agent_id != current_agent.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this message")
    
    return MessageStatusResponse(
        message_id=message.id,
        from_agent_id=message.from_agent_id,
        to_agent_id=message.to_agent_id,
        status=message.status,
        retry_count=message.retry_count,
        created_at=message.created_at,
        delivered_at=message.delivered_at,
        error_message=message.error_message
    )