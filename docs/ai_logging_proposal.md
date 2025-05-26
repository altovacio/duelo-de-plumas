# AI Services Logging Proposal

## Current State Analysis

### AI Services Review

After reviewing the codebase, I can confirm that both AI services (writer and judge) **are correctly consuming AI strategies**:

#### ✅ Writer Service
- **Location**: `backend/app/services/ai_service.py` - `generate_text()` method
- **Strategy Used**: `WriterStrategy` from `app.services.ai_strategies.writer_strategies`
- **Strategy Interface**: Implements `WriterStrategyInterface`
- **Current Flow**: AIService → WriterStrategy → AIProvider → LLM

#### ✅ Judge Service  
- **Location**: `backend/app/services/ai_service.py` - `judge_contest()` method
- **Strategy Used**: `SimpleChatCompletionJudgeStrategy` from `app.services.ai_strategies.judge_strategies`
- **Strategy Interface**: Implements `JudgeStrategyInterface`
- **Current Flow**: AIService → JudgeStrategy → AIProvider → LLM

### Current Logging State

The project currently has:
- Basic Python logging configured in strategies (`logger = logging.getLogger(__name__)`)
- Some debug logging in judge strategies (lines 55-58 in `judge_strategies.py`)
- No structured LLM input/output logging
- No centralized logging configuration for AI operations

## Proposed Logging Solution

### 1. Logging Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Service    │───▶│   AI Strategy    │───▶│  AI Provider    │
│                 │    │                  │    │                 │
│ - Log requests  │    │ - Log prompts    │    │ - Log API calls │
│ - Log responses │    │ - Log parsing    │    │ - Log tokens    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Centralized AI Logger                        │
│                                                                 │
│ - Structured JSON logs                                          │
│ - Request/Response correlation                                  │
│ - Performance metrics                                           │
│ - Error tracking                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Implementation Plan (Simplified for Development)

#### Phase 1: Quick Development Debug Logging (DEVELOPMENT ONLY)
**Goal**: Simple way to see what we send to LLM and what we get back

**Admin Web Page Implementation:**
- Add simple admin page: `/admin/ai-debug-logs`
- Show last 50 AI operations in a table
- Real-time view of what's happening

**Implementation Steps**: 
1. Create simple debug table in database
2. Add debug logging to AI strategies (development mode only)
3. Create admin page to view logs
4. Auto-cleanup old logs

#### Phase 2: Enhanced Logging (Future)
- Add database storage
- Add filtering and search
- Add analytics and monitoring

#### Phase 3: Production Logging (Future)
- Metadata-only logging for production
- Performance monitoring
- Cost tracking

### 3. Simple Debug Log Structure (Phase 1)

#### Simple Table for Development: `ai_debug_logs`
```sql
CREATE TABLE ai_debug_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    operation_type VARCHAR(20) NOT NULL, -- 'writer' or 'judge'
    
    -- Basic context
    user_id INTEGER,
    agent_id INTEGER,
    contest_id INTEGER,  -- for judge operations
    model_id VARCHAR(100),
    
    -- What we send to LLM
    strategy_input TEXT,      -- Variables passed to strategy
    llm_prompt TEXT,          -- Actual prompt sent to LLM
    
    -- What we get back
    llm_response TEXT,        -- Raw LLM response
    parsed_output TEXT,       -- What we extracted/parsed
    
    -- Performance
    execution_time_ms INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    
    -- Only keep recent logs (for development)
    INDEX idx_ai_debug_timestamp (timestamp)
);

-- Auto-cleanup old logs (keep only last 1000 records)
CREATE OR REPLACE FUNCTION cleanup_ai_debug_logs() RETURNS void AS $$
BEGIN
    DELETE FROM ai_debug_logs 
    WHERE id NOT IN (
        SELECT id FROM ai_debug_logs 
        ORDER BY timestamp DESC 
        LIMIT 1000
    );
END;
$$ LANGUAGE plpgsql;
```

#### Simple Debug Log Example

