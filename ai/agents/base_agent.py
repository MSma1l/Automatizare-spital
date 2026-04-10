import logging
from datetime import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all AI agents."""

    name: str = "base_agent"
    description: str = "Base agent"

    def __init__(self, db: Session = None):
        self.db = db

    def run(self) -> dict:
        """Execute the agent's main logic. Override in subclasses."""
        raise NotImplementedError

    def log_action(self, action: str, data: dict = None):
        """Log agent action to database."""
        if not self.db:
            logger.info(f"[{self.name}] {action}")
            return
        from models.db import AgentLog
        log = AgentLog(
            agent_name=self.name,
            action=action,
            data=data,
            created_at=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.commit()
        logger.info(f"[{self.name}] {action}")

    def create_recommendation(self, target_user_id: int, recommendation: str,
                              priority: str = "normal", data: dict = None):
        """Create a recommendation for a user."""
        if not self.db:
            logger.info(f"[{self.name}] Recommendation for user {target_user_id}: {recommendation[:50]}...")
            return
        from models.db import AgentRecommendation
        rec = AgentRecommendation(
            agent_name=self.name,
            target_user_id=target_user_id,
            recommendation=recommendation,
            priority=priority,
            data=data,
            created_at=datetime.utcnow(),
        )
        self.db.add(rec)
        self.db.commit()
        logger.info(f"[{self.name}] Recommendation for user {target_user_id}: {recommendation[:50]}...")
