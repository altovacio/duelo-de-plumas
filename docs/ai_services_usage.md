# AI Services Usage Guide

This document explains how to use the real AI service implementations for OpenAI and Anthropic in the Duelo de Plumas platform.

## Environment Setup

To use the real AI services, you need to set up API keys for the providers you want to use:

1. Create or edit the `.env` file in the `backend` directory
2. Add your API keys:
   ```
   OPENAI_API_KEY=your-openai-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   ```

## Available Models

The system uses the models defined in `backend/app/utils/ai_model_costs.json`. By default, the following models are enabled:

- **OpenAI**:
  - `gpt-4o` - GPT-4o (omni)
  - `gpt-4o-mini` - GPT-4o mini

- **Anthropic**:
  - `claude-3-7-sonnet-latest` - Claude 3.7 Sonnet
  - `claude-3-5-haiku-latest` - Claude 3.5 Haiku

You can enable or disable models by modifying the `available` field in the JSON file.

## Cost Management

All AI operations in the platform use the credit system for cost tracking:

- 1 credit = $0.01 USD
- Costs are calculated based on token usage (both input and output tokens)
- Users need sufficient credits to perform AI operations
- Each operation records token usage and cost information

## Using Batch Completions

The platform supports batch processing for efficiency with both OpenAI and Anthropic:

### OpenAI

OpenAI provides a native batch API for more efficient processing of multiple requests:

```python
# Example of using batch completions with OpenAI
from app.services.ai_provider_service import get_provider_for_model

provider = get_provider_for_model("gpt-4o")
if provider:
    results = await provider.generate_batch(
        model_id="gpt-4o",
        prompts=["Prompt 1", "Prompt 2", "Prompt 3"],
        system_message="Optional system message",
        temperature=0.7
    )
    
    for text, prompt_tokens, completion_tokens in results:
        # Process each result
        print(f"Generated text: {text}")
        print(f"Tokens used: {prompt_tokens + completion_tokens}")
```

#### OpenAI Batch Processing Benefits

- **Simplified processing**: Send multiple requests in a single API call
- **Increased throughput**: Process more requests more efficiently
- **Reduced overhead**: Less HTTP connection overhead compared to multiple individual calls
- **Automatic retries**: Built-in handling of rate limits and transient errors
- **Graceful fallback**: If batch API fails, the system automatically falls back to concurrent individual requests

The implementation handles:
1. Creating a properly formatted batch request
2. Processing all completions in parallel
3. Collecting and returning results with proper token accounting

### Anthropic

Anthropic provides a native Message Batches API which is used for batch processing, offering several advantages:

- **50% cost reduction** compared to standard API prices
- Efficient processing of large volumes of requests asynchronously
- Support for up to 100,000 message requests per batch

The implementation automatically handles:
1. Creating a batch request
2. Polling for completion status
3. Retrieving and processing results

```python
# Example of using batch completions with Anthropic
from app.services.ai_provider_service import get_provider_for_model

provider = get_provider_for_model("claude-3-7-sonnet-latest")
if provider:
    results = await provider.generate_batch(
        model_id="claude-3-7-sonnet-latest",
        prompts=["Prompt 1", "Prompt 2", "Prompt 3"],
        system_message="Optional system message",
        temperature=0.7
    )
    
    for text, prompt_tokens, completion_tokens in results:
        # Process each result at 50% of standard price
        print(f"Generated text: {text}")
        print(f"Tokens used: {prompt_tokens + completion_tokens}")
```

#### Anthropic Batch Pricing

| Model             | Batch input   | Batch output  |
| ----------------- | ------------- | ------------- |
| Claude 3.7 Sonnet | $1.50 / MTok  | $7.50 / MTok  |
| Claude 3.5 Sonnet | $1.50 / MTok  | $7.50 / MTok  |
| Claude 3.5 Haiku  | $0.40 / MTok  | $2 / MTok     |
| Claude 3 Opus     | $7.50 / MTok  | $37.50 / MTok |
| Claude 3 Haiku    | $0.125 / MTok | $0.625 / MTok |

These prices represent a 50% discount from standard API rates.

## Example Usage in Agent Service

The AI services are primarily used through the `AgentService`, which handles judge and writer agents. The service:

1. Validates that the user has access to the agent
2. Checks if the user has sufficient credits
3. Calls the appropriate AI provider through the `AIService`
4. Deducts credits based on actual token usage
5. Stores the results in the database

### Batch Processing for Contest Judging

When judging contests with multiple texts, the system automatically uses batch processing to evaluate entries more efficiently:

1. Each text is individually evaluated using batch processing
2. Individual evaluations are aggregated and a final ranking is determined
3. For Anthropic models, this provides a 50% cost reduction
4. For OpenAI models, this provides improved performance and reliability

### Judges Use Batch Services, Writers Use Regular Chat Completions

With this implementation, the system is designed so that:

- **Judges** (when evaluating multiple texts in a contest) automatically use batch services:
    - For Anthropic, this means the official Message Batches API (with 50% cost savings).
    - For OpenAI, this means the official batch API (or a fallback to concurrent requests if needed).
    - This is ideal for judging, as it processes many texts efficiently and cost-effectively.

- **Writers** (when generating a single text) use regular chat completions:
    - The system calls the provider's single completion endpoint for each writing request.
    - This is appropriate for generating a single piece of text, such as a story or poem.

**Why this is beneficial:**
- The logic for batch vs. single completions is handled automatically by the service layer.
- The system always chooses the most efficient and cost-effective method for the use case.
- Users and API consumers do not need to know or care about the underlying batching—they just get fast, cost-effective results.

**Example:**
- Judging a contest with 10 texts → uses batch processing for all texts.
- Generating a new story with a writer agent → uses a single chat completion.

**References:**
- [OpenAI Batch API](https://platform.openai.com/docs/guides/batch)
- [Anthropic Batch Processing](https://docs.anthropic.com/en/docs/build-with-claude/batch-processing)

## Extending with New Providers

To add support for a new AI provider:

1. Create a new class in `backend/app/services/ai_provider_service.py` that implements the `AIProviderInterface`
2. Add the provider to the `PROVIDER_MAP` in the same file
3. Add models for the provider in the `ai_model_costs.json` file

## Troubleshooting

If you encounter issues with the AI services:

1. Check that the API keys are correctly set in the `.env` file
2. Verify that the models you're trying to use have `"available": true` in the JSON config
3. Look for error messages in the logs, which will indicate issues with API calls
4. Ensure the user has sufficient credits for the operation

### Batch Processing Troubleshooting

#### OpenAI Batch
- The system has a fallback mechanism that will automatically revert to individual requests if the batch API fails
- Check logs for any errors with batch processing, which may indicate rate limiting or quota issues

#### Anthropic Batch
- Batch processing is asynchronous and may take time to complete (most batches finish within 1 hour)
- If a batch doesn't complete within 24 hours, it will expire
- Maximum batch size is 100,000 message requests or 256 MB
- Batch results are available for 29 days after creation

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [OpenAI Batch Processing](https://platform.openai.com/docs/guides/batch)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Anthropic Batch Processing Documentation](https://docs.anthropic.com/en/docs/build-with-claude/batch-processing) 