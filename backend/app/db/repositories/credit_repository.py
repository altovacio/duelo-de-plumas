from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select, text
from sqlalchemy.orm import selectinload

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
    async def filter_transactions_with_user_info(
        db: AsyncSession,
        filters: CreditTransactionFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Filter credit transactions with user information."""
        stmt = (
            select(
                CreditTransaction.id,
                CreditTransaction.user_id,
                CreditTransaction.amount,
                CreditTransaction.transaction_type,
                CreditTransaction.description,
                CreditTransaction.ai_model,
                CreditTransaction.tokens_used,
                CreditTransaction.real_cost_usd,
                CreditTransaction.created_at,
                User.username,
                User.email
            )
            .join(User, User.id == CreditTransaction.user_id)
        )
        
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
        
        # Convert to list of dictionaries
        transactions = []
        for row in result.all():
            transactions.append({
                'id': row.id,
                'user_id': row.user_id,
                'amount': row.amount,
                'transaction_type': row.transaction_type,
                'description': row.description,
                'ai_model': row.ai_model,
                'tokens_used': row.tokens_used,
                'real_cost_usd': row.real_cost_usd,
                'created_at': row.created_at,
                'username': row.username,
                'email': row.email
            })
        
        return transactions
    
    @staticmethod
    async def get_filtered_summary_stats(
        db: AsyncSession,
        filters: CreditTransactionFilter
    ) -> Dict[str, Any]:
        """Get summary statistics for filtered transactions."""
        base_stmt = select(CreditTransaction)
        
        # Apply same filters as the main query
        if filters.user_id:
            base_stmt = base_stmt.filter(CreditTransaction.user_id == filters.user_id)
        
        if filters.transaction_type:
            base_stmt = base_stmt.filter(CreditTransaction.transaction_type == filters.transaction_type)
        
        if filters.ai_model:
            base_stmt = base_stmt.filter(CreditTransaction.ai_model == filters.ai_model)
        
        if filters.date_from:
            base_stmt = base_stmt.filter(CreditTransaction.created_at >= filters.date_from)
        
        if filters.date_to:
            base_stmt = base_stmt.filter(CreditTransaction.created_at <= filters.date_to)
        
        # Calculate summary stats
        result = await db.execute(base_stmt)
        transactions = result.scalars().all()
        
        total_purchased = sum(t.amount for t in transactions if t.transaction_type == 'purchase')
        total_consumed = abs(sum(t.amount for t in transactions if t.transaction_type == 'consumption'))
        total_refunded = sum(t.amount for t in transactions if t.transaction_type == 'refund')
        total_adjusted = sum(t.amount for t in transactions if t.transaction_type == 'admin_adjustment')
        total_cost_usd = sum(t.real_cost_usd or 0 for t in transactions)
        
        return {
            'total_purchased': total_purchased,
            'total_consumed': total_consumed,
            'total_refunded': total_refunded,
            'total_adjusted': total_adjusted,
            'total_cost_usd': total_cost_usd,
            'total_transactions': len(transactions)
        }
    
    @staticmethod
    async def get_credit_usage_summary(db: AsyncSession) -> CreditUsageSummary:
        """Get a summary of credit usage across the system."""
        # Total credits consumed
        total_credits_consumed_stmt = select(func.sum(func.abs(CreditTransaction.amount))).filter(
            CreditTransaction.transaction_type == "consumption"
        )
        total_credits_consumed_result = await db.execute(total_credits_consumed_stmt)
        total_credits_used = total_credits_consumed_result.scalar_one_or_none() or 0
        
        # Credits consumed by AI model
        usage_by_model_stmt = select(
            CreditTransaction.ai_model,
            func.sum(func.abs(CreditTransaction.amount)).label("total")
        ).filter(
            CreditTransaction.transaction_type == "consumption",
            CreditTransaction.ai_model.is_not(None)
        ).group_by(CreditTransaction.ai_model)
        usage_by_model_result = await db.execute(usage_by_model_stmt)
        usage_by_model_rows = usage_by_model_result.all()
        usage_by_model = {model: total for model, total in usage_by_model_rows}
        
        # Credits consumed by user
        usage_by_user_stmt = select(
            User.username,
            func.sum(func.abs(CreditTransaction.amount)).label("total")
        ).join(
            User, User.id == CreditTransaction.user_id
        ).filter(
            CreditTransaction.transaction_type == "consumption"
        ).group_by(User.username)
        usage_by_user_result = await db.execute(usage_by_user_stmt)
        usage_by_user_rows = usage_by_user_result.all()
        usage_by_user = {username: total for username, total in usage_by_user_rows}
        
        # Average cost per consumption operation
        consumption_count_stmt = select(func.count(CreditTransaction.id)).filter(
            CreditTransaction.transaction_type == "consumption",
            CreditTransaction.ai_model.is_not(None)
        )
        consumption_count_result = await db.execute(consumption_count_stmt)
        consumption_count = consumption_count_result.scalar_one_or_none() or 1
        
        average_cost = abs(total_credits_used) / consumption_count if consumption_count > 0 else 0
        
        # Total tokens used
        total_tokens_used_stmt = select(func.sum(CreditTransaction.tokens_used)).filter(
            CreditTransaction.tokens_used.is_not(None)
        )
        total_tokens_used_result = await db.execute(total_tokens_used_stmt)
        total_tokens_used = total_tokens_used_result.scalar_one_or_none() or 0
        
        # Compute real cost in USD using the stored real_cost_usd field
        real_cost_stmt = select(func.sum(CreditTransaction.real_cost_usd)).filter(
            CreditTransaction.transaction_type == "consumption",
            CreditTransaction.real_cost_usd.is_not(None)
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