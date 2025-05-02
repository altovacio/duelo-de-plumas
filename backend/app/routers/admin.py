from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
# ADD: AI Client imports for trigger endpoint
import openai
import anthropic
from ..dependencies import get_openai_client, get_anthropic_client
# ADD: AI Service import
from ..services import ai_services

# Correct relative imports for modules two levels up
from ... import schemas, models
from ...database import get_db_session
from ... import security
# ADD: Import AI Schema
from ..schemas.ai_schemas import GenerateTextResponse

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(security.require_admin)]
)

# --- AI Writer Management ---

@router.get("/ai-writers", response_model=List[schemas.AIWriterAdminView])
async def admin_list_ai_writers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all configured AI Writers."""
    result = await db.execute(
        select(models.AIWriter)
        .order_by(models.AIWriter.name)
        .offset(skip)
        .limit(limit)
    )
    writers = result.scalars().all()
    return writers

@router.post("/ai-writers", response_model=schemas.AIWriterAdminView, status_code=status.HTTP_201_CREATED)
async def admin_create_ai_writer(
    writer_data: schemas.AIWriterCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Creates a new AI Writer."""
    existing_writer = await db.scalar(select(models.AIWriter).where(models.AIWriter.name == writer_data.name))
    if existing_writer:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"AI Writer with name '{writer_data.name}' already exists.")
    new_writer = models.AIWriter(**writer_data.model_dump())
    db.add(new_writer)
    await db.commit()
    await db.refresh(new_writer)
    return new_writer

@router.get("/ai-writers/{writer_id}", response_model=schemas.AIWriterAdminView)
async def admin_get_ai_writer(
    writer_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Gets details of a specific AI Writer."""
    writer = await db.get(models.AIWriter, writer_id)
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")
    return writer

@router.put("/ai-writers/{writer_id}", response_model=schemas.AIWriterAdminView)
async def admin_update_ai_writer(
    writer_id: int,
    writer_update: schemas.AIWriterUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Updates an existing AI Writer."""
    writer = await db.get(models.AIWriter, writer_id)
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")
    update_data = writer_update.model_dump(exclude_unset=True)
    if 'name' in update_data and update_data['name'] != writer.name:
        existing_writer = await db.scalar(select(models.AIWriter).where(models.AIWriter.name == update_data['name']))
        if existing_writer:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"AI Writer with name '{update_data['name']}' already exists.")
    for field, value in update_data.items():
        setattr(writer, field, value)
    db.add(writer)
    await db.commit()
    await db.refresh(writer)
    return writer

