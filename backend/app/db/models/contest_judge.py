from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Index, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base
# Import Agent model for relationship typing if not already implicitly available
# from .agent import Agent # Assuming Agent model is in agent.py
# from .user import User # Assuming User model is in user.py


class ContestJudge(Base):
    __tablename__ = "contest_judges"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id", ondelete="CASCADE"), nullable=False)
    
    # Changed judge_id to user_judge_id and made it nullable
    user_judge_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    # Added agent_judge_id, nullable
    agent_judge_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=True)
    
    # Relationships
    user_judge = relationship("User", foreign_keys=[user_judge_id], back_populates="contest_judges")
    agent_judge = relationship("Agent", foreign_keys=[agent_judge_id], back_populates="contest_judges")
    contest = relationship("Contest", back_populates="contest_judges")
    
    assignment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    has_voted = Column(Boolean, default=False)
    
    __table_args__ = (
        # Updated unique constraint to consider both types of judges for a contest
        Index("contest_judge_user_unique", contest_id, user_judge_id, unique=True, postgresql_where=user_judge_id.is_not(None)),
        Index("contest_judge_agent_unique", contest_id, agent_judge_id, unique=True, postgresql_where=agent_judge_id.is_not(None)),
        # Check constraint to ensure only one of user_judge_id or agent_judge_id is set
        CheckConstraint(
            "(user_judge_id IS NOT NULL AND agent_judge_id IS NULL) OR "
            "(user_judge_id IS NULL AND agent_judge_id IS NOT NULL)",
            name="ck_contest_judge_one_type_only"
        ),
    )

    # Add relationships to User and Agent if they are not defined elsewhere
    # and are needed directly on ContestJudge.
    # Typically, the "many-to-many" relationship is defined on Contest and User/Agent models
    # referencing this association table.

    # The existing relationships might be:
    # In Contest model: judges = relationship("User", secondary="contest_judges", ...)
    # This will need to be more complex now, or Contest will have two judge lists:
    # human_judges and ai_judges. # This is handled by Contest.contest_judges providing ContestJudge objects

    # For now, focusing on the structure of ContestJudge itself.
    # The relationships in User.py and Contest.py referring to ContestJudge
    # will need to be updated.
    # User.contest_judges (links User to ContestJudge entries where user_judge_id is set) # DONE
    # Agent would need a similar contest_judges relationship. # DONE
    # Contest.contest_judges (would need to be able to fetch both types, or be split) # DONE - Contest.contest_judges links to ContestJudge entries 