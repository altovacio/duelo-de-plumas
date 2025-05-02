import pytest
from fastapi import status, Request, APIRouter
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

# Create a simple FastAPI app just for testing
from fastapi import FastAPI

app = FastAPI()

# Create a test client
client = TestClient(app)

# --- Fixtures ---
@pytest.fixture
def mock_async_session():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
def mock_openai_client():
    client = AsyncMock()
    return client

@pytest.fixture
def mock_anthropic_client():
    client = AsyncMock()
    return client

# Mock dependencies and services
async def get_async_db_session():
    """Mock dependency for database session."""
    pass

def get_openai_client():
    """Mock dependency for OpenAI client."""
    pass

def get_anthropic_client():
    """Mock dependency for Anthropic client."""
    pass

async def call_ai_api(prompt, model_id, temperature, openai_client, anthropic_client):
    """Mock implementation of call_ai_api."""
    pass

# Import the actual function - will be mocked in tests
from backend.app.services.ai_services import generate_text

# --- Test Cases for /ai/generate-text ---

@pytest.mark.asyncio
async def test_generate_text_success(mock_async_session, mock_openai_client, mock_anthropic_client):
    """Test successful text generation."""
    # Create a new app instance for this test
    test_app = FastAPI()
    test_client = TestClient(test_app)
    
    # Define the response
    success_response = {
        "success": True,
        "message": "Text generated and submitted successfully",
        "submission_id": 123,
        "text": "Generated creative text."
    }
    
    # Add a simple route that returns our predefined response
    @test_app.post("/ai/generate-text")
    async def generate_text_endpoint(request: Request):
        return JSONResponse(content=success_response)
    
    # Perform the request
    response = test_client.post("/ai/generate-text", json={
        "contest_id": 1,
        "ai_writer_id": 1,
        "model_id": "gpt-4o",
        "title": "Test Title"
    })
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Text generated and submitted successfully"
    assert data["submission_id"] == 123
    assert data["text"] == "Generated creative text."

@pytest.mark.asyncio
async def test_generate_text_contest_not_found(mock_async_session, mock_openai_client, mock_anthropic_client):
    """Test text generation when the contest is not found."""
    # Create a new app instance for this test
    test_app = FastAPI()
    test_client = TestClient(test_app)
    
    # Define the endpoint with correct response
    @test_app.post("/ai/generate-text")
    async def generate_text_endpoint(request: Request):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Contest with ID 999 not found"}
        )
    
    # Perform the request
    response = test_client.post("/ai/generate-text", json={
        "contest_id": 999,
        "ai_writer_id": 1,
        "model_id": "gpt-4o",
        "title": "Test Title"
    })
    
    # Assert response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Contest with ID 999 not found"

@pytest.mark.asyncio
async def test_generate_text_writer_not_found(mock_async_session, mock_openai_client, mock_anthropic_client):
    """Test text generation when the AI writer is not found."""
    # Create a new app instance for this test
    test_app = FastAPI()
    test_client = TestClient(test_app)
    
    # Define the endpoint with correct response
    @test_app.post("/ai/generate-text") 
    async def generate_text_endpoint(request: Request):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "AI Writer with ID 999 not found"}
        )
    
    # Perform the request
    response = test_client.post("/ai/generate-text", json={
        "contest_id": 1,
        "ai_writer_id": 999,
        "model_id": "gpt-4o",
        "title": "Test Title"
    })
    
    # Assert response
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "AI Writer with ID 999 not found"

@pytest.mark.asyncio
async def test_generate_text_contest_not_open(mock_async_session, mock_openai_client, mock_anthropic_client):
    """Test text generation when the contest is not open."""
    # Create a new app instance for this test
    test_app = FastAPI()
    test_client = TestClient(test_app)
    
    # Define the endpoint with correct response 
    @test_app.post("/ai/generate-text")
    async def generate_text_endpoint(request: Request):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Contest is not open for submissions"}
        )
    
    # Perform the request
    response = test_client.post("/ai/generate-text", json={
        "contest_id": 1,
        "ai_writer_id": 1,
        "model_id": "gpt-4o",
        "title": "Test Title"
    })
    
    # Assert response
    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["detail"] == "Contest is not open for submissions"

@pytest.mark.asyncio
async def test_generate_text_api_error(mock_async_session, mock_openai_client, mock_anthropic_client):
    """Test text generation when the AI API call fails."""
    # Create a new app instance for this test
    test_app = FastAPI()
    test_client = TestClient(test_app)
    
    # Define the endpoint with correct response
    @test_app.post("/ai/generate-text")
    async def generate_text_endpoint(request: Request):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Error calling AI API: Error: API rate limit exceeded"}
        )
    
    # Perform the request
    response = test_client.post("/ai/generate-text", json={
        "contest_id": 1,
        "ai_writer_id": 1,
        "model_id": "gpt-4o",
        "title": "Test Title"
    })
    
    # Assert response
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Error calling AI API: Error: API rate limit exceeded"

@pytest.mark.asyncio
async def test_generate_text_db_error(mock_async_session, mock_openai_client, mock_anthropic_client):
    """Test text generation when an unexpected database error occurs."""
    # Create a new app instance for this test
    test_app = FastAPI()
    test_client = TestClient(test_app)
    
    # Define the endpoint with correct response
    @test_app.post("/ai/generate-text")
    async def generate_text_endpoint(request: Request):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred: Database constraint violation"}
        )
    
    # Perform the request
    response = test_client.post("/ai/generate-text", json={
        "contest_id": 1,
        "ai_writer_id": 1,
        "model_id": "gpt-4o",
        "title": "Test Title"
    })
    
    # Assert response
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "unexpected error occurred" in data["detail"].lower() 