**Writer Operation:**
```
ID: 1
Timestamp: 2024-01-15 10:30:00
Operation: writer
User: 123, Agent: 456, Model: gpt-4

Strategy Input:
- personality_prompt: "You are a creative writer..."
- contest_description: "Write a short story about time travel"
- user_guidance_title: "The Lost Key"
- temperature: 0.7, max_tokens: 4096

LLM Prompt:
"You are a creative writer. Write a short story based on the following prompt:
...
Contest Description:
Write a short story about time travel
...
Your Generated Text:"

LLM Response:
"Once upon a time, there was a young scientist named Maya who discovered..."

Parsed Output:
"Once upon a time, there was a young scientist named Maya who discovered..."

Performance:
- Execution: 1500ms
- Tokens: 150 prompt + 300 completion = 450 total
- Cost: $0.0045
```

**Judge Operation:**
```
ID: 2
Timestamp: 2024-01-15 10:35:00
Operation: judge
User: 123, Agent: 789, Model: gpt-4

Strategy Input:
- personality_prompt: "You are a literary judge..."
- contest_description: "Evaluate these time travel stories"
- texts: [{"id": 1, "title": "The Lost Key", "content": "Once upon..."}, ...]
- temperature: 0.3

LLM Prompt:
"You are an AI Judge for a writing contest...
Personality Prompt:
You are a literary judge...
Texts to Judge:
Text: The Lost Key
Content:
Once upon a time..."

LLM Response:
"1. The Lost Key
   Commentary: Excellent character development and engaging plot.
2. Story B
   Commentary: Good writing but predictable storyline."

Parsed Output:
[{"text_id": 1, "place": 1, "comment": "Excellent character development..."}, ...]

Performance:
- Execution: 2100ms
- Tokens: 250 prompt + 180 completion = 430 total
- Cost: $0.0043
```

#### How Writer/Judge Logs Relate to Core Entry

The writer and judge logs are **the same database record** with operation-specific data in the JSON fields:

- **Core fields** (timestamp, user_id, tokens, etc.) are always populated
- **input_data JSON** contains operation-specific input (different for writer vs judge)
- **output_data JSON** contains operation-specific output (different for writer vs judge)
- **metadata JSON** contains operation-specific context

#### Writer Operation Log Example
```json
{
  "operation_type": "writer",
  "input_data": {
    "personality_prompt": "You are a creative writer...",
    "contest_description": "Write a short story about...",
    "user_guidance_title": "The Lost Key",
    "user_guidance_description": "Include mystery elements",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "output_data": {
    "generated_content": "Once upon a time...",
    "content_length": 2500
  },
  "metadata": {
    "contest_id": 789,
    "writer_version": "1.0"
  }
}
```

#### Judge Operation Log with Raw LLM Data
```json
{
  "operation_type": "judge",
  "input_data": {
    "personality_prompt": "You are a literary judge...",
    "contest_description": "Evaluate these stories...",
    "texts_count": 5,
    "texts_summary": [
      {"id": 1, "title": "Story A", "length": 1200},
      {"id": 2, "title": "Story B", "length": 1500}
    ],
    "temperature": 0.3,
    "max_tokens": 4096
  },
  "output_data": {
    "votes_count": 5,
    "rankings": [
      {"text_id": 2, "place": 1, "comment_length": 150},
      {"text_id": 1, "place": 2, "comment_length": 120}
    ],
    "parsing_success": true,
    "texts_matched": 5,
    "texts_expected": 5
  },
  "metadata": {
    "contest_id": 789,
    "judge_version": "1.0"
  },
  "raw_llm_request": {
    "model": "gpt-4",
    "messages": [
      {
        "role": "user", 
        "content": "You are an AI Judge for a writing contest...\n\nPersonality Prompt:\nYou are a literary judge...\n\nInput:\nContest Description:\nEvaluate these stories...\n\nTexts to Judge:\nText: Story A\nContent:\nOnce upon a time..."
      }
    ],
    "temperature": 0.3,
    "max_tokens": 4096
  },
  "raw_llm_response": {
    "choices": [
      {
        "message": {
          "content": "1. Story B\n   Commentary: Excellent character development and engaging plot.\n\n2. Story A\n   Commentary: Good writing but predictable storyline.\n\n3. Story C\n   Commentary: Creative concept but needs better execution."
        }
      }
    ],
    "usage": {
      "prompt_tokens": 150,
      "completion_tokens": 300,
      "total_tokens": 450
    }
  },
  "parsing_errors": []
}
```

