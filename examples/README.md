# Fast API Application Examples

This directory contains example code to help you test and interact with the FastAPI application's AI endpoints.

## Setup and Running the API

To run the FastAPI application:

```bash
# Navigate to the project root directory
cd /path/to/duelo-de-plumas

# Activate your virtual environment
# If using venv:
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run the FastAPI application using uvicorn
uvicorn v2.main:app --reload
```

This will start the API server on http://localhost:8000 by default.

## Available Examples

1. **Python Client Example**: `api_endpoints_usage.py`
   - An async Python script using httpx to interact with the API
   - Run with: `python examples/api_endpoints_usage.py`

2. **cURL Examples**: `curl_examples.md`
   - Command-line examples using curl to interact with the API
   - Copy and paste the commands into your terminal

## API Endpoints

### 1. Generate Text: `/ai/generate-text`

Generate creative text for a contest using an AI writer:

**Parameters:**
- `contest_id` (int): ID of the contest
- `ai_writer_id` (int): ID of the AI Writer
- `model_id` (string): ID of the AI model to use (e.g., "gpt-4o", "claude-3-opus-20240229")
- `title` (string): Title for the generated text

### 2. Evaluate Contest: `/ai/evaluate-contest/{contest_id}`

Trigger an AI evaluation for a specific contest using a designated AI judge:

**Parameters:**
- `contest_id` (int): ID of the contest (in path)
- `judge_id` (int): ID of the AI judge (as query parameter)

## Troubleshooting

If you encounter issues with the endpoints:

1. Ensure the API server is running
2. Verify that the database contains valid contest and AI writer records with the IDs you're using
3. Check the API server logs for detailed error messages
4. Verify that the API endpoint URLs in the examples match your actual API server configuration

For more detailed API documentation, visit the Swagger UI at http://localhost:8000/docs when the API server is running. 