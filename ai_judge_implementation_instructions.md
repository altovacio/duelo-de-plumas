# AI Judge Implementation Instructions

This document provides instructions for completing the implementation of the AI judges feature in Duelo de Plumas.

## Installation

1. Activate your virtual environment:
   ```
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. Install the new dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Initialize database migrations (if not already done):
   ```
   flask db init
   ```

4. Create a migration for the new AI judge fields:
   ```
   flask db migrate -m "Add AI judge fields"
   ```

5. Apply the migration:
   ```
   flask db upgrade
   ```

6. Run the AI judge seeding script to create the initial judges:
   ```
   python seed_ai_judges.py
   ```

## Features Implemented

The AI judge implementation includes the following features:

1. **Model Changes**:
   - Added AI judge fields to the User model
   - Created an AIEvaluation model to store AI evaluation results

2. **AI Judge Service**:
   - AI judge parameter configuration
   - API integration with OpenAI and Anthropic
   - Prompt construction and response parsing
   - Cost tracking and token counting

3. **Admin Interface**:
   - Add/edit/delete AI judges
   - Configure AI judge personality prompts and models
   - Assign AI judges to contests

4. **Contest Evaluation**:
   - AI judge evaluation triggering
   - Display of AI evaluation results
   - Integration with existing contest result system

5. **Initial AI Judges**:
   - Five AI judge personas with unique personalities

## Usage

### Managing AI Judges

1. Log in as an admin
2. Go to the Admin Panel
3. Click on "Manage AI Judges"
4. From here you can:
   - View existing AI judges
   - Add new AI judges
   - Edit AI judge configurations
   - Delete AI judges

### Running AI Evaluations

1. Create a contest and assign one or more AI judges
2. Once the contest moves to the evaluation phase:
   - Log in as an admin
   - Go to the contest submissions page
   - In the AI Judges section, click "Run Evaluation" for each AI judge
   - The system will call the AI API, process the results, and create rankings

### Notes on API Costs

- The system tracks token usage and costs for each AI evaluation
- Costs are displayed after each evaluation run
- Make sure your OpenAI and Anthropic API keys are set in the .env file

## Troubleshooting

If you encounter issues with the AI judges:

1. Check your API keys in the .env file
2. Ensure you have internet access for API calls
3. Check the application logs for detailed error messages
4. Verify that the database migration completed successfully
5. Make sure the AI judges were properly seeded

## Security Considerations

- API keys are stored in the .env file and should be kept secure
- AI judges use randomly generated passwords that are not meant to be used for login
- Consider implementing more robust prompt security for production use 