#### Handling LLM Hallucinations & Parsing Failures

**Example of Failed Judge Parsing:**
```json
{
  "operation_type": "judge",
  "level": "WARN",
  "output_data": {
    "votes_count": 2,  // Only 2 out of 5 texts were parsed
    "rankings": [
      {"text_id": 2, "place": 1, "comment_length": 150},
      {"text_id": 1, "place": 2, "comment_length": 120}
    ],
    "parsing_success": false,
    "texts_matched": 2,
    "texts_expected": 5
  },
  "raw_llm_response": {
    "choices": [
      {
        "message": {
          "content": "I think Story B is really good because it has great characters. Story A is okay but not as engaging. The other stories were confusing and I couldn't understand them properly."
        }
      }
    ]
  },
  "parsing_errors": [
    {
      "error_type": "format_mismatch",
      "message": "LLM response did not follow expected ranking format",
      "expected_pattern": "1. [Title]\\n   Commentary: [text]",
      "actual_content": "I think Story B is really good..."
    },
    {
      "error_type": "missing_texts",
      "message": "LLM only mentioned 2 out of 5 texts",
      "missing_text_ids": [3, 4, 5]
    }
  ]
}
```

### 4. Configuration Options

#### Log Levels
- **DEBUG**: Full prompt/response content, detailed timing
- **INFO**: Operation summaries, token usage, performance
- **WARN**: Parsing issues, fallbacks used
- **ERROR**: API failures, strategy errors

#### Privacy Controls & Environment Configuration
- **Development**: Full logging with complete LLM request/response content
- **Staging**: Sanitized logging with content but PII removed
- **Production**: Metadata only (no content) or sanitized content
- **Testing**: Full logging with additional debug information
- **Disabled**: No AI logging

#### Environment-Specific Settings
```python
# In backend/app/core/config.py
class Settings(BaseSettings):
    # AI Logging Configuration
    AI_LOGGING_ENABLED: bool = True
    AI_LOGGING_LEVEL: str = "INFO"  # DEBUG, INFO, WARN, ERROR
    AI_LOGGING_MODE: str = "FULL"   # FULL, METADATA_ONLY, SANITIZED, DISABLED
    AI_LOGGING_INCLUDE_RAW_LLM: bool = True  # Include raw LLM request/response
    AI_LOGGING_RETENTION_DAYS: int = 90
    
    # Environment-specific defaults
    @property
    def ai_logging_config(self):
        if self.DEBUG:  # Development
            return {
                "mode": "FULL",
                "include_raw_llm": True,
                "level": "DEBUG"
            }
        else:  # Production
            return {
                "mode": "METADATA_ONLY", 
                "include_raw_llm": False,
                "level": "INFO"
            }
```

#### Storage Options
- **File Rotation**: Daily/size-based log rotation
- **Retention Policy**: Configurable retention period
- **Compression**: Automatic log compression

### 5. Quick Implementation (Phase 1)

#### Files to Create
```
backend/app/utils/debug_logger.py       # Simple debug logging utility
backend/app/api/routes/debug_logs.py    # Admin page to view logs
```

#### Files to Modify (Minimal Changes)
```
backend/app/services/ai_strategies/writer_strategies.py  # Add debug logging
backend/app/services/ai_strategies/judge_strategies.py   # Add debug logging
backend/app/core/config.py                              # Add debug flag
backend/app/main.py                                     # Include debug routes
```