@router.delete("/ai-writers/{writer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_ai_writer(
    writer_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Deletes an AI Writer."""
    writer = await db.get(models.AIWriter, writer_id)
    if not writer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Writer not found")
    await db.delete(writer)
    await db.commit()
    return None

# --- Contest Judge Assignment ---

@router.post("/contests/{contest_id}/judges/{judge_id}", status_code=status.HTTP_201_CREATED, summary="Assign Judge to Contest")
async def admin_assign_judge_to_contest(
    contest_id: int,
    judge_id: int,
    assignment_data: schemas.AssignJudgeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Assigns a judge (human or AI) to a specific contest."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    judge = await db.get(models.User, judge_id)
    if not judge or judge.role != 'judge':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Judge not found or user is not a judge")
    ai_model = assignment_data.ai_model
    if judge.is_ai_judge() and not ai_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An ai_model must be specified when assigning an AI judge.")
    if not judge.is_ai_judge():
        ai_model = None
    
    # TODO: Validate ai_model against available models from config/ai_params.py?

    existing_assignment_result = await db.execute(
        select(models.contest_judges)
        .where(models.contest_judges.c.contest_id == contest_id)
        .where(models.contest_judges.c.user_id == judge_id)
    )
    existing_assignment = existing_assignment_result.first()
    if existing_assignment:
        if judge.is_ai_judge() and existing_assignment.ai_model != ai_model:
            stmt = (
                models.contest_judges.update()
                .where(models.contest_judges.c.contest_id == contest_id)
                .where(models.contest_judges.c.user_id == judge_id)
                .values(ai_model=ai_model)
            )
            await db.execute(stmt)
            await db.commit()
            return {"message": f"AI Judge {judge.username} model updated for contest {contest.title}"}
        else:
            return {"message": f"Judge {judge.username} already assigned to contest {contest.title}"}
    try:
        insert_stmt = models.contest_judges.insert().values(
            contest_id=contest_id,
            user_id=judge_id,
            ai_model=ai_model
        )
        await db.execute(insert_stmt)
        await db.commit()
        return {"message": f"Judge {judge.username} assigned to contest {contest.title}"} 
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to assign judge: {e}")

@router.delete("/contests/{contest_id}/judges/{judge_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Unassign Judge from Contest")
async def admin_unassign_judge_from_contest(
    contest_id: int,
    judge_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Removes a judge assignment from a contest."""
    existing_assignment = await db.execute(
        select(models.contest_judges.c.user_id)
        .where(models.contest_judges.c.contest_id == contest_id)
        .where(models.contest_judges.c.user_id == judge_id)
    )
    if not existing_assignment.first():
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Judge assignment not found for this contest")
    try:
        delete_stmt = models.contest_judges.delete().where(
            models.contest_judges.c.contest_id == contest_id,
            models.contest_judges.c.user_id == judge_id
        )
        await db.execute(delete_stmt)
        await db.commit()
        return None
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to unassign judge: {e}")

# --- Contest Status/Password Management ---

@router.put("/contests/{contest_id}/status", response_model=schemas.ContestPublic, summary="Set Contest Status")
async def admin_set_contest_status(
    contest_id: int,
    status_data: schemas.ContestSetStatusRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Manually sets the status of a contest."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    contest.status = status_data.status
    db.add(contest)
    await db.commit()
    await db.refresh(contest)
    return contest

@router.put("/contests/{contest_id}/reset-password", status_code=status.HTTP_200_OK, summary="Reset Private Contest Password")
async def admin_reset_contest_password(
    contest_id: int,
    password_data: schemas.ContestResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Sets a new password for a private contest."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    if contest.contest_type != 'private':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot set password for a public contest.")
    contest.set_password(password_data.new_password)
    db.add(contest)
    await db.commit()
    return {"message": "Contest password reset successfully"}

# --- AI Judge Management (Users with judge_type='ai') ---

@router.get("/ai-judges", response_model=List[schemas.AIJudgeAdminView])
async def admin_list_ai_judges(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all AI Judge users."""
    result = await db.execute(
        select(models.User)
        .where(models.User.role == 'judge', models.User.judge_type == 'ai')
        .order_by(models.User.username)
        .offset(skip)
        .limit(limit)
    )
    ai_judges = result.scalars().all()
    return ai_judges

@router.post("/ai-judges", response_model=schemas.AIJudgeAdminView, status_code=status.HTTP_201_CREATED)
async def admin_create_ai_judge(
    judge_data: schemas.AIJudgeCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Creates a new AI Judge user."""
    existing_user = await db.scalar(select(models.User).where(models.User.username == judge_data.username))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    existing_email = await db.scalar(select(models.User).where(models.User.email == judge_data.email))
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    new_judge = models.User(
        username=judge_data.username,
        email=judge_data.email,
        ai_personality_prompt=judge_data.ai_personality_prompt,
        role='judge',
        judge_type='ai'
    )
    new_judge.set_password(judge_data.password)
    db.add(new_judge)
    await db.commit()
    await db.refresh(new_judge)
    return new_judge

@router.get("/ai-judges/{judge_id}", response_model=schemas.AIJudgeAdminView)
async def admin_get_ai_judge(
    judge_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Gets details of a specific AI Judge user."""
    judge = await db.scalar(select(models.User).where(models.User.id == judge_id, models.User.judge_type == 'ai'))
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")
    return judge

@router.put("/ai-judges/{judge_id}", response_model=schemas.AIJudgeAdminView)
async def admin_update_ai_judge(
    judge_id: int,
    judge_update: schemas.AIJudgeUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Updates an existing AI Judge user."""
    judge = await db.scalar(select(models.User).where(models.User.id == judge_id, models.User.judge_type == 'ai'))
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")
    update_data = judge_update.model_dump(exclude_unset=True)
    password = update_data.pop("password", None)
    if 'username' in update_data and update_data['username'] != judge.username:
        existing = await db.scalar(select(models.User).where(models.User.username == update_data['username']))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    if 'email' in update_data and update_data['email'] != judge.email:
        existing = await db.scalar(select(models.User).where(models.User.email == update_data['email']))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    for field, value in update_data.items():
        setattr(judge, field, value)
    if password:
        judge.set_password(password)
    db.add(judge)
    await db.commit()
    await db.refresh(judge)
    return judge

@router.delete("/ai-judges/{judge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_ai_judge(
    judge_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Deletes an AI Judge user."""
    judge = await db.scalar(select(models.User).where(models.User.id == judge_id, models.User.judge_type == 'ai'))
    if not judge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Judge not found")
    assigned_contests = await db.scalar(select(func.count(models.contest_judges.c.contest_id)).where(models.contest_judges.c.user_id == judge_id))
    if assigned_contests > 0:
         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot delete AI Judge {judge.username} as they are assigned to {assigned_contests} contest(s). Remove assignments first.")
    await db.delete(judge)
    await db.commit()
    return None

# --- AI Evaluation Info ---

@router.get("/ai-evaluations", response_model=List[schemas.AIEvaluationPublic], summary="List AI Evaluations")
async def admin_list_ai_evaluations(
    contest_id: Optional[int] = None,
    judge_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Lists AI evaluation records, optionally filtered."""
    stmt = select(models.AIEvaluation).order_by(models.AIEvaluation.timestamp.desc())
    if contest_id:
        stmt = stmt.where(models.AIEvaluation.contest_id == contest_id)
    if judge_id:
        stmt = stmt.where(models.AIEvaluation.judge_id == judge_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    evaluations = result.scalars().all()
    return evaluations

@router.get("/ai-evaluations/{evaluation_id}", response_model=schemas.AIEvaluationDetail, summary="Get AI Evaluation Details")
async def admin_get_ai_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Gets the full details of a specific AI evaluation record."""
    evaluation = await db.get(models.AIEvaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Evaluation record not found")
    return evaluation

# --- AI Writer Submission Trigger ---

@router.post("/contests/{contest_id}/ai-submission", response_model=GenerateTextResponse, summary="Trigger AI Submission")
async def admin_trigger_ai_submission(
    contest_id: int,
    submission_request: schemas.TriggerAISubmissionRequest,
    db: AsyncSession = Depends(get_db_session),
    openai_client: openai.AsyncOpenAI | None = Depends(get_openai_client),
    anthropic_client: anthropic.AsyncAnthropic | None = Depends(get_anthropic_client)
):
    """Triggers an AI Writer to generate and submit text for a contest."""
    contest = await db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    if contest.status != 'open':
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Contest status is '{contest.status}', must be 'open' to submit.")
    result = await ai_services.generate_text(
        session=db,
        contest_id=contest_id,
        ai_writer_id=submission_request.ai_writer_id,
        model_id=submission_request.model_id,
        title=submission_request.title,
        openai_client=openai_client,
        anthropic_client=anthropic_client
    )
    if not result.get("success"): 
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = result.get("message", "Failed to generate AI submission.")
        if "not found" in detail.lower(): status_code = status.HTTP_404_NOT_FOUND
        elif "not open" in detail.lower(): status_code = status.HTTP_400_BAD_REQUEST
        elif "error calling ai api" in detail.lower(): status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        raise HTTPException(status_code=status_code, detail=detail)
    return result

# --- Submission Management (Ensure correct placement) ---

@router.delete("/submissions/{submission_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Submission")
async def admin_delete_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Deletes a specific submission and its associated votes (due to cascade)."""
    submission = await db.get(models.Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    await db.delete(submission)
    await db.commit()
    return None

# --- Other Admin Endpoints (Placeholders) ---
# TODO: Implement endpoints for:
# - Listing/Managing Users (Human Judges, Admins)
# - Overriding Contest status/passwords (Partially done)
# - Viewing detailed AI evaluation costs/logs (Partially done)
# - Triggering AI submissions for contests (Done)
