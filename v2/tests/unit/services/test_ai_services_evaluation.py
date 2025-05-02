import pytest
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from sqlalchemy.ext.asyncio import AsyncSession
# Removed Table, Column imports as we won't mock them directly this way
import openai
import anthropic

# Assuming the service file is in v2/app/services/ai_services.py
from v2.app.services.ai_services import run_ai_evaluation

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# --- Mock Models & Data ---

# Use simple MagicMocks for patching the model classes now
MockContest = MagicMock()
MockUser = MagicMock()
MockSubmission = MagicMock()
MockVote = MagicMock()
MockAIEvaluation = MagicMock()
MockContestJudgesTable = MagicMock() # Mock for the table object

@pytest.fixture
def mock_session():
    """Fixture for a mocked async database session."""
    # Session mock remains the same
    session = AsyncMock(spec=AsyncSession)
    session.get = AsyncMock()
    session.execute = AsyncMock()
    session.scalars = AsyncMock()
    session.add = MagicMock() 
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session

@pytest.fixture
def mock_openai_client():
    """Fixture for a mocked async OpenAI client."""
    return AsyncMock(spec=openai.AsyncOpenAI)

@pytest.fixture
def mock_anthropic_client():
    """Fixture for a mocked async Anthropic client."""
    return AsyncMock(spec=anthropic.AsyncAnthropic)

# Patch the model imports within the service module for all tests in this file
@pytest.fixture(autouse=True)
def patch_models():
    # Patch model names with simple MagicMocks using nested with statements
    # Use create=True in case the import failed in the service module
    with patch('v2.app.services.ai_services.Contest', MockContest, create=True):
        with patch('v2.app.services.ai_services.User', MockUser, create=True):
            with patch('v2.app.services.ai_services.Submission', MockSubmission, create=True):
                with patch('v2.app.services.ai_services.Vote', MockVote, create=True):
                    with patch('v2.app.services.ai_services.AIEvaluation', MockAIEvaluation, create=True):
                        with patch('v2.app.services.ai_services.contest_judges', MockContestJudgesTable, create=True):
                            yield # Allows tests to run with patches active

# --- Tests for run_ai_evaluation --- 

# Mock the SQLAlchemy query functions used within the service
@patch('v2.app.services.ai_services.select', return_value=MagicMock()) 
@patch('v2.app.services.ai_services.delete', return_value=MagicMock())
@patch('v2.app.services.ai_services.construct_judge_prompt', return_value="Mock Prompt")
@patch('v2.app.services.ai_services.call_ai_api')
@patch('v2.app.services.ai_services.parse_ai_judge_response', return_value=[(101, 1, "Comment 1"), (102, 2, "Comment 2")])
async def test_run_ai_evaluation_success(
    mock_parse, mock_call_api, mock_construct_prompt, mock_delete, mock_select,
    mock_session, mock_openai_client, mock_anthropic_client
):
    # Arrange: Mock DB *results*
    # Create mock instances just for data holding if needed by the function logic
    mock_contest_instance = MagicMock(id=1, title="Test Contest")
    mock_judge_instance = MagicMock(id=5, username="AIJudge", is_ai_judge=MagicMock(return_value=True), ai_personality_prompt="Pers")
    mock_submission_instances = [MagicMock(id=101), MagicMock(id=102)]
    mock_assignment = MagicMock()
    mock_assignment.ai_model = 'test-model-id'
    mock_existing_eval = None # Simulate no existing evaluation
    
    mock_session.get.side_effect = [mock_contest_instance, mock_judge_instance]
    
    # Mock the result of session.execute(select(...)).first() for judge assignment
    mock_execute_result_assign = MagicMock() # The result object itself is not async
    mock_execute_result_assign.first.return_value = mock_assignment # .first() is sync
    # Mock the result of session.execute(delete(...))
    mock_execute_result_delete = MagicMock() # delete doesn't usually return useful data
    mock_session.execute.side_effect = [mock_execute_result_assign, mock_execute_result_delete]
    
    # Mock the result of session.scalars(select(...)).all() for submissions
    mock_scalars_result_subs = MagicMock() # Result object is not async
    mock_scalars_result_subs.all.return_value = mock_submission_instances # .all() is sync
    # Mock the result of session.scalars(select(...)).first() for existing evaluation
    mock_scalars_result_eval = MagicMock()
    mock_scalars_result_eval.first.return_value = mock_existing_eval # .first() is sync
    mock_session.scalars.side_effect = [mock_scalars_result_subs, mock_scalars_result_eval]
    
    # Mock API call result
    mock_call_api.return_value = {
        'success': True, 'response_text': "AI Response", 'cost': 0.01,
        'prompt_tokens': 100, 'completion_tokens': 50, 'error_message': None
    }
    
    # Mock the AIEvaluation instantiation
    # Patching the class means MockAIEvaluation is the class used
    # We need to control what happens when it's instantiated
    mock_eval_instance = MagicMock(spec=MockAIEvaluation) # Use the patched name
    mock_eval_instance.id = 999
    MockAIEvaluation.return_value = mock_eval_instance 

    # Act
    result = await run_ai_evaluation(
        contest_id=1, judge_id=5, session=mock_session, 
        openai_client=mock_openai_client, anthropic_client=mock_anthropic_client
    )
    
    # Assert
    assert result['success'] is True
    assert result['message'] == "AI evaluation completed successfully. Created 2 vote records."
    assert result['cost'] == 0.01
    assert result['evaluation_id'] == 999 
    assert result['votes_created'] == 2
    assert result['is_reevaluation'] is False
    
    # Check functions were called
    mock_session.get.assert_any_call(MockContest, 1)
    mock_session.get.assert_any_call(MockUser, 5)
    mock_select.assert_called() # Ensure select was called 
    mock_construct_prompt.assert_called_once_with(mock_contest_instance, mock_judge_instance, mock_submission_instances)
    mock_call_api.assert_awaited_once()
    mock_parse.assert_called_once_with("AI Response", mock_submission_instances)
    
    # Check DB writes
    assert mock_session.add.call_count == 3 
    mock_session.flush.assert_awaited() 
    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_not_awaited()
    mock_session.delete.assert_not_awaited()
    MockAIEvaluation.assert_called_once() # Check class was instantiated
    assert MockVote.call_count == 2 # Check Vote class was instantiated twice