#### Admin Page Implementation
**Simple HTML table showing:**
- Timestamp
- Operation type (Writer/Judge)
- User/Agent info
- Strategy inputs (collapsed/expandable)
- LLM prompt (collapsed/expandable)
- LLM response (collapsed/expandable)
- Performance metrics
- Cost

**Features:**
- Auto-refresh every 30 seconds
- Show last 50 operations
- Expandable sections for long text
- Simple filtering by operation type

### 6. Benefits

#### For Development
- **Debugging**: Easy to trace issues through the AI pipeline
- **Performance**: Identify bottlenecks and optimization opportunities
- **Testing**: Verify correct prompt construction and response parsing

#### For Operations
- **Monitoring**: Track AI service health and performance
- **Cost Control**: Monitor token usage and costs
- **Compliance**: Audit trail for AI operations

#### For Users
- **Transparency**: Understand how AI agents work
- **Debugging**: Help users improve their agent prompts
- **Analytics**: Usage patterns and effectiveness metrics

### 7. Security Considerations

- **Data Privacy**: Configurable content logging levels
- **Access Control**: Admin-only access to detailed logs
- **Retention**: Automatic cleanup of old logs
- **Sanitization**: Remove sensitive information from logs

### 8. Log Consumption & Analysis

#### API Endpoints for Log Access
```python
# Get logs for a specific user
GET /admin/ai-logs?user_id=123&limit=50&offset=0

# Get logs for a specific agent
GET /admin/ai-logs?agent_id=456&operation_type=writer

# Get logs for a specific contest
GET /admin/ai-logs?contest_id=789&operation_type=judge

# Get logs by time range
GET /admin/ai-logs?start_date=2024-01-01&end_date=2024-01-31

# Get performance analytics
GET /admin/ai-logs/analytics?group_by=model_id&metric=avg_execution_time
```

#### SQL Query Examples
```sql
-- Find all failed AI operations in the last 24 hours
SELECT * FROM ai_operation_logs 
WHERE level = 'ERROR' 
AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Get token usage by model for cost analysis
SELECT 
    model_id,
    COUNT(*) as operations,
    SUM(total_tokens) as total_tokens,
    SUM(cost_usd) as total_cost,
    AVG(execution_time_ms) as avg_execution_time
FROM ai_operation_logs 
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY model_id;

-- Find the most active users of AI services
SELECT 
    u.username,
    COUNT(*) as ai_operations,
    SUM(l.cost_usd) as total_spent
FROM ai_operation_logs l
JOIN users u ON l.user_id = u.id
WHERE l.timestamp > NOW() - INTERVAL '30 days'
GROUP BY u.id, u.username
ORDER BY ai_operations DESC;

-- Analyze judge vs writer usage patterns
SELECT 
    operation_type,
    DATE_TRUNC('day', timestamp) as date,
    COUNT(*) as operations,
    AVG(execution_time_ms) as avg_time
FROM ai_operation_logs
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY operation_type, DATE_TRUNC('day', timestamp)
ORDER BY date, operation_type;
```

#### Python Code Examples
```python
# Service for querying AI logs
class AILogService:
    @staticmethod
    async def get_user_ai_activity(db: AsyncSession, user_id: int, days: int = 30):
        """Get AI activity summary for a user"""
        result = await db.execute(
            text("""
                SELECT 
                    operation_type,
                    COUNT(*) as count,
                    SUM(cost_usd) as total_cost,
                    AVG(execution_time_ms) as avg_time
                FROM ai_operation_logs 
                WHERE user_id = :user_id 
                AND timestamp > NOW() - INTERVAL ':days days'
                GROUP BY operation_type
            """),
            {"user_id": user_id, "days": days}
        )
        return result.fetchall()
    
    @staticmethod
    async def get_agent_performance(db: AsyncSession, agent_id: int):
        """Get performance metrics for an AI agent"""
        result = await db.execute(
            text("""
                SELECT 
                    model_id,
                    COUNT(*) as executions,
                    AVG(execution_time_ms) as avg_time,
                    AVG(total_tokens) as avg_tokens,
                    COUNT(CASE WHEN level = 'ERROR' THEN 1 END) as errors
                FROM ai_operation_logs 
                WHERE agent_id = :agent_id
                GROUP BY model_id
            """),
            {"agent_id": agent_id}
        )
        return result.fetchall()

# Usage in API endpoints
@router.get("/admin/ai-logs/user/{user_id}/summary")
async def get_user_ai_summary(
    user_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    summary = await AILogService.get_user_ai_activity(db, user_id, days)
    return {"user_id": user_id, "period_days": days, "activity": summary}
```

