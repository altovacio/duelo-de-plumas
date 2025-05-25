from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.database import get_db
from app.api.routes.auth import get_current_user
from app.db.models.user import User as UserModel
from app.db.models.ai_debug_log import AIDebugLog
from app.utils.debug_logger import AIDebugLogger
from app.core.config import settings

router = APIRouter()

@router.get("/admin/ai-debug-logs", response_class=HTMLResponse)
async def get_ai_debug_logs_page(
    operation_type: Optional[str] = Query(None, description="Filter by operation type (writer/judge)"),
    limit: int = Query(50, description="Number of logs to show"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Admin page to view AI debug logs (development only)."""
    
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if debug logging is enabled
    if not AIDebugLogger.is_enabled():
        return HTMLResponse("""
        <html>
        <head><title>AI Debug Logs</title></head>
        <body>
            <h1>AI Debug Logs</h1>
            <p><strong>Debug logging is disabled.</strong></p>
            <p>Debug logging is only available in development mode (DEBUG=True).</p>
        </body>
        </html>
        """)
    
    # Build query
    query = select(AIDebugLog).order_by(desc(AIDebugLog.timestamp))
    
    if operation_type:
        query = query.where(AIDebugLog.operation_type == operation_type)
    
    query = query.limit(limit)
    
    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Debug Logs</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
            .filters {{ margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
            .filters a {{ margin-right: 15px; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
            .filters a:hover {{ background: #0056b3; }}
            .filters a.active {{ background: #28a745; }}
            .log-entry {{ border: 1px solid #ddd; margin-bottom: 15px; border-radius: 5px; overflow: hidden; }}
            .log-header {{ background: #f8f9fa; padding: 12px; border-bottom: 1px solid #ddd; cursor: pointer; }}
            .log-header:hover {{ background: #e9ecef; }}
            .log-content {{ padding: 15px; display: none; }}
            .log-content.show {{ display: block; }}
            .operation-writer {{ border-left: 4px solid #28a745; }}
            .operation-judge {{ border-left: 4px solid #007bff; }}
            .metrics {{ display: flex; gap: 20px; margin-top: 10px; }}
            .metric {{ background: #e9ecef; padding: 5px 10px; border-radius: 3px; font-size: 0.9em; }}
            .section {{ margin-bottom: 15px; }}
            .section h4 {{ margin: 0 0 8px 0; color: #495057; }}
            .content-box {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.9em; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
            .no-logs {{ text-align: center; padding: 40px; color: #6c757d; }}
            .refresh-info {{ text-align: center; margin-bottom: 20px; color: #6c757d; font-size: 0.9em; }}
        </style>
        <script>
            function toggleLog(id) {{
                const content = document.getElementById('content-' + id);
                content.classList.toggle('show');
            }}
            
            // Auto-refresh every 30 seconds
            setTimeout(function() {{
                window.location.reload();
            }}, 30000);
        </script>
    </head>
    <body>
        <div class="container">
            <h1>AI Debug Logs</h1>
            
            <div class="refresh-info">
                🔄 Auto-refreshing every 30 seconds | Showing last {limit} operations
            </div>
            
            <div class="filters">
                <a href="/admin/ai-debug-logs" {"class='active'" if not operation_type else ""}>All Operations</a>
                <a href="/admin/ai-debug-logs?operation_type=writer" {"class='active'" if operation_type == 'writer' else ""}>Writer Only</a>
                <a href="/admin/ai-debug-logs?operation_type=judge" {"class='active'" if operation_type == 'judge' else ""}>Judge Only</a>
            </div>
    """
    
    if not logs:
        html_content += """
            <div class="no-logs">
                <h3>No AI operations logged yet</h3>
                <p>AI operations will appear here when they are executed in development mode.</p>
            </div>
        """
    else:
        for log in logs:
            operation_class = f"operation-{log.operation_type}"
            
            # Format timestamp
            timestamp_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # Format metrics
            metrics_html = f"""
                <div class="metrics">
                    <span class="metric">⏱️ {log.execution_time_ms}ms</span>
                    <span class="metric">📝 {log.prompt_tokens or 0} + {log.completion_tokens or 0} = {(log.prompt_tokens or 0) + (log.completion_tokens or 0)} tokens</span>
                    <span class="metric">💰 ${log.cost_usd or 0:.4f}</span>
                    <span class="metric">🤖 {log.model_id or 'Unknown'}</span>
                </div>
            """
            
            html_content += f"""
            <div class="log-entry {operation_class}">
                <div class="log-header" onclick="toggleLog({log.id})">
                    <strong>{timestamp_str}</strong> | 
                    <strong>{log.operation_type.upper()}</strong> | 
                    User: {log.user_id or 'N/A'} | 
                    Agent: {log.agent_id or 'N/A'}
                    {f" | Contest: {log.contest_id}" if log.contest_id else ""}
                    {metrics_html}
                </div>
                <div id="content-{log.id}" class="log-content">
                    <div class="section">
                        <h4>📥 Strategy Input</h4>
                        <div class="content-box">{log.strategy_input or 'No input logged'}</div>
                    </div>
                    
                    <div class="section">
                        <h4>🚀 LLM Prompt</h4>
                        <div class="content-box">{log.llm_prompt or 'No prompt logged'}</div>
                    </div>
                    
                    <div class="section">
                        <h4>🤖 LLM Response</h4>
                        <div class="content-box">{log.llm_response or 'No response logged'}</div>
                    </div>
                    
                    <div class="section">
                        <h4>📤 Parsed Output</h4>
                        <div class="content-box">{log.parsed_output or 'No output logged'}</div>
                    </div>
                </div>
            </div>
            """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@router.get("/admin/ai-debug-logs/api")
async def get_ai_debug_logs_api(
    operation_type: Optional[str] = Query(None),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """API endpoint to get AI debug logs as JSON."""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if not AIDebugLogger.is_enabled():
        return {"enabled": False, "logs": []}
    
    # Build query
    query = select(AIDebugLog).order_by(desc(AIDebugLog.timestamp))
    
    if operation_type:
        query = query.where(AIDebugLog.operation_type == operation_type)
    
    query = query.limit(limit)
    
    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "enabled": True,
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "operation_type": log.operation_type,
                "user_id": log.user_id,
                "agent_id": log.agent_id,
                "contest_id": log.contest_id,
                "model_id": log.model_id,
                "strategy_input": log.strategy_input,
                "llm_prompt": log.llm_prompt,
                "llm_response": log.llm_response,
                "parsed_output": log.parsed_output,
                "execution_time_ms": log.execution_time_ms,
                "prompt_tokens": log.prompt_tokens,
                "completion_tokens": log.completion_tokens,
                "cost_usd": float(log.cost_usd) if log.cost_usd else None
            }
            for log in logs
        ]
    } 