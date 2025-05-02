# API Endpoint Usage Examples with curl

This document provides examples of how to use the AI API endpoints using `curl` commands.

## Generate Text Endpoint

The `/ai/generate-text` endpoint allows you to generate creative text for a contest using an AI writer.

### Example Request

```bash
curl -X POST "http://localhost:8000/ai/generate-text" \
  -H "Content-Type: application/json" \
  -d '{
    "contest_id": 1,
    "ai_writer_id": 1,
    "model_id": "gpt-4o",
    "title": "The Silent Guardian"
  }'
```

### Example Response (Success)

```json
{
  "success": true,
  "message": "Text generated and submitted successfully",
  "submission_id": 42,
  "text": "In the shadows of the ancient city, where cobblestone streets wind through forgotten alleys..."
}
```

### Example Response (Error - Contest Not Found)

```json
{
  "detail": "Contest with ID 999 not found"
}
```

## Evaluate Contest Endpoint

The `/ai/evaluate-contest/{contest_id}` endpoint triggers an AI evaluation for a specific contest using a designated AI judge.

### Example Request

```bash
curl -X POST "http://localhost:8000/ai/evaluate-contest/1?judge_id=1"
```

### Example Response (Success)

```json
{
  "success": true,
  "message": "Contest evaluation completed successfully",
  "evaluation_id": 15,
  "judge_id": 1,
  "contest_id": 1,
  "rankings": {
    "42": 1,
    "43": 2,
    "44": 3
  },
  "comments": {
    "42": "This submission demonstrated exceptional creativity and mastery of language...",
    "43": "A compelling narrative with strong character development...",
    "44": "While the story had an interesting premise, the execution lacked depth..."
  }
}
```

### Example Response (Error - Judge Not Found)

```json
{
  "detail": "AI Judge with ID 999 not found"
}
```

## Notes

- Replace `http://localhost:8000` with your actual API server URL
- Use actual `contest_id` and `ai_writer_id` values from your database
- Available `model_id` options include: "gpt-4o", "claude-3-opus-20240229", etc. 