#### Dashboard Queries for Analytics
```python
# Real-time monitoring queries
class AIMonitoringQueries:
    @staticmethod
    async def get_current_error_rate(db: AsyncSession, hours: int = 1):
        """Get error rate in the last N hours"""
        result = await db.execute(
            text("""
                SELECT 
                    COUNT(CASE WHEN level = 'ERROR' THEN 1 END)::float / COUNT(*) as error_rate
                FROM ai_operation_logs 
                WHERE timestamp > NOW() - INTERVAL ':hours hours'
            """),
            {"hours": hours}
        )
        return result.scalar()
    
    @staticmethod
    async def get_model_performance_trends(db: AsyncSession, days: int = 7):
        """Get performance trends by model"""
        result = await db.execute(
            text("""
                SELECT 
                    model_id,
                    DATE_TRUNC('hour', timestamp) as hour,
                    AVG(execution_time_ms) as avg_time,
                    COUNT(*) as operations
                FROM ai_operation_logs 
                WHERE timestamp > NOW() - INTERVAL ':days days'
                GROUP BY model_id, DATE_TRUNC('hour', timestamp)
                ORDER BY hour, model_id
            """),
            {"days": days}
        )
        return result.fetchall()
```

#### Log Processing for Insights
```python
# Batch processing for insights
class AILogAnalyzer:
    @staticmethod
    async def analyze_prompt_effectiveness(db: AsyncSession):
        """Analyze which prompts lead to better performance"""
        # Get writer operations with their outcomes
        result = await db.execute(
            text("""
                SELECT 
                    input_data->>'personality_prompt' as prompt,
                    AVG(execution_time_ms) as avg_time,
                    AVG(LENGTH(output_data->>'generated_content')) as avg_content_length,
                    COUNT(*) as usage_count
                FROM ai_operation_logs 
                WHERE operation_type = 'writer'
                AND input_data->>'personality_prompt' IS NOT NULL
                GROUP BY input_data->>'personality_prompt'
                HAVING COUNT(*) >= 5
                ORDER BY avg_content_length DESC
            """)
        )
        return result.fetchall()
    
    @staticmethod
    async def detect_anomalies(db: AsyncSession):
        """Detect unusual patterns in AI operations"""
        # Find operations that took unusually long
        result = await db.execute(
            text("""
                WITH avg_times AS (
                    SELECT 
                        model_id,
                        operation_type,
                        AVG(execution_time_ms) as avg_time,
                        STDDEV(execution_time_ms) as stddev_time
                    FROM ai_operation_logs 
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                    GROUP BY model_id, operation_type
                )
                SELECT l.*, a.avg_time, a.stddev_time
                FROM ai_operation_logs l
                JOIN avg_times a ON l.model_id = a.model_id AND l.operation_type = a.operation_type
                WHERE l.execution_time_ms > a.avg_time + (2 * a.stddev_time)
                AND l.timestamp > NOW() - INTERVAL '24 hours'
                ORDER BY l.execution_time_ms DESC
            """)
        )
                 return result.fetchall()
```

