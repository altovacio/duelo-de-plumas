import pytest
from unittest.mock import patch, MagicMock
import re

# Assuming the service file is in v2/app/services/ai_services.py
# Adjust the import path if your structure is different
from backend.app.services.ai_services import (
    get_model_info,
    count_tokens,
    calculate_cost,
    format_submissions_text,
    construct_judge_prompt,
    construct_writer_prompt,
    parse_ai_judge_response
)

# --- Test Data ---

# Mock configuration data (mirroring ai_params.py structure)
MOCK_AI_MODELS = [
    {
        'id': 'test-model-1', 'name': 'Test Model 1', 'provider': 'testprovider', 
        'max_tokens': 1000, 'api_name': 'api-model-1', 'available': True
    },
    {
        'id': 'test-model-2', 'name': 'Test Model 2', 'provider': 'testprovider', 
        'max_tokens': 2000, 'api_name': 'api-model-2', 'available': True
    },
    {
        'id': 'unavailable-model', 'name': 'Unavailable Model', 'provider': 'testprovider', 
        'max_tokens': 500, 'api_name': 'api-model-unavail', 'available': False
    },
]

MOCK_API_PRICING = {
    'testprovider': {
        'api-model-1': {'input': 0.01, 'output': 0.02},
        'api-model-2': {'input': 0.03, 'output': 0.04},
    }
}

MOCK_DEFAULT_AI_MODEL_ID = 'test-model-1'

# Mock objects for Contest, User, Submission, AIWriter
class MockContest:
    def __init__(self, title="Test Contest", description="A test description."):
        self.title = title
        self.description = description

class MockUser: # Represents a Judge
    def __init__(self, ai_personality_prompt="Be a fair judge."):
        self.ai_personality_prompt = ai_personality_prompt

class MockAIWriter:
    def __init__(self, personality_prompt="Write creatively."):
        self.personality_prompt = personality_prompt

class MockSubmission:
    def __init__(self, id, title, text_content):
        self.id = id
        self.title = title
        self.text_content = text_content

# --- Tests for get_model_info ---

@patch('backend.app.services.ai_services.AI_MODELS', MOCK_AI_MODELS)
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', MOCK_DEFAULT_AI_MODEL_ID)
def test_get_model_info_found():
    model_info = get_model_info('test-model-2')
    assert model_info['id'] == 'test-model-2'
    assert model_info['name'] == 'Test Model 2'

@patch('backend.app.services.ai_services.AI_MODELS', MOCK_AI_MODELS)
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', MOCK_DEFAULT_AI_MODEL_ID)
def test_get_model_info_not_found_uses_default():
    model_info = get_model_info('non-existent-model')
    assert model_info['id'] == MOCK_DEFAULT_AI_MODEL_ID

@patch('backend.app.services.ai_services.AI_MODELS', [MOCK_AI_MODELS[1]]) # Only model 2 available
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', 'test-model-1') # Default not available
def test_get_model_info_default_not_found_uses_first_available():
    model_info = get_model_info('non-existent-model')
    assert model_info['id'] == 'test-model-2' # Falls back to the only available one

@patch('backend.app.services.ai_services.AI_MODELS', []) # No models available
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', MOCK_DEFAULT_AI_MODEL_ID)
def test_get_model_info_no_models_available_raises_index_error():
     # If AI_MODELS is empty, accessing AI_MODELS[0] will raise IndexError
     with pytest.raises(IndexError):
           get_model_info('any-model')


# --- Tests for count_tokens ---

# Mock tiktoken behavior
class MockEncoding:
    def encode(self, text):
        # Simple mock: token count is number of words
        return text.split()

@patch('backend.app.services.ai_services.tiktoken')
@patch('backend.app.services.ai_services.AI_MODELS', MOCK_AI_MODELS)
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', MOCK_DEFAULT_AI_MODEL_ID)
def test_count_tokens_success(mock_tiktoken):
    mock_tiktoken.encoding_for_model.return_value = MockEncoding()
    text = "This is a test sentence."
    tokens = count_tokens(text, 'test-model-1')
    mock_tiktoken.encoding_for_model.assert_called_with('api-model-1')
    assert tokens == 5 # "This", "is", "a", "test", "sentence."

@patch('backend.app.services.ai_services.tiktoken')
@patch('backend.app.services.ai_services.AI_MODELS', MOCK_AI_MODELS)
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', MOCK_DEFAULT_AI_MODEL_ID)
def test_count_tokens_encoding_key_error_falls_back_to_base(mock_tiktoken):
    mock_tiktoken.encoding_for_model.side_effect = KeyError("Model not found")
    mock_tiktoken.get_encoding.return_value = MockEncoding()
    text = "Another test."
    tokens = count_tokens(text, 'test-model-2')
    mock_tiktoken.encoding_for_model.assert_called_with('api-model-2')
    mock_tiktoken.get_encoding.assert_called_with('cl100k_base')
    assert tokens == 2