# Patch query functions for the failure test too
@patch('v2.app.services.ai_services.select', return_value=MagicMock()) 
@patch('v2.app.services.ai_services.delete', return_value=MagicMock())
@patch('v2.app.services.ai_services.construct_judge_prompt')
@patch('v2.app.services.ai_services.call_ai_api')
@patch('v2.app.services.ai_services.parse_ai_judge_response')
async def test_run_ai_evaluation_api_failure(
    mock_parse, mock_call_api, mock_construct_prompt, mock_delete, mock_select,
    mock_session, mock_openai_client, mock_anthropic_client
):
    # Arrange: Mock DB results
    mock_contest_instance = MagicMock(id=1, title="Test Contest")
    mock_judge_instance = MagicMock(id=5, username="AIJudge", is_ai_judge=MagicMock(return_value=True))
    mock_submission_instances = [MagicMock(id=101)]
    mock_assignment = MagicMock()
    mock_assignment.ai_model = 'test-model-id'
    mock_existing_eval = None
    
    mock_session.get.side_effect = [mock_contest_instance, mock_judge_instance]
    mock_execute_result_assign = MagicMock() 
    mock_execute_result_assign.first.return_value = mock_assignment 
    mock_session.execute.return_value = mock_execute_result_assign
    mock_scalars_result_subs = MagicMock() 
    mock_scalars_result_subs.all.return_value = mock_submission_instances
    mock_scalars_result_eval = MagicMock()
    mock_scalars_result_eval.first.return_value = mock_existing_eval
    mock_session.scalars.side_effect = [mock_scalars_result_subs, mock_scalars_result_eval]
    
    # Mock API call failure
    mock_call_api.return_value = {
        'success': False, 'response_text': "Error: API Down", 'cost': 0.001,
        'prompt_tokens': 10, 'completion_tokens': 0, 'error_message': "API Down"
    }
    
    # Act
    result = await run_ai_evaluation(
        contest_id=1, judge_id=5, session=mock_session, 
        openai_client=mock_openai_client, anthropic_client=mock_anthropic_client
    )
    
    # Assert
    assert result['success'] is False
    assert "Error calling AI API: API Down" in result['message']
    assert result['cost'] == 0.001 
    mock_construct_prompt.assert_called_once()
    mock_call_api.assert_awaited_once()
    mock_parse.assert_not_called() 
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_awaited()
    mock_session.rollback.assert_awaited_once() 

# Add more tests for other scenarios:
# - Contest/Judge not found
# - Judge not AI judge
# - Judge not assigned / No model ID
# - No submissions found
# - Re-evaluation case (existing evaluation found and deleted)
# - Parsing returns empty results
# - Unexpected exception during execution 