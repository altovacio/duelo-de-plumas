from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.repositories.credit_repository import CreditRepository
from app.db.repositories.user_repository import UserRepository
from app.schemas.credit import (
    CreditTransactionCreate,
    CreditTransactionResponse,
    CreditTransactionFilter,
    CreditUsageSummary,
    UserCreditUpdate
)


class CreditService:
    @staticmethod
    def add_credits(
        db: Session, user_id: int, credit_update: UserCreditUpdate
    ) -> CreditTransactionResponse:
        """
        Add credits to a user's account and record the transaction.
        This operation can only be performed by an admin.
        """
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # Create a credit transaction record
        transaction = CreditTransactionCreate(
            user_id=user_id,
            amount=credit_update.credits,
            transaction_type="addition",
            description=credit_update.description
        )
        
        # Update user's credit balance
        user.credits += credit_update.credits
        db.commit()
        
        # Record the transaction
        db_transaction = CreditRepository.create_transaction(db, transaction)
        return CreditTransactionResponse.from_orm(db_transaction)
    
    @staticmethod
    def deduct_credits(
        db: Session,
        user_id: int,
        amount: int,
        description: str,
        ai_model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        model_cost_rate: Optional[float] = None
    ) -> CreditTransactionResponse:
        """
        Deduct credits from a user's account and record the transaction.
        Used when a user consumes credits for AI services.
        """
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # Check if user has enough credits
        if user.credits < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. Required: {amount}, Available: {user.credits}"
            )
        
        # Create a credit transaction record
        transaction = CreditTransactionCreate(
            user_id=user_id,
            amount=-amount,  # Negative amount for deduction
            transaction_type="deduction",
            description=description,
            ai_model=ai_model,
            tokens_used=tokens_used,
            model_cost_rate=model_cost_rate
        )
        
        # Update user's credit balance
        user.credits -= amount
        db.commit()
        
        # Record the transaction
        db_transaction = CreditRepository.create_transaction(db, transaction)
        return CreditTransactionResponse.from_orm(db_transaction)
    
    @staticmethod
    def get_user_transactions(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[CreditTransactionResponse]:
        """Get all credit transactions for a specific user."""
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        transactions = CreditRepository.get_transactions_by_user(db, user_id, skip, limit)
        return [CreditTransactionResponse.from_orm(transaction) for transaction in transactions]
    
    @staticmethod
    def filter_transactions(
        db: Session, filters: CreditTransactionFilter, skip: int = 0, limit: int = 100
    ) -> List[CreditTransactionResponse]:
        """Filter credit transactions based on various criteria."""
        transactions = CreditRepository.filter_transactions(db, filters, skip, limit)
        return [CreditTransactionResponse.from_orm(transaction) for transaction in transactions]
    
    @staticmethod
    def get_credit_usage_summary(db: Session) -> CreditUsageSummary:
        """Get a summary of credit usage across the system."""
        return CreditRepository.get_credit_usage_summary(db)
    
    @staticmethod
    def has_sufficient_credits(db: Session, user_id: int, required_credits: int) -> bool:
        """Check if a user has sufficient credits for an operation."""
        user = UserRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        return user.credits >= required_credits 