@patch('backend.app.services.ai_services.tiktoken')
@patch('backend.app.services.ai_services.AI_MODELS', MOCK_AI_MODELS)
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', MOCK_DEFAULT_AI_MODEL_ID)
def test_count_tokens_all_encoding_errors_fall_back_to_chars(mock_tiktoken):
    mock_tiktoken.encoding_for_model.side_effect = KeyError("Model not found")
    mock_tiktoken.get_encoding.side_effect = KeyError("cl100k_base not found")
    text = "Short test" # 10 chars
    tokens = count_tokens(text, 'test-model-1')
    assert tokens == 10 // 4 # Fallback calculation

# --- Tests for calculate_cost ---

@patch('backend.app.services.ai_services.AI_MODELS', MOCK_AI_MODELS)
@patch('backend.app.services.ai_services.API_PRICING', MOCK_API_PRICING)
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', MOCK_DEFAULT_AI_MODEL_ID)
def test_calculate_cost_success():
    cost = calculate_cost('test-model-1', 1000, 2000) # 1k input, 2k output
    # Expected: (1000/1000 * 0.01) + (2000/1000 * 0.02) = 0.01 + 0.04 = 0.05
    assert cost == pytest.approx(0.05)

@patch('backend.app.services.ai_services.AI_MODELS', MOCK_AI_MODELS)
@patch('backend.app.services.ai_services.API_PRICING', MOCK_API_PRICING)
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', MOCK_DEFAULT_AI_MODEL_ID)
def test_calculate_cost_model_not_in_pricing():
    cost = calculate_cost('model-not-in-pricing', 1000, 1000)
     # Falls back to default model 'test-model-1'
    assert cost == pytest.approx(0.01 + 0.02) 

@patch('backend.app.services.ai_services.AI_MODELS', MOCK_AI_MODELS)
@patch('backend.app.services.ai_services.API_PRICING', {}) # Empty pricing
@patch('backend.app.services.ai_services.DEFAULT_AI_MODEL_ID', MOCK_DEFAULT_AI_MODEL_ID)
def test_calculate_cost_no_pricing_info():
    cost = calculate_cost('test-model-1', 1000, 1000)
    assert cost == 0.0

# --- Tests for format_submissions_text ---

def test_format_submissions_text():
    submissions = [
        MockSubmission(id=1, title="Title One", text_content="Content one."),
        MockSubmission(id=123, title="Second Title", text_content="More content here."),
    ]
    expected_text = '''

TEXTO #1: "Title One"
Content one.
--- FIN DEL TEXTO #1 ---

TEXTO #123: "Second Title"
More content here.
--- FIN DEL TEXTO #123 ---'''
    assert format_submissions_text(submissions) == expected_text

def test_format_submissions_text_empty():
    assert format_submissions_text([]) == ""

# --- Tests for construct_judge_prompt ---

@patch('backend.app.services.ai_services.BASE_JUDGE_INSTRUCTION_PROMPT', "Judge Instruction")
def test_construct_judge_prompt():
    contest = MockContest(title="Judging Contest")
    judge = MockUser(ai_personality_prompt="Strict Personality")
    submissions = [MockSubmission(id=5, title="Entry 5", text_content="Text 5")]
    
    prompt = construct_judge_prompt(contest, judge, submissions)
    
    # Use triple quotes for multiline assertions
    assert """<INSTRUCCIONES>
Judge Instruction
</INSTRUCCIONES>""" in prompt
    assert """<PERSONALIDAD>
Strict Personality
</PERSONALIDAD>""" in prompt
    # Note: Raw f-string formatting might differ slightly in newlines, 
    # checking key parts might be more robust. Let's check substrings.
    assert "CONCURSO: Judging Contest" in prompt
    assert "DESCRIPCIÓN: A test description." in prompt
    assert "Strict Personality" in prompt
    assert """<TEXTOS_A_JUDICAR>


TEXTO #5: "Entry 5"
Text 5
--- FIN DEL TEXTO #5 ---
</TEXTOS_A_JUDICAR>""" in prompt

# --- Tests for construct_writer_prompt ---

@patch('backend.app.services.ai_services.BASE_WRITER_INSTRUCTION_PROMPT', "Writer Instruction")
def test_construct_writer_prompt():
    contest = MockContest(title="Writing Contest", description=None)
    writer = MockAIWriter(personality_prompt="Creative Style")
    title = "My Masterpiece"
    
    prompt = construct_writer_prompt(contest, writer, title)
    
    # Use triple quotes for multiline assertions
    assert """<INSTRUCCIONES>
Writer Instruction
</INSTRUCCIONES>""" in prompt
    assert """<PERSONALIDAD>
Creative Style
</PERSONALIDAD>""" in prompt
    # Check key substrings for context
    assert "CONCURSO: Writing Contest" in prompt
    assert "DESCRIPCIÓN: No hay descripción específica." in prompt
    assert "TÍTULO DEL TEXTO: My Masterpiece" in prompt
    assert "Creative Style" in prompt

