from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, literal_column, case

from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.schemas.contest import ContestCreate, ContestUpdate


class ContestRepository:
    @staticmethod
    def create_contest(db: Session, contest: ContestCreate, creator_id: int) -> Contest:
        db_contest = Contest(
            title=contest.title,
            description=contest.description,
            is_private=contest.is_private,
            password=contest.password,
            min_votes_required=contest.min_votes_required,
            end_date=contest.end_date,
            judge_restrictions=contest.judge_restrictions,
            author_restrictions=contest.author_restrictions,
            creator_id=creator_id
        )
        db.add(db_contest)
        db.commit()
        db.refresh(db_contest)
        return db_contest
    
    @staticmethod
    def get_contests(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        state: Optional[str] = None,
        is_private: Optional[bool] = None,
        creator_id: Optional[int] = None
    ) -> List[Contest]:
        query = db.query(Contest)
        
        # Apply filters if provided
        if state:
            query = query.filter(Contest.state == state)
        if is_private is not None:
            query = query.filter(Contest.is_private == is_private)
        if creator_id:
            query = query.filter(Contest.creator_id == creator_id)
            
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_contest(db: Session, contest_id: int) -> Optional[Contest]:
        return db.query(Contest).filter(Contest.id == contest_id).first()
    
    @staticmethod
    def update_contest(
        db: Session, contest_id: int, contest_update: ContestUpdate
    ) -> Optional[Contest]:
        db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
        if not db_contest:
            return None
        
        update_data = contest_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_contest, key, value)
        
        db.commit()
        db.refresh(db_contest)
        return db_contest
    
    @staticmethod
    def delete_contest(db: Session, contest_id: int) -> bool:
        db_contest = db.query(Contest).filter(Contest.id == contest_id).first()
        if not db_contest:
            return False
        
        db.delete(db_contest)
        db.commit()
        return True
    
    @staticmethod
    def get_contest_with_counts(db: Session, contest_id: int) -> Optional[dict]:
        """Get contest with participant count and text count"""
        result = db.query(
            Contest,
            func.count(func.distinct(ContestText.text_id)).label("text_count"),
            func.count(func.distinct(ContestJudge.judge_id)).label("participant_count")
        ).outerjoin(
            ContestText, ContestText.contest_id == Contest.id
        ).outerjoin(
            ContestJudge, ContestJudge.contest_id == Contest.id
        ).filter(
            Contest.id == contest_id
        ).group_by(
            Contest.id
        ).first()
        
        if not result:
            return None
            
        contest, text_count, participant_count = result
        return {
            "contest": contest,
            "text_count": text_count,
            "participant_count": participant_count
        }
    
    # Methods for contest text submissions
    @staticmethod
    def submit_text_to_contest(db: Session, contest_id: int, text_id: int) -> Optional[ContestText]:
        # Check if text is already submitted to this contest
        existing = db.query(ContestText).filter(
            ContestText.contest_id == contest_id,
            ContestText.text_id == text_id
        ).first()
        
        if existing:
            return None  # Already submitted
            
        db_contest_text = ContestText(
            contest_id=contest_id,
            text_id=text_id
        )
        db.add(db_contest_text)
        db.commit()
        db.refresh(db_contest_text)
        return db_contest_text
    
    @staticmethod
    def get_contest_texts(db: Session, contest_id: int) -> List[ContestText]:
        return db.query(ContestText).filter(
            ContestText.contest_id == contest_id
        ).all()
    
    @staticmethod
    def remove_text_from_contest(db: Session, contest_id: int, text_id: int) -> bool:
        db_contest_text = db.query(ContestText).filter(
            ContestText.contest_id == contest_id,
            ContestText.text_id == text_id
        ).first()
        
        if not db_contest_text:
            return False
            
        db.delete(db_contest_text)
        db.commit()
        return True
    
    # Methods for contest judge assignments
    @staticmethod
    def assign_judge_to_contest(db: Session, contest_id: int, judge_id: int) -> Optional[ContestJudge]:
        # Check if judge is already assigned to this contest
        existing = db.query(ContestJudge).filter(
            ContestJudge.contest_id == contest_id,
            ContestJudge.judge_id == judge_id
        ).first()
        
        if existing:
            return None  # Already assigned
            
        db_contest_judge = ContestJudge(
            contest_id=contest_id,
            judge_id=judge_id
        )
        db.add(db_contest_judge)
        db.commit()
        db.refresh(db_contest_judge)
        return db_contest_judge
    
    @staticmethod
    def get_contest_judges(db: Session, contest_id: int) -> List[ContestJudge]:
        return db.query(ContestJudge).filter(
            ContestJudge.contest_id == contest_id
        ).all()
    
    @staticmethod
    def remove_judge_from_contest(db: Session, contest_id: int, judge_id: int) -> bool:
        db_contest_judge = db.query(ContestJudge).filter(
            ContestJudge.contest_id == contest_id,
            ContestJudge.judge_id == judge_id
        ).first()
        
        if not db_contest_judge:
            return False
            
        db.delete(db_contest_judge)
        db.commit()
        return True 