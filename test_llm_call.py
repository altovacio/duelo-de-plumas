import os
import sys
import json
import logging
from dotenv import load_dotenv

# Add project root to path to allow importing app modules
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now import necessary components from the app
try:
    from app.services.ai_judge_service import call_ai_api, get_model_costs, calculate_cost
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Ensure this script is run from the project root directory and necessary packages are installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables (especially API keys)
load_dotenv()

def test_llm_calls():
    """Tests API calls for available models."""
    logging.info("Starting LLM call test...")

    model_costs_data = get_model_costs()
    if not model_costs_data:
        logging.error("Failed to load model costs. Cannot proceed with tests.")
        return

    available_models = [m for m_id, m in model_costs_data.items() if m.get('available')]
    if not available_models:
        logging.warning("No models marked as available in ai_model_costs.json. No tests to run.")
        return

    test_prompt = "Name 5 fruits and 1 tool."
    logging.info(f"Using test prompt: \"{test_prompt}\"")

    results = {}
    for model_info in available_models:
        model_id = model_info['id']
        provider = model_info.get('provider')
        logging.info(f"--- Testing Model: {model_id} (Provider: {provider}) ---")
        
        # Check for API keys before attempting call
        api_key_needed = None
        if provider == "OpenAI":
            api_key_needed = 'OPENAI_API_KEY'
        elif provider == "Anthropic":
            api_key_needed = 'ANTHROPIC_API_KEY'
            
        if api_key_needed and not os.environ.get(api_key_needed):
            logging.warning(f"API Key {api_key_needed} not found in environment variables. Skipping test for {model_id}.")
            results[model_id] = {'status': 'skipped', 'reason': f'{api_key_needed} not set'}
            continue
            
        # Call the API function
        api_result = call_ai_api(test_prompt, model_id)
        results[model_id] = api_result
        
        if api_result.get('success'):
            logging.info(f"SUCCESS - Response received from {model_id}.")
            prompt_tokens = api_result.get('prompt_tokens')
            completion_tokens = api_result.get('completion_tokens')
            cost = calculate_cost(model_id, prompt_tokens, completion_tokens)
            results[model_id]['calculated_cost'] = cost
            # print(f"Response Text: {api_result.get('response_text')[:200]}...") # Optionally print snippet
        else:
            logging.error(f"FAILED - Error calling {model_id}: {api_result.get('error')}")

    logging.info("--- LLM Call Test Summary ---")
    for model_id, result in results.items():
        status = "UNKNOWN"
        details = ""
        if result.get('status') == 'skipped':
            status = "SKIPPED"
            details = f"({result.get('reason')})"
        elif result.get('success') is True:
            status = "SUCCESS"
            cost_str = f"{result.get('calculated_cost', 'N/A'):.6f}" if result.get('calculated_cost') is not None else "N/A"
            details = f"(Tokens: P={result.get('prompt_tokens', 'N/A')}, C={result.get('completion_tokens', 'N/A')}, Cost: ${cost_str})"
        elif result.get('success') is False:
            status = "FAILED"
            details = f"({result.get('error', 'Unknown error')})"
            
        print(f"- {model_id}: {status} {details}")

if __name__ == "__main__":
    test_llm_calls() 