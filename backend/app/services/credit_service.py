from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.credit_repository import CreditRepository
from app.db.repositories.user_repository import UserRepository
from app.schemas.credit import (
    CreditTransactionCreate,
    CreditTransactionResponse,
    CreditTransactionFilter,
    CreditUsageSummary,
    UserCreditUpdate
)
from app.db.models.credit_transaction import CreditTransaction
from app.db.models.user import User
from app.schemas.user import UserCredit


class CreditService:
    @staticmethod
    async def add_credits(
        db: AsyncSession, user_id: int, credit_update: UserCreditUpdate
    ) -> CreditTransaction:
        """
        Add credits to a user's account and record the transaction.
        This operation can only be performed by an admin.
        """
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # Update user's credit balance via UserRepository
        new_credit_value = user.credits + credit_update.credits
        await user_repo.update_credits(user_id, UserCredit(credits=new_credit_value))
        # Note: user object in memory might be stale here, but transaction records new balance contextually
        
        # Create a credit transaction record
        transaction_create = CreditTransactionCreate(
            user_id=user_id,
            amount=credit_update.credits, # Positive for addition
            transaction_type="addition",
            description=credit_update.description
        )
        db_transaction = await CreditRepository.create_transaction(db, transaction_create)
        return db_transaction
    
    @staticmethod
    async def deduct_credits(
        db: AsyncSession,
        user_id: int,
        amount: int,
        description: str,
        ai_model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        model_cost_rate: Optional[float] = None
    ) -> CreditTransaction:
        """
        Deduct credits from a user's account and record the transaction.
        Used when a user consumes credits for AI services.
        """
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deduction amount must be positive."
            )
        
        if user.credits < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient credits. Required: {amount}, Available: {user.credits}"
            )
        
        # Update user's credit balance via UserRepository
        new_credit_value = user.credits - amount
        await user_repo.update_credits(user_id, UserCredit(credits=new_credit_value))
        
        # Create a credit transaction record
        transaction_create = CreditTransactionCreate(
            user_id=user_id,
            amount=-amount,  # Negative amount for deduction in transaction log
            transaction_type="deduction",
            description=description,
            ai_model=ai_model,
            tokens_used=tokens_used,
            model_cost_rate=model_cost_rate
        )
        db_transaction = await CreditRepository.create_transaction(db, transaction_create)
        return db_transaction
    
    @staticmethod
    async def get_user_transactions(
        db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[CreditTransaction]:
        """Get all credit transactions for a specific user."""
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        transactions = await CreditRepository.get_transactions_by_user(db, user_id, skip, limit)
        return transactions
    
    @staticmethod
    async def filter_transactions(
        db: AsyncSession, filters: CreditTransactionFilter, skip: int = 0, limit: int = 100
    ) -> List[CreditTransaction]:
        """Filter credit transactions based on various criteria."""
        transactions = await CreditRepository.filter_transactions(db, filters, skip, limit)
        return transactions
    
    @staticmethod
    async def get_credit_usage_summary(db: AsyncSession) -> CreditUsageSummary:
        """Get a summary of credit usage across the system."""
        return await CreditRepository.get_credit_usage_summary(db)
    
    @staticmethod
    async def has_sufficient_credits(db: AsyncSession, user_id: int, required_credits: int) -> bool:
        """Check if a user has sufficient credits for an operation."""
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            # Consider if this should return False or raise an error.
            # Raising error seems more appropriate if user must exist.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found for credit check"
            )
        if required_credits < 0: # Credits required should not be negative
            return True # Or raise error, depends on desired behavior

        result = user.credits >= required_credits
        return result 