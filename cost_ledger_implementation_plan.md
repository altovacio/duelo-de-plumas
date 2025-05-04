# Cost Ledger Implementation Plan

## 1. Goal

To ensure that the history of AI-related costs (both real monetary cost, if tracked, and user credit consumption) is preserved even when associated `User` or `Contest` records are deleted. This provides a persistent audit trail for accountability and monitoring.

## 2. New Model (`CostLedger`)

We will introduce a new table/model in `backend/models.py`.

```python
# backend/models.py

# ... other imports ...
from sqlalchemy import Numeric # For potential currency/precise cost

class CostLedger(Base):
    __tablename__ = 'cost_ledger'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign Key to User - Decide on ON DELETE behavior:
    # Option A: Keep user_id even if user is deleted (Requires NO database constraint)
    #   - Pro: Always know who spent it. Con: Potential for stale IDs if user is purged later.
    # Option B: Set user_id to NULL if user is deleted (Requires nullable=True and DB ON DELETE SET NULL)
    #   - Pro: Cleaner data state. Con: Lose direct link if user is deleted.
    # Recommended: Option A for accountability, ensure FK constraint is NOT added by Alembic, or added with NO ACTION.
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False) # Or ForeignKey('user.id', ondelete='SET NULL') ?
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
    
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # e.g., 'ai_evaluate', 'ai_generate', 'admin_credit_assign', 'initial_credit'
    
    credits_change: Mapped[int] = mapped_column(Integer, nullable=False) # Amount credits changed by (negative for deduction, positive for assignment)
    
    # Optional: Track real cost if available/needed
    real_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Or Numeric for precision
    
    # Store context about the action
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # e.g., "Evaluation for Contest 123", "Generation by Writer 45"
    
    # Reference to the specific entity triggering the cost (optional but helpful)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # e.g., 'contest', 'ai_evaluation', 'ai_writing_request', 'user_ai_judge', 'user_ai_writer'
    related_entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Store the resulting credit balance after the transaction (optional, for easier history view)
    resulting_balance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self):
        return f'<CostLedger {self.id}: User {self.user_id}, Action {self.action_type}, Change {self.credits_change}>'

```

**Decision:** Need to finalize the `ondelete` behavior for `user_id`. For maximum accountability, keeping the `user_id` even after user deletion seems preferable. This means we should ensure Alembic *doesn't* add a foreign key constraint with cascade or set null behavior for this specific column, or added with NO ACTION.

## 3. New Schemas

Define corresponding Pydantic schemas in `backend/schemas.py`.

```python
# backend/schemas.py

# ... other imports ...

class CostLedgerBase(BaseModel):
    user_id: int
    timestamp: datetime
    action_type: str
    credits_change: int
    real_cost: Optional[float] = None
    description: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    resulting_balance: Optional[int] = None

# Schema for reading ledger entries (e.g., for admin view)
class CostLedgerRead(CostLedgerBase):
    id: int
    
    model_config = {
        "from_attributes": True
    }

# Potentially needed if creating ledger entries directly via API (unlikely?)
# class CostLedgerCreate(CostLedgerBase):
#    pass 

```

## 4. Database Migrations

*   Run `alembic revision --autogenerate -m "Add cost_ledger table"` after defining the model.
*   **Carefully review** the generated migration script, especially the definition of the `user_id` column and any foreign key constraints automatically added. Adjust if necessary to achieve the desired `ON DELETE` behavior (likely removing the FK constraint or setting `ondelete='NO ACTION'`).
*   Run `alembic upgrade head` to apply the migration.

## 5. Endpoint Modifications

### 5.1. AI Action Endpoints (`/ai-writers/{writer_id}/generate`, `/ai-judges/{judge_id}/evaluate`) [Implemented - Placeholders]
### 5.1. AI Action Endpoints (`/ai-writers/{writer_id}/generate`, `/ai-judges/{judge_id}/evaluate`) [Implemented]

