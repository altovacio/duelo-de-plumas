import json
import time
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.db.models.ai_debug_log import AIDebugLog


class AIDebugLogger:
    """Simple debug logger for AI operations (development only)."""
    
    @staticmethod
    def is_enabled() -> bool:
        """Check if debug logging is enabled (only in development)."""
        return settings.DEBUG
    
    @staticmethod
    async def log_writer_operation(
        db: AsyncSession,
        user_id: Optional[int],
        agent_id: Optional[int],
        model_id: str,
        strategy_input: Dict[str, Any],
        llm_prompt: str,
        llm_response: str,
        parsed_output: str,
        execution_time_ms: int,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float
    ):
        """Log a writer operation."""
        if not AIDebugLogger.is_enabled():
            return
            
        try:
            # Format strategy input as readable text
            strategy_input_text = AIDebugLogger._format_strategy_input(strategy_input)
            
            debug_log = AIDebugLog(
                operation_type="writer",
                user_id=user_id,
                agent_id=agent_id,
                model_id=model_id,
                strategy_input=strategy_input_text,
                llm_prompt=llm_prompt,
                llm_response=llm_response,
                parsed_output=parsed_output,
                execution_time_ms=execution_time_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd
            )
            
            db.add(debug_log)
            await db.commit()
            
            # Cleanup old logs (keep only last 1000)
            await AIDebugLogger._cleanup_old_logs(db)
            
        except Exception as e:
            print(f"Debug logging error: {e}")
            # Don't let debug logging break the main operation
            pass
    
    @staticmethod
    async def log_judge_operation(
        db: AsyncSession,
        user_id: Optional[int],
        agent_id: Optional[int],
        contest_id: Optional[int],
        model_id: str,
        strategy_input: Dict[str, Any],
        llm_prompt: str,
        llm_response: str,
        parsed_output: List[Dict[str, Any]],
        execution_time_ms: int,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float
    ):
        """Log a judge operation."""
        if not AIDebugLogger.is_enabled():
            return
            
        try:
            # Format strategy input as readable text
            strategy_input_text = AIDebugLogger._format_strategy_input(strategy_input)
            
            # Format parsed output as readable text
            parsed_output_text = json.dumps(parsed_output, indent=2)
            
            debug_log = AIDebugLog(
                operation_type="judge",
                user_id=user_id,
                agent_id=agent_id,
                contest_id=contest_id,
                model_id=model_id,
                strategy_input=strategy_input_text,
                llm_prompt=llm_prompt,
                llm_response=llm_response,
                parsed_output=parsed_output_text,
                execution_time_ms=execution_time_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd
            )
            
            db.add(debug_log)
            await db.commit()
            
            # Cleanup old logs (keep only last 1000)
            await AIDebugLogger._cleanup_old_logs(db)
            
        except Exception as e:
            print(f"Debug logging error: {e}")
            # Don't let debug logging break the main operation
            pass
    
    @staticmethod
    def _format_strategy_input(strategy_input: Dict[str, Any]) -> str:
        """Format strategy input as readable text."""
        lines = []
        for key, value in strategy_input.items():
            if isinstance(value, str):
                # Truncate long strings
                display_value = value[:200] + "..." if len(value) > 200 else value
                lines.append(f"- {key}: \"{display_value}\"")
            elif isinstance(value, list):
                lines.append(f"- {key}: [{len(value)} items]")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    @staticmethod
    async def _cleanup_old_logs(db: AsyncSession):
        """Keep only the last 1000 debug logs."""
        try:
            await db.execute(
                text("""
                    DELETE FROM ai_debug_logs 
                    WHERE id NOT IN (
                        SELECT id FROM ai_debug_logs 
                        ORDER BY timestamp DESC 
                        LIMIT 1000
                    )
                """)
            )
            await db.commit()
        except Exception as e:
            print(f"Debug log cleanup error: {e}")
            pass
    
    @staticmethod
    async def get_recent_logs(db: AsyncSession, limit: int = 50) -> List[AIDebugLog]:
        """Get recent debug logs for the admin page."""
        if not AIDebugLogger.is_enabled():
            return []
            
        try:
            result = await db.execute(
                text("""
                    SELECT * FROM ai_debug_logs 
                    ORDER BY timestamp DESC 
                    LIMIT :limit
                """),
                {"limit": limit}
            )
            return result.fetchall()
        except Exception as e:
            print(f"Error fetching debug logs: {e}")
            return [] 