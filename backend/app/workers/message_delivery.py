import time
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import redis
import json

from app.core.database import SessionLocal
from app.models.database import Message, Agent, MessageStatus, AgentStatus
from app.workers.webhook_caller import call_webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageDeliveryWorker:
    def __init__(self, poll_interval: int = 5):
        """
        poll_interval: seconds between polling for queued messages
        """
        self.poll_interval = poll_interval
        self.max_retries = 5
        self.retry_delays = [60, 300, 900, 3600, 21600]  # 1min, 5min, 15min, 1hr, 6hr

        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe('agent_status_change')
            logger.info("Connected to Redis for instant waitlist processing")
        except:
            logger.warning("Redis not available, using polling only")
            self.redis_client = None

        
    def should_retry_message(self, message: Message) -> bool:
        """Check if message should be retried based on retry count and delay"""
        if message.retry_count >= self.max_retries:
            return False
        
        if message.retry_count == 0:
            return True
        
        # Calculate when next retry should happen
        delay_seconds = self.retry_delays[message.retry_count - 1]
        last_attempt = message.last_retry_at or message.created_at
        next_retry_time = last_attempt + timedelta(seconds=delay_seconds)
        
        return datetime.now(timezone.utc) >= next_retry_time
    
    def process_queued_messages(self, db: Session):
        """Process all queued messages"""
        messages = db.query(Message).filter(
            Message.status == MessageStatus.QUEUED
        ).all()
        
        for message in messages:
            if not self.should_retry_message(message):
                continue
            
            # Get recipient agent
            recipient = db.query(Agent).filter(Agent.id == message.to_agent_id).first()
            
            if not recipient:
                logger.error(f"Recipient agent {message.to_agent_id} not found for message {message.id}")
                message.status = MessageStatus.FAILED
                message.error_message = "Recipient agent not found"
                db.commit()
                continue
            
            # Check if recipient is online
            if recipient.status != AgentStatus.ONLINE:
                logger.info(f"Recipient {recipient.id} is {recipient.status}, keeping message {message.id} queued")
                continue
            
            # Attempt delivery
            logger.info(f"Attempting delivery of message {message.id} (attempt {message.retry_count + 1})")
            success, error_msg = call_webhook(message, recipient, db)
            
            if success:
                logger.info(f"Successfully delivered message {message.id}")
            else:
                message.retry_count += 1
                message.last_retry_at = datetime.now(timezone.utc)
                
                if message.retry_count >= self.max_retries:
                    message.status = MessageStatus.FAILED
                    message.error_message = f"Max retries exceeded. Last error: {error_msg}"
                    logger.error(f"Message {message.id} failed after {self.max_retries} attempts")
                else:
                    message.error_message = error_msg
                    next_retry = self.retry_delays[message.retry_count - 1]
                    logger.warning(f"Message {message.id} delivery failed: {error_msg}. Will retry in {next_retry}s")
                
                db.commit()
    
    def run(self):
        """Main worker loop"""
        logger.info(f"Message delivery worker started (polling every {self.poll_interval}s)")
        
        while True:
            try:
                db = SessionLocal()
                
                # Process queued messages
                self.process_queued_messages(db)
                
                # Listen for status change notifications
                if self.redis_client:
                    message = self.pubsub.get_message(timeout=self.poll_interval)
                    if message and message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            if data.get('status') == 'online':
                                agent_id = data.get('agent_id')
                                logger.info(f"Received status change notification for {agent_id}")
                                self.process_status_change_to_online(agent_id, db)
                        except:
                            pass
                else:
                    time.sleep(self.poll_interval)
                
                db.close()
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)

    def process_status_change_to_online(self, agent_id: str, db: Session):
        """Process queued messages when an agent comes online"""
        messages = db.query(Message).filter(
            Message.to_agent_id == agent_id,
            Message.status == MessageStatus.QUEUED
        ).all()
        
        if not messages:
            return
        
        logger.info(f"Agent {agent_id} came online, processing {len(messages)} queued messages")
        
        recipient = db.query(Agent).filter(Agent.id == agent_id).first()
        if not recipient:
            return
        
        for message in messages:
            # Force immediate delivery attempt by resetting retry time
            message.last_retry_at = None
            db.commit()
            
            logger.info(f"Triggering immediate delivery of message {message.id}")
            success, error_msg = call_webhook(message, recipient, db)
            
            if not success:
                message.retry_count += 1
                message.last_retry_at = datetime.now(timezone.utc)
                message.error_message = error_msg
                db.commit()


if __name__ == "__main__":
    worker = MessageDeliveryWorker(poll_interval=5)
    worker.run()