# --- Tests for parse_ai_judge_response ---

def test_parse_ai_judge_response_standard_format():
    response_text = """
Some introductory text.

RANKING:
1. TEXTO #10 - Title A
2. TEXTO #25 - Title B
3. TEXTO #5 - Title C

JUSTIFICACIONES:
1. Justification for #10. It was good.
2. Justification for #25. It was okay.
3. Justification for #5. It needs work.

Some concluding text.
"""
    submissions = [
        MockSubmission(id=5, title="Title C", text_content="..."),
        MockSubmission(id=10, title="Title A", text_content="..."),
        MockSubmission(id=25, title="Title B", text_content="..."),
    ]
    
    expected = [
        (10, 1, "Justification for #10. It was good."),
        (25, 2, "Justification for #25. It was okay."),
        (5, 3, "Justification for #5. It needs work."),
    ]
    
    result = parse_ai_judge_response(response_text, submissions)
    # Sort results by place for consistent comparison
    result.sort(key=lambda x: x[1])
    assert result == expected

def test_parse_ai_judge_response_variation_format():
    response_text = """
RANKING FINAL:
1: Texto #30
2) Text #15
3. (Submission #42)

COMENTARIOS:
Rank 1: Comment for 30.
Rank 2: Comment for 15.
Rank 3: Comment for 42.
"""
    submissions = [
        MockSubmission(id=15, title="Title 15", text_content="..."),
        MockSubmission(id=30, title="Title 30", text_content="..."),
        MockSubmission(id=42, title="Title 42", text_content="..."),
    ]
    
    expected = [
        (30, 1, "Comment for 30."),
        (15, 2, "Comment for 15."),
        (42, 3, "Comment for 42."),
    ]
    
    result = parse_ai_judge_response(response_text, submissions)
    result.sort(key=lambda x: x[1])
    assert result == expected

def test_parse_ai_judge_response_missing_justifications():
    response_text = """
RANKING:
1. TEXTO #1
2. TEXTO #2
"""
    submissions = [
        MockSubmission(id=1, title="Title 1", text_content="..."),
        MockSubmission(id=2, title="Title 2", text_content="..."),
    ]
    
    expected = [
        (1, 1, ""),
        (2, 2, ""),
    ]
    
    result = parse_ai_judge_response(response_text, submissions)
    result.sort(key=lambda x: x[1])
    assert result == expected

def test_parse_ai_judge_response_mention():
    response_text = """
RANKING:
1. TEXTO #11
2. TEXTO #22
3. TEXTO #33
4. TEXTO #44 (Mención Honorífica)

JUSTIFICACIONES:
1. Justification 11.
2. Justification 22.
3. Justification 33.
4. Justification 44 (Mention).
"""
    submissions = [
        MockSubmission(id=11, title="Title 11", text_content="..."),
        MockSubmission(id=22, title="Title 22", text_content="..."),
        MockSubmission(id=33, title="Title 33", text_content="..."),
        MockSubmission(id=44, title="Title 44", text_content="..."),
    ]
    
    expected = [
        (11, 1, "Justification 11."),
        (22, 2, "Justification 22."),
        (33, 3, "Justification 33."),
        (44, 4, "Justification 44 (Mention)."),
    ]
    
    result = parse_ai_judge_response(response_text, submissions)
    result.sort(key=lambda x: x[1])
    assert result == expected

def test_parse_ai_judge_response_no_ranking_section():
    # Test case where the RANKING keyword is missing but format might be guessable
    response_text = """
1. TEXTO #100
2. TEXTO #200

JUSTIFICACIONES:
1. Just 100.
2. Just 200.
"""
    submissions = [
        MockSubmission(id=100, title="Title 100", text_content="..."),
        MockSubmission(id=200, title="Title 200", text_content="..."),
    ]
    
    expected = [
        (100, 1, "Just 100."),
        (200, 2, "Just 200."),
    ]
    
    result = parse_ai_judge_response(response_text, submissions)
    result.sort(key=lambda x: x[1])
    assert result == expected


def test_parse_ai_judge_response_malformed_ranking_id():
    response_text = """
RANKING:
1. TEXTO #abc - Should be ignored
2. TEXTO #10
"""
    submissions = [MockSubmission(id=10, title="Title 10", text_content="...")]
    expected = [(10, 2, "")]
    result = parse_ai_judge_response(response_text, submissions)
    assert result == expected

def test_parse_ai_judge_response_id_not_in_submissions():
    response_text = """
RANKING:
1. TEXTO #999 - Not in contest
2. TEXTO #10
"""
    submissions = [MockSubmission(id=10, title="Title 10", text_content="...")]
    expected = [(10, 2, "")]
    result = parse_ai_judge_response(response_text, submissions)
    assert result == expected 