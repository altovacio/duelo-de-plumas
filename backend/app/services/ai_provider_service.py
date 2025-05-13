"""
Module for AI provider implementations.
This module contains implementations for various AI model providers.
"""

import os
import json
import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any, Union
import aiohttp
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Try importing tiktoken, handle if not available
try:
    import tiktoken
    tiktoken_available = True
except ImportError:
    tiktoken = None
    tiktoken_available = False
    logger.warning("tiktoken library not found. Falling back to character-based token estimation.")

from app.utils.ai_models import ModelProvider

# Approximation function for token counting
def estimate_token_count(text: str, model_id: str = "gpt-4") -> int:
    """
    Estimate the number of tokens in a text.
    Uses tiktoken for compatible models if available, otherwise approximates.
    """
    if tiktoken_available:
        try:
            # Attempt to get encoding for the specified model or a default
            encoding = tiktoken.encoding_for_model(model_id)
            return len(encoding.encode(text))
        except KeyError:
            try:
                 # Fallback for models not directly mapped in tiktoken, e.g., use cl100k_base
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            except Exception as e:
                logger.warning(f"tiktoken encoding failed for model '{model_id}' and fallback 'cl100k_base': {e}. Using character approximation.")
        except Exception as e:
            # Catch other potential tiktoken errors
            logger.warning(f"tiktoken failed for model '{model_id}': {e}. Using character approximation.")
            
    # Fallback approximation: 1 token ≈ 4 characters
    return max(1, len(text) // 4)


class AIProviderInterface(ABC):
    """Abstract base class for AI providers."""
    
    @classmethod
    @abstractmethod
    async def validate_credentials(cls) -> bool:
        """Validate that the provider credentials are configured and valid."""
        pass
        
    @classmethod
    @abstractmethod
    async def generate_text(
        cls, 
        model_id: str,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, int, int]:
        """
        Generate text using the provider's API.
        
        Args:
            model_id: The specific model ID to use
            prompt: The prompt to generate from
            system_message: Optional system message to include
            temperature: The temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (generated_text, prompt_tokens, completion_tokens)
        """
        pass
    
    @classmethod
    @abstractmethod
    async def generate_batch(
        cls,
        model_id: str,
        prompts: List[str],
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> List[Tuple[str, int, int]]:
        """
        Generate multiple completions in a batch.
        
        Args:
            model_id: The specific model ID to use
            prompts: List of prompts to generate from
            system_message: Optional system message to include for all prompts
            temperature: The temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens per generation
            
        Returns:
            List of tuples (generated_text, prompt_tokens, completion_tokens)
        """
        pass


class OpenAIProvider(AIProviderInterface):
    """Implementation for OpenAI API."""
    
    @classmethod
    async def validate_credentials(cls) -> bool:
        """Check if OpenAI API key is set and valid."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found in environment variables")
            return False
            
        # Simple validation by making a minimal API call
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                async with session.get(
                    "https://api.openai.com/v1/models",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return True
                    logger.error(f"OpenAI API validation failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error validating OpenAI credentials: {e}")
            return False
    
    @classmethod
    async def generate_text(
        cls, 
        model_id: str,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, int, int]:
        """Generate text using OpenAI API."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        body = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            body["max_tokens"] = max_tokens
            
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=body
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"OpenAI API error: {response.status}, {error_text}")
                        
                    response_data = await response.json()
                    
                    generated_text = response_data["choices"][0]["message"]["content"]
                    prompt_tokens = response_data["usage"]["prompt_tokens"]
                    completion_tokens = response_data["usage"]["completion_tokens"]
                    
                    return generated_text, prompt_tokens, completion_tokens
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise
    
    @classmethod
    async def generate_batch(
        cls,
        model_id: str,
        prompts: List[str],
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> List[Tuple[str, int, int]]:
        """
        Generate a batch of completions using OpenAI's batch API.
        
        This uses OpenAI's native batch processing which can be more efficient
        and cost-effective than sending individual requests.
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        # Prepare batch request
        messages_list = []
        for prompt in prompts:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            messages_list.append(messages)
        
        # Create the batch request body
        batch_request = {
            "requests": [
                {
                    "model": model_id,
                    "messages": messages,
                    "temperature": temperature
                }
                for messages in messages_list
            ]
        }
        
        if max_tokens:
            for request in batch_request["requests"]:
                request["max_tokens"] = max_tokens
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    "https://api.openai.com/v1/chat/completions/batch",
                    headers=headers,
                    json=batch_request
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"OpenAI Batch API error: {response.status}, {error_text}")
                    
                    response_data = await response.json()
                    
                    # Process batch results
                    results = []
                    for completion in response_data["batch_completions"]:
                        if "error" in completion:
                            logger.error(f"Error in batch item: {completion['error']}")
                            results.append(("Error generating text", 0, 0))
                        else:
                            generated_text = completion["choices"][0]["message"]["content"]
                            prompt_tokens = completion["usage"]["prompt_tokens"]
                            completion_tokens = completion["usage"]["completion_tokens"]
                            results.append((generated_text, prompt_tokens, completion_tokens))
                    
                    # Ensure we have the right number of results
                    if len(results) < len(prompts):
                        for _ in range(len(prompts) - len(results)):
                            results.append(("Error: Missing batch result", 0, 0))
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Error with OpenAI batch API, falling back to concurrent requests: {e}")
            
            # Fallback to concurrent processing for backwards compatibility
            tasks = []
            for prompt in prompts:
                tasks.append(cls.generate_text(
                    model_id=model_id,
                    prompt=prompt,
                    system_message=system_message,
                    temperature=temperature,
                    max_tokens=max_tokens
                ))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any errors
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in batch item {i}: {result}")
                    processed_results.append(("Error generating text", 0, 0))
                else:
                    processed_results.append(result)
                    
            return processed_results


class AnthropicProvider(AIProviderInterface):
    """Implementation for Anthropic Claude API."""
    
    ANTHROPIC_API_VERSION = "2023-06-01"
    MAX_POLL_ATTEMPTS = 20
    POLL_INTERVAL_SECONDS = 10
    
    @classmethod
    async def validate_credentials(cls) -> bool:
        """Check if Anthropic API key is set and valid."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("Anthropic API key not found in environment variables")
            return False
            
        # Simple validation by making a minimal API call
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": cls.ANTHROPIC_API_VERSION,
                    "Content-Type": "application/json"
                }
                async with session.get(
                    "https://api.anthropic.com/v1/models",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return True
                    logger.error(f"Anthropic API validation failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error validating Anthropic credentials: {e}")
            return False
    
    @classmethod
    async def generate_text(
        cls, 
        model_id: str,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, int, int]:
        """Generate text using Anthropic Claude API."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        
        body = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens or 1024
        }
        
        if system_message:
            body["system"] = system_message
            
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": cls.ANTHROPIC_API_VERSION,
                    "Content-Type": "application/json"
                }
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=body
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"Anthropic API error: {response.status}, {error_text}")
                        
                    response_data = await response.json()
                    
                    generated_text = response_data["content"][0]["text"]
                    
                    # Anthropic now includes token counts in response
                    prompt_tokens = response_data["usage"]["input_tokens"]
                    completion_tokens = response_data["usage"]["output_tokens"]
                    
                    return generated_text, prompt_tokens, completion_tokens
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            raise
    
    @classmethod
    async def generate_batch(
        cls,
        model_id: str,
        prompts: List[str],
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> List[Tuple[str, int, int]]:
        """
        Generate a batch of completions using Anthropic Message Batches API.
        
        This uses Anthropic's native batch processing which provides 50% cost savings
        and improved efficiency for processing multiple requests.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        
        # Prepare batch request
        requests = []
        for i, prompt in enumerate(prompts):
            request = {
                "custom_id": f"request_{i}_{uuid.uuid4().hex[:8]}",
                "params": {
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens or 1024
                }
            }
            
            if system_message:
                request["params"]["system"] = system_message
                
            requests.append(request)
        
        # Create the batch
        batch_id = await cls._create_batch(api_key, requests)
        
        # Poll until the batch is complete
        batch_results = await cls._poll_batch_until_complete(api_key, batch_id)
        
        # Process the results
        return cls._process_batch_results(batch_results, len(prompts))
        
    @classmethod
    async def _create_batch(cls, api_key: str, requests: List[Dict]) -> str:
        """Create a new message batch."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": cls.ANTHROPIC_API_VERSION,
                    "Content-Type": "application/json"
                }
                
                body = {"requests": requests}
                
                async with session.post(
                    "https://api.anthropic.com/v1/messages/batches",
                    headers=headers,
                    json=body
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"Anthropic Batch API error: {response.status}, {error_text}")
                    
                    response_data = await response.json()
                    batch_id = response_data["id"]
                    
                    logger.info(f"Created Anthropic batch with ID: {batch_id}")
                    return batch_id
        except Exception as e:
            logger.error(f"Error creating Anthropic batch: {e}")
            raise
    
    @classmethod
    async def _poll_batch_until_complete(cls, api_key: str, batch_id: str) -> Dict:
        """Poll the batch status until it's complete or max attempts are reached."""
        for attempt in range(cls.MAX_POLL_ATTEMPTS):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "x-api-key": api_key,
                        "anthropic-version": cls.ANTHROPIC_API_VERSION
                    }
                    
                    async with session.get(
                        f"https://api.anthropic.com/v1/messages/batches/{batch_id}",
                        headers=headers
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise ValueError(f"Anthropic Batch polling error: {response.status}, {error_text}")
                        
                        batch_status = await response.json()
                        
                        if batch_status["processing_status"] == "ended":
                            logger.info(f"Batch {batch_id} processing complete")
                            
                            # Get the results
                            results_url = batch_status["results_url"]
                            async with session.get(results_url) as results_response:
                                if results_response.status != 200:
                                    error_text = await results_response.text()
                                    raise ValueError(f"Error fetching batch results: {results_response.status}, {error_text}")
                                
                                # Results are in JSONL format, one JSON object per line
                                results_text = await results_response.text()
                                results = [json.loads(line) for line in results_text.strip().split('\n')]
                                return results
                        
                        logger.info(f"Batch {batch_id} still processing. Status: {batch_status['processing_status']}, " + 
                                   f"Counts: {batch_status['request_counts']}. Waiting {cls.POLL_INTERVAL_SECONDS}s...")
                        
                        # Wait before polling again
                        await asyncio.sleep(cls.POLL_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"Error polling batch status: {e}")
                raise
        
        raise TimeoutError(f"Batch {batch_id} did not complete within the maximum number of polling attempts")
    
    @classmethod
    def _process_batch_results(cls, batch_results: List[Dict], expected_count: int) -> List[Tuple[str, int, int]]:
        """Process the batch results into the expected format."""
        # Sort results by custom_id to maintain original order
        sorted_results = sorted(batch_results, key=lambda x: int(x["custom_id"].split("_")[1]))
        
        processed_results = []
        for result in sorted_results:
            if result["result"]["type"] == "succeeded":
                message = result["result"]["message"]
                text = message["content"][0]["text"]
                input_tokens = message["usage"]["input_tokens"]
                output_tokens = message["usage"]["output_tokens"]
                processed_results.append((text, input_tokens, output_tokens))
            else:
                # Handle errors
                error_message = "Error generating text"
                if result["result"]["type"] == "errored" and "error" in result["result"]:
                    error_message = f"Error: {result['result']['error']['message']}"
                processed_results.append((error_message, 0, 0))
        
        # Ensure we have the right number of results
        if len(processed_results) < expected_count:
            # Fill in missing results if needed
            for _ in range(expected_count - len(processed_results)):
                processed_results.append(("Error: Missing batch result", 0, 0))
        
        return processed_results


# Provider registry
PROVIDER_MAP = {
    ModelProvider.OPENAI: OpenAIProvider,
    ModelProvider.ANTHROPIC: AnthropicProvider,
}


def get_provider_for_model(model_id: str) -> Optional[AIProviderInterface]:
    """Get the appropriate provider for a model ID based on model metadata."""
    from app.utils.ai_models import get_model_by_id
    
    model = get_model_by_id(model_id)
    if not model:
        return None
    
    provider_class = PROVIDER_MAP.get(model.provider)
    return provider_class 