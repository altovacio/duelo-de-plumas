import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-you-should-change'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Add other configuration variables here if needed
    LANGUAGES = ['es'] # Default language
    # Example: Contest parameters
    # MAX_SUBMISSION_LENGTH = 5000 # words
    # JUDGES_PER_CONTEST = 3 

# Configuration for the contest seeding script

CONTEST_NAME = "Muestra"
EXAMPLES_DIR = "examples"
OUTPUT_FILE = f"{CONTEST_NAME.lower()}_contest_data.json" 