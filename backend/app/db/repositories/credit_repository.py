from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text

from app.db.models.credit_transaction import CreditTransaction
from app.db.models.user import User
from app.schemas.credit import CreditTransactionCreate, CreditTransactionFilter, CreditUsageSummary


class CreditRepository:
    @staticmethod
    def create_transaction(db: Session, transaction: CreditTransactionCreate) -> CreditTransaction:
        """Create a new credit transaction record."""
        db_transaction = CreditTransaction(**transaction.dict())
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction
    
    @staticmethod
    def get_transactions_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[CreditTransaction]:
        """Get all credit transactions for a specific user."""
        return db.query(CreditTransaction).filter(
            CreditTransaction.user_id == user_id
        ).order_by(
            desc(CreditTransaction.created_at)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_transaction_by_id(db: Session, transaction_id: int) -> Optional[CreditTransaction]:
        """Get a specific credit transaction by ID."""
        return db.query(CreditTransaction).filter(CreditTransaction.id == transaction_id).first()
    
    @staticmethod
    def filter_transactions(
        db: Session, 
        filters: CreditTransactionFilter,
        skip: int = 0, 
        limit: int = 100
    ) -> List[CreditTransaction]:
        """Filter credit transactions based on various criteria."""
        query = db.query(CreditTransaction)
        
        if filters.user_id:
            query = query.filter(CreditTransaction.user_id == filters.user_id)
        
        if filters.transaction_type:
            query = query.filter(CreditTransaction.transaction_type == filters.transaction_type)
        
        if filters.ai_model:
            query = query.filter(CreditTransaction.ai_model == filters.ai_model)
        
        if filters.date_from:
            query = query.filter(CreditTransaction.created_at >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(CreditTransaction.created_at <= filters.date_to)
        
        return query.order_by(desc(CreditTransaction.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_credit_usage_summary(db: Session) -> CreditUsageSummary:
        """Get a summary of credit usage across the system."""
        # Total credits used (sum of all deductions)
        total_credits_used = db.query(
            func.sum(CreditTransaction.amount).label("total")
        ).filter(
            CreditTransaction.transaction_type == "deduction"
        ).scalar() or 0
        
        # Credits used by AI model
        usage_by_model_query = db.query(
            CreditTransaction.ai_model,
            func.sum(CreditTransaction.amount).label("total")
        ).filter(
            CreditTransaction.transaction_type == "deduction",
            CreditTransaction.ai_model.is_not(None)
        ).group_by(
            CreditTransaction.ai_model
        ).all()
        
        usage_by_model = {model: abs(total) for model, total in usage_by_model_query}
        
        # Credits used by user
        usage_by_user_query = db.query(
            User.username,
            func.sum(CreditTransaction.amount).label("total")
        ).join(
            User, User.id == CreditTransaction.user_id
        ).filter(
            CreditTransaction.transaction_type == "deduction"
        ).group_by(
            User.username
        ).all()
        
        usage_by_user = {username: abs(total) for username, total in usage_by_user_query}
        
        # Average cost per operation
        operations_count = db.query(
            func.count(CreditTransaction.id)
        ).filter(
            CreditTransaction.transaction_type == "deduction",
            CreditTransaction.ai_model.is_not(None)
        ).scalar() or 1  # Avoid division by zero
        
        average_cost = abs(total_credits_used) / operations_count if operations_count > 0 else 0
        
        # Total tokens used
        total_tokens_used = db.query(
            func.sum(CreditTransaction.tokens_used).label("total_tokens")
        ).filter(
            CreditTransaction.tokens_used.is_not(None)
        ).scalar() or 0
        
        return CreditUsageSummary(
            total_credits_used=abs(total_credits_used),
            usage_by_model=usage_by_model,
            usage_by_user=usage_by_user,
            average_cost_per_operation=average_cost,
            total_tokens_used=total_tokens_used
        ) 