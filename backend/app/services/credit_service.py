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
        # We update the credits by passing the amount to add/remove directly
        await user_repo.update_credits(user_id, UserCredit(amount=credit_update.credits, description=credit_update.description))
        
        # Create a credit transaction record
        transaction_create = CreditTransactionCreate(
            user_id=user_id,
            amount=credit_update.credits, # Positive for purchases/refunds, negative for consumption
            transaction_type="admin_adjustment",  # Admin operations are always admin_adjustment
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
        real_cost_usd: Optional[float] = None
    ) -> CreditTransaction:
        """
        Deduct credits from a user's account and record the transaction.
        Used when a user consumes credits for AI services.
        
        Args:
            db: Database session
            user_id: User ID to deduct credits from
            amount: Number of credits to deduct
            description: Description of the transaction
            ai_model: ID of the AI model used (if applicable)
            tokens_used: Total number of tokens used (if applicable)
            real_cost_usd: Actual cost in USD calculated using estimate_cost_usd
        
        Returns:
            The created transaction record
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
        
        # Update user's credit balance via UserRepository
        # Pass negative amount for deduction (UserRepository will add this to current credits)
        await user_repo.update_credits(user_id, UserCredit(amount=-amount, description=description))
        
        # Create a credit transaction record
        transaction_create = CreditTransactionCreate(
            user_id=user_id,
            amount=-amount,  # Negative amount for consumption in transaction log
            transaction_type="consumption",
            description=description,
            ai_model=ai_model,
            tokens_used=tokens_used,
            real_cost_usd=real_cost_usd
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
    async def filter_transactions_with_user_info(
        db: AsyncSession, filters: CreditTransactionFilter, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        """Filter credit transactions with user information."""
        return await CreditRepository.filter_transactions_with_user_info(db, filters, skip, limit)
    
    @staticmethod
    async def get_filtered_summary_stats(
        db: AsyncSession, filters: CreditTransactionFilter
    ) -> dict:
        """Get summary statistics for filtered transactions."""
        return await CreditRepository.get_filtered_summary_stats(db, filters)
    
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
    
    @staticmethod
    async def add_purchase_credits(
        db: AsyncSession,
        user_id: int,
        amount: int,
        description: str
    ) -> CreditTransaction:
        """
        Add credits to a user's account from a purchase and record the transaction.
        """
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase amount must be positive."
            )
            
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # Update user's credit balance
        await user_repo.update_credits(user_id, UserCredit(amount=amount, description=description))
        
        # Create a credit transaction record
        transaction_create = CreditTransactionCreate(
            user_id=user_id,
            amount=amount,
            transaction_type="purchase",
            description=description
        )
        db_transaction = await CreditRepository.create_transaction(db, transaction_create)
        return db_transaction
    
    @staticmethod
    async def process_refund(
        db: AsyncSession,
        user_id: int,
        amount: int,
        description: str
    ) -> CreditTransaction:
        """
        Process a refund for a user and record the transaction.
        Refunds add credits back to the user's account.
        """
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount must be positive."
            )
            
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # Update user's credit balance
        await user_repo.update_credits(user_id, UserCredit(amount=amount, description=description))
        
        # Create a credit transaction record
        transaction_create = CreditTransactionCreate(
            user_id=user_id,
            amount=amount,
            transaction_type="refund",
            description=description
        )
        db_transaction = await CreditRepository.create_transaction(db, transaction_create)
        return db_transaction 