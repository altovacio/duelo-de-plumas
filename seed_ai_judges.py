import os
import json
from app import create_app, db
from app.models import User

# Define the AI judges to be created
# Note: We need to select a valid, available model ID from our config.
# Let's choose 'gpt-4o-mini' as the default for now as it's marked available and likely cheaper.
DEFAULT_AI_MODEL_ID = 'gpt-4o-mini'

# Load available models to verify the default exists
try:
    config_path = os.path.join(os.path.dirname(__file__), 'app', 'config', 'ai_model_costs.json')
    with open(config_path, 'r') as f:
        all_models = json.load(f)
    available_models = [m for m in all_models if m.get('available', False)]
    available_model_ids = [m['id'] for m in available_models]

    if DEFAULT_AI_MODEL_ID not in available_model_ids:
        if available_model_ids:
            print(f"Warning: Default model '{DEFAULT_AI_MODEL_ID}' is not available. Falling back to '{available_model_ids[0]}'.")
            DEFAULT_AI_MODEL_ID = available_model_ids[0]
        else:
            print("Error: No AI models marked as available in ai_model_costs.json. Cannot assign a default model.")
            DEFAULT_AI_MODEL_ID = None # Indicate failure
except FileNotFoundError:
    print("Error: app/config/ai_model_costs.json not found. Cannot verify default AI model.")
    DEFAULT_AI_MODEL_ID = None
except json.JSONDecodeError:
    print("Error: Could not parse app/config/ai_model_costs.json.")
    DEFAULT_AI_MODEL_ID = None
except Exception as e:
    print(f"An unexpected error occurred reading model config: {e}")
    DEFAULT_AI_MODEL_ID = None

judges_to_seed = [
    {
        'username': 'Sigmund',
        'email': 'sigmund@duelo.ai',
        'password': 'complexPassword1!', # Use a secure default or generate dynamically
        'role': 'judge',
        'judge_type': 'ai',
        'ai_model_id': DEFAULT_AI_MODEL_ID,
        'ai_personality_prompt': "Focus on the underlying subconscious motivations and symbolism in the text. Analyze the emotional depth and psychological complexity."
    },
    {
        'username': 'Alfred',
        'email': 'alfred@duelo.ai',
        'password': 'complexPassword1!',
        'role': 'judge',
        'judge_type': 'ai',
        'ai_model_id': DEFAULT_AI_MODEL_ID,
        'ai_personality_prompt': "Evaluate the text's logical structure, clarity of thought, and the elegance of its core ideas. Look for originality and intellectual rigor."
    },
    {
        'username': 'Pablo',
        'email': 'pablo@duelo.ai',
        'password': 'complexPassword1!',
        'role': 'judge',
        'judge_type': 'ai',
        'ai_model_id': DEFAULT_AI_MODEL_ID,
        'ai_personality_prompt': "Judge the text based on its originality, boldness, and departure from convention. Value unique style and artistic risk-taking."
    },
    {
        'username': 'Charles',
        'email': 'charles@duelo.ai',
        'password': 'complexPassword1!',
        'role': 'judge',
        'judge_type': 'ai',
        'ai_model_id': DEFAULT_AI_MODEL_ID,
        'ai_personality_prompt': "Assess the text's adaptability and fitness for its purpose. How well does it evolve its themes and narrative? Focus on development and thematic survival."
    },
    {
        'username': 'Igor',
        'email': 'igor@duelo.ai',
        'password': 'complexPassword1!',
        'role': 'judge',
        'judge_type': 'ai',
        'ai_model_id': DEFAULT_AI_MODEL_ID,
        'ai_personality_prompt': "Analyze the text's rhythm, pacing, and structural innovation. Look for dissonant ideas resolved in interesting ways and a strong, perhaps unconventional, narrative pulse."
    }
]

def seed_judges():
    if DEFAULT_AI_MODEL_ID is None:
        print("Cannot seed AI judges due to issues loading or finding an available AI model.")
        return

    app = create_app()
    with app.app_context():
        print("Seeding AI judges...")
        count = 0
        for judge_data in judges_to_seed:
            # Check if user already exists
            existing_user = User.query.filter(
                (User.username == judge_data['username']) |
                (User.email == judge_data['email'])
            ).first()

            if existing_user:
                print(f"User '{judge_data['username']}' or email '{judge_data['email']}' already exists. Skipping.")
                continue

            # Create new user
            user = User(
                username=judge_data['username'],
                email=judge_data['email'],
                role=judge_data['role'],
                judge_type=judge_data['judge_type'],
                ai_model_id=judge_data['ai_model_id'],
                ai_personality_prompt=judge_data['ai_personality_prompt']
            )
            user.set_password(judge_data['password'])
            db.session.add(user)
            count += 1
            print(f"Added AI judge: {judge_data['username']}")

        try:
            db.session.commit()
            print(f"Successfully seeded {count} AI judges.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing judges to database: {e}")

if __name__ == '__main__':
    seed_judges() 