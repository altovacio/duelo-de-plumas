"""
Examples for using the AI API endpoints in the FastAPI application.
"""

import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"  # Change as needed for your deployment

async def test_generate_text():
    """Test the /ai/generate-text endpoint."""
    url = f"{BASE_URL}/ai/generate-text"
    
    # Request payload based on GenerateTextRequest schema
    payload = {
        "contest_id": 1,  # Replace with an actual contest ID from your database
        "ai_writer_id": 1,  # Replace with an actual AI writer ID
        "model_id": "gpt-4o",  # Or another supported model like "claude-3-opus-20240229"
        "title": "The Silent Guardian"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("\nSuccessful Response:")
                print(f"Success: {result['success']}")
                print(f"Message: {result['message']}")
                print(f"Submission ID: {result['submission_id']}")
                # Print just the first 100 chars of the text to keep output manageable
                if result.get('text'):
                    preview = result['text'][:100] + "..." if len(result['text']) > 100 else result['text']
                    print(f"Generated Text Preview: {preview}")
            else:
                print("\nError Response:")
                print(response.text)
                
        except Exception as e:
            print(f"Error: {e}")

async def test_evaluate_contest():
    """Test the /ai/evaluate-contest/{contest_id} endpoint."""
    contest_id = 1  # Replace with an actual contest ID
    judge_id = 1    # Replace with an actual AI judge ID
    
    url = f"{BASE_URL}/ai/evaluate-contest/{contest_id}?judge_id={judge_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("\nSuccessful Response:")
                print(f"Success: {result['success']}")
                print(f"Message: {result['message']}")
                print(f"Evaluation ID: {result.get('evaluation_id')}")
                print(f"Judge ID: {result.get('judge_id')}")
                print(f"Contest ID: {result.get('contest_id')}")
                
                if result.get('rankings'):
                    print("\nRankings:")
                    for sub_id, place in result['rankings'].items():
                        print(f"Submission {sub_id}: Rank {place}")
                
                if result.get('comments'):
                    print("\nComments Preview:")
                    for sub_id, comment in result['comments'].items():
                        preview = comment[:100] + "..." if len(comment) > 100 else comment
                        print(f"Submission {sub_id}: {preview}")
            else:
                print("\nError Response:")
                print(response.text)
                
        except Exception as e:
            print(f"Error: {e}")

async def main():
    """Run the API endpoint examples."""
    print("===== Testing /ai/generate-text endpoint =====")
    await test_generate_text()
    
    print("\n\n===== Testing /ai/evaluate-contest endpoint =====")
    await test_evaluate_contest()

if __name__ == "__main__":
    asyncio.run(main()) 