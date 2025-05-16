from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select, text

from app.db.models.credit_transaction import CreditTransaction
from app.db.models.user import User
from app.schemas.credit import CreditTransactionCreate, CreditTransactionFilter, CreditUsageSummary


class CreditRepository:
    @staticmethod
    async def create_transaction(db: AsyncSession, transaction_data: CreditTransactionCreate) -> CreditTransaction:
        """Create a new credit transaction record."""
        db_transaction = CreditTransaction(**transaction_data.model_dump())
        db.add(db_transaction)
        await db.commit()
        await db.refresh(db_transaction)
        return db_transaction
    
    @staticmethod
    async def get_transactions_by_user(
        db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[CreditTransaction]:
        """Get all credit transactions for a specific user."""
        stmt = select(CreditTransaction).filter(
            CreditTransaction.user_id == user_id
        ).order_by(
            desc(CreditTransaction.created_at)
        ).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_transaction_by_id(db: AsyncSession, transaction_id: int) -> Optional[CreditTransaction]:
        """Get a specific credit transaction by ID."""
        stmt = select(CreditTransaction).filter(CreditTransaction.id == transaction_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def filter_transactions(
        db: AsyncSession,
        filters: CreditTransactionFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[CreditTransaction]:
        """Filter credit transactions based on various criteria."""
        stmt = select(CreditTransaction)
        
        if filters.user_id:
            stmt = stmt.filter(CreditTransaction.user_id == filters.user_id)
        
        if filters.transaction_type:
            stmt = stmt.filter(CreditTransaction.transaction_type == filters.transaction_type)
        
        if filters.ai_model:
            stmt = stmt.filter(CreditTransaction.ai_model == filters.ai_model)
        
        if filters.date_from:
            stmt = stmt.filter(CreditTransaction.created_at >= filters.date_from)
        
        if filters.date_to:
            stmt = stmt.filter(CreditTransaction.created_at <= filters.date_to)
        
        stmt = stmt.order_by(desc(CreditTransaction.created_at)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_credit_usage_summary(db: AsyncSession) -> CreditUsageSummary:
        """Get a summary of credit usage across the system."""
        # Total credits used
        total_credits_used_stmt = select(func.sum(CreditTransaction.amount)).filter(
            CreditTransaction.transaction_type == "deduction"
        )
        total_credits_used_result = await db.execute(total_credits_used_stmt)
        total_credits_used = total_credits_used_result.scalar_one_or_none() or 0
        
        # Credits used by AI model
        usage_by_model_stmt = select(
            CreditTransaction.ai_model,
            func.sum(CreditTransaction.amount).label("total")
        ).filter(
            CreditTransaction.transaction_type == "deduction",
            CreditTransaction.ai_model.is_not(None)
        ).group_by(CreditTransaction.ai_model)
        usage_by_model_result = await db.execute(usage_by_model_stmt)
        usage_by_model_rows = usage_by_model_result.all()
        usage_by_model = {model: abs(total) for model, total in usage_by_model_rows}
        
        # Credits used by user
        usage_by_user_stmt = select(
            User.username,
            func.sum(CreditTransaction.amount).label("total")
        ).join(
            User, User.id == CreditTransaction.user_id
        ).filter(
            CreditTransaction.transaction_type == "deduction"
        ).group_by(User.username)
        usage_by_user_result = await db.execute(usage_by_user_stmt)
        usage_by_user_rows = usage_by_user_result.all()
        usage_by_user = {username: abs(total) for username, total in usage_by_user_rows}
        
        # Average cost per operation
        operations_count_stmt = select(func.count(CreditTransaction.id)).filter(
            CreditTransaction.transaction_type == "deduction",
            CreditTransaction.ai_model.is_not(None)
        )
        operations_count_result = await db.execute(operations_count_stmt)
        operations_count = operations_count_result.scalar_one_or_none() or 1
        
        average_cost = abs(total_credits_used) / operations_count if operations_count > 0 else 0
        
        # Total tokens used
        total_tokens_used_stmt = select(func.sum(CreditTransaction.tokens_used)).filter(
            CreditTransaction.tokens_used.is_not(None)
        )
        total_tokens_used_result = await db.execute(total_tokens_used_stmt)
        total_tokens_used = total_tokens_used_result.scalar_one_or_none() or 0
        
        # Compute real cost in USD
        real_cost_stmt = select(func.sum(CreditTransaction.model_cost_rate)).filter(
            CreditTransaction.transaction_type == "deduction",
            CreditTransaction.model_cost_rate.is_not(None)
        )
        real_cost_result = await db.execute(real_cost_stmt)
        total_real_cost_usd = real_cost_result.scalar_one_or_none() or 0.0
        
        return CreditUsageSummary(
            total_credits_used=abs(total_credits_used),
            usage_by_model=usage_by_model,
            usage_by_user=usage_by_user,
            average_cost_per_operation=average_cost,
            total_tokens_used=total_tokens_used,
            total_real_cost_usd=total_real_cost_usd
        ) 