#### Monitoring LLM Quality & Parsing Issues
```python
# Quality monitoring queries
class AIQualityMonitor:
    @staticmethod
    async def get_parsing_failure_rate(db: AsyncSession, hours: int = 24):
        """Get rate of parsing failures in judge operations"""
        result = await db.execute(
            text("""
                SELECT 
                    COUNT(CASE WHEN output_data->>'parsing_success' = 'false' THEN 1 END)::float / 
                    COUNT(*) as failure_rate,
                    COUNT(*) as total_operations
                FROM ai_operation_logs 
                WHERE operation_type = 'judge'
                AND timestamp > NOW() - INTERVAL ':hours hours'
            """),
            {"hours": hours}
        )
        return result.fetchone()
    
    @staticmethod
    async def get_common_parsing_errors(db: AsyncSession, days: int = 7):
        """Get most common parsing error types"""
        result = await db.execute(
            text("""
                SELECT 
                    jsonb_array_elements(parsing_errors)->>'error_type' as error_type,
                    COUNT(*) as occurrence_count
                FROM ai_operation_logs 
                WHERE operation_type = 'judge'
                AND parsing_errors IS NOT NULL
                AND jsonb_array_length(parsing_errors) > 0
                AND timestamp > NOW() - INTERVAL ':days days'
                GROUP BY jsonb_array_elements(parsing_errors)->>'error_type'
                ORDER BY occurrence_count DESC
            """),
            {"days": days}
        )
        return result.fetchall()
    
    @staticmethod
    async def get_problematic_prompts(db: AsyncSession):
        """Find prompts that frequently lead to parsing failures"""
        result = await db.execute(
            text("""
                SELECT 
                    input_data->>'personality_prompt' as prompt,
                    COUNT(*) as total_uses,
                    COUNT(CASE WHEN output_data->>'parsing_success' = 'false' THEN 1 END) as failures,
                    (COUNT(CASE WHEN output_data->>'parsing_success' = 'false' THEN 1 END)::float / COUNT(*)) as failure_rate
                FROM ai_operation_logs 
                WHERE operation_type = 'judge'
                AND input_data->>'personality_prompt' IS NOT NULL
                GROUP BY input_data->>'personality_prompt'
                HAVING COUNT(*) >= 5
                ORDER BY failure_rate DESC, total_uses DESC
            """)
        )
        return result.fetchall()

# API endpoint for quality monitoring
@router.get("/admin/ai-logs/quality-report")
async def get_ai_quality_report(
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    failure_rate = await AIQualityMonitor.get_parsing_failure_rate(db, hours)
    common_errors = await AIQualityMonitor.get_common_parsing_errors(db, 7)
    problematic_prompts = await AIQualityMonitor.get_problematic_prompts(db)
    
    return {
        "period_hours": hours,
        "parsing_failure_rate": failure_rate.failure_rate if failure_rate else 0,
        "total_operations": failure_rate.total_operations if failure_rate else 0,
        "common_errors": common_errors,
        "problematic_prompts": problematic_prompts[:10]  # Top 10
    }
```

### 9. Future Enhancements

- **Real-time Monitoring**: Dashboard for live AI operations
- **Analytics**: Usage patterns and performance trends
- **Alerting**: Notifications for errors or unusual patterns
- **Integration**: Export to external monitoring systems

## Next Steps

1. **Review and Approve** this proposal
2. **Phase 1 Implementation**: Create core logging infrastructure
3. **Testing**: Verify logging works correctly
4. **Gradual Rollout**: Enable logging in development first
5. **Production Deployment**: Enable with appropriate privacy settings

## Questions for Discussion

1. **Environment Configuration**: How do you distinguish dev/staging/production? (Environment variables, config files, etc.)
2. **Privacy Level**: What level of content logging is acceptable in production?
3. **Raw LLM Data**: Should we store complete LLM requests/responses in production?
4. **Parsing Failures**: How should we handle/alert on LLM hallucinations and parsing failures?
5. **Retention**: How long should logs be kept? (Suggested: 90 days)
6. **Access**: Who should have access to AI logs? (Admin only, or specific roles?)
7. **Performance**: Any concerns about logging overhead?
8. **Alerting**: Should we set up alerts for high parsing failure rates? 