*   Located in `backend/app/routers/ai_agents.py`.
*   **Logic Update:**
    1.  Perform existing checks (ownership).
    2.  **Start transaction.**
    3.  Fetch the user with `select...for_update()`.
    4.  **(Optional) Pre-check credits.** (Currently skipped in implementation, relies on post-check)
    5.  Execute the AI service call (`perform_ai_generation` or `perform_ai_evaluation`).
    6.  If successful:
        *   Calculate `actual_credit_cost` and `real_cost` from service result.
        *   **Atomically (within the DB transaction):**
            *   Fetch the user with `select...for_update()`. # Already fetched and locked
            *   Verify `user.credits >= actual_credit_cost` (after AI call). Raise 402 if check fails.
            *   Update `user.credits = user.credits - actual_credit_cost`.
            *   Create `CostLedger` entry:
                *   `user_id = user.id`
                *   `action_type = 'ai_generate' / 'ai_evaluate'`
                *   `credits_change = -actual_credit_cost`
                *   `real_cost = calculated_real_cost`
                *   `description = f"Generation using writer {writer_id}..."` (or similar)
                *   `related_entity_type = 'user_ai_writer' / 'user_ai_judge'`
                *   `related_entity_id = writer_id / judge_id`
                *   `resulting_balance = user.credits` (after deduction)
            *   Add the new `CostLedger` record to the session (`db.add(ledger_entry)`).
            *   Add the updated `User` record to the session (`db.add(user)`).
            *   **If evaluation, Vote objects are already added to the session by the service.**
            *   Commit the transaction (`await db.commit()`).
    7.  Return success response (containing generated text or evaluation status, cost info).
    8.  **If AI service call fails or insufficient credits:**
        *   **Rollback transaction automatically via `finally` block.**
        *   Return appropriate error response (e.g., 500, 503, 402).

### 5.2. Admin Credit Management (`PUT /admin/users/{user_id}/credits`) [Implemented]

*   Located in `backend/app/routers/admin.py`.
*   **Logic Update:**
    1.  Validate input (e.g., positive credit amount for additions).
    2.  Fetch user.
    3.  Calculate the `credit_change` amount.
    4.  Update `user.credits`.
    5.  **Create `CostLedger` entry:**
        *   `user_id = user.id`
        *   `action_type = 'admin_credit_adjust'` (or 'admin_credit_set')
        *   `credits_change = calculated_credit_change` (can be positive or negative if setting absolute value)
        *   `description = f"Admin {current_admin.username} adjusted credits."`
        *   `resulting_balance = user.credits` (after adjustment)
    6.  Add user and ledger entry to session, commit.
    7.  Return updated user info.

### 5.3. Admin Cost/Consumption Monitoring

*   **`GET /admin/ai-costs-summary` [Updated]:** Modify this endpoint to primarily query the `CostLedger` table for `real_cost` aggregation based on `action_type` ('ai\_evaluate', 'ai\_generate'). Continue querying `AIEvaluation` / `AIWritingRequest` for token counts and recent records as needed by the `AICostsSummary` schema. The financial source of truth is the ledger.
*   **New Endpoint: `GET /admin/users/{user_id}/credit-history` [Implemented]:** Create a new endpoint to retrieve the `CostLedger` records for a specific `user_id`, ordered by `timestamp`. This provides the detailed consumption history.
*   **Existing Endpoint: `GET /admin/users/` & `GET /auth/users/me`:** These should continue fetching the current `user.credits` balance directly from the `User` model for efficiency, as this value is kept up-to-date by the action/adjustment endpoints. The ledger is for the *history*.

## 6. User Credit Balance

*   The `User.credits` field remains the primary source for checking the *current* balance quickly within endpoints before executing actions.
*   The `CostLedger` table provides the historical record of *how* that balance changed.

## 7. Frontend Impact

*   User profile/dashboard needs to display the `credits` field from `/auth/users/me`.
*   Admin user management interface needs to display credits and provide UI for the `/admin/users/{user_id}/credits` endpoint.
*   Admin cost monitoring pages need to be updated to potentially display data from the new `/admin/users/{user_id}/credit-history` endpoint and the revised `/admin/ai-costs-summary`. 