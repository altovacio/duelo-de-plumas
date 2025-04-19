# Plan for Implementing AI Judges

This document outlines the steps and considerations for integrating AI judges into the Duelo de Plumas platform.

## 1. Configuration & Judge Setup

*   **Judge Types:** When a judge is registered, they must be designated as either 'Human' or 'AI'.
*   **AI Judge Configuration (Admin):**
    *   For AI judges, the admin interface must allow selection of the specific AI model to use (e.g., GPT-4, Gemini, Claude) from a dropdown list.
    *   The admin must provide a "Personality Prompt" for each AI judge, defining its persona or specific evaluation focus.
*   **API Keys:** will be securely stored in .env file
*   **Prompt Engineering:**
    *   **System Prompt Structure:** The final prompt sent to the AI will be constructed from two parts:
        1.  A fixed **Instruction Prompt**: Contains standardized instructions on how to evaluate submissions, rank them (1st, 2nd, 3rd), assign optional Honorable Mentions for outstanding entries outside the top 3, and the expected output format. This part is maintained within the application code or configuration.
        2.  A variable **Personality Prompt**: Provided by the admin during AI judge setup (see above). This allows customization of the judge's evaluation style or focus.
    *   **Prompt Formatting:** The application needs to correctly combine the instruction prompt, personality prompt, contest description and the submission texts before sending to the AI.
*   **Parameters File:** Consider a dedicated parameters file (e.g., `ai_judge_params.json` or a section in `config.py`) for easy modification of available models, default instruction prompts, and other AI-related settings. *Self-note: Personality prompts are stored with the judge entity.*

## 2. Backend Implementation

*   **User/Judge Model Update:** Modify the `User` model (or a dedicated `Judge` model if it exists) (`app/models.py`) to include:
    *   A field indicating the judge type (`judge_type`: 'human' or 'ai').
    *   Fields for AI judges: `ai_model` (string, storing the selected model identifier), `ai_personality_prompt` (text).
*   **Contest Model Update:** Modify the `Contest` model (`app/models.py`) to link to the assigned judge(s). If multiple judges are possible, manage this relationship. *Decision: For now, assume one judge per contest for simplicity, can be expanded later.*
*   **AI Evaluation Service/Module:** Create a new service or module (e.g., `app/services/ai_judge_service.py`) responsible for:
    *   Fetching judge details (model, personality prompt).
    *   Connecting to the chosen AI API.
    *   Formatting submissions and constructing the final combined prompt (instructions + personality + contest info + submissions).
    *   Sending requests to the AI model.
    *   Parsing the AI's response (rankings, comments/justifications).
    *   Handling potential errors (API errors, rate limits, malformed responses).
    *   Implementing retries or fallback mechanisms.
*   **Trigger Mechanism:** AI evaluation will be initiated **manually** by an administrator via the contest management interface.
*   **Data Storage:**
    *   Adapt the `Evaluation` model or create a new `AIEvaluation` model to store the results from an AI judge.
    *   Store:
        *   The AI's ranking for each submission.
        *   AI's comments/justifications for each ranking.
        *   The specific `ai_model` used for the evaluation.
        *   The `prompt_tokens` used (input tokens).
        *   The `completion_tokens` generated (output tokens).
        *   The calculated `cost` of the API call (requires knowing model pricing).
        *   The full prompt sent to the AI (for auditing/debugging).
        *   Potentially the raw AI response (for auditing/debugging).
    *   Link the AI evaluation results back to the `Contest` and relevant `Submission`s.
*   **Integration with Existing Logic:**
    *   Modify the `evaluate_contest` route/view (`app/routes/contest.py`, `app/templates/contest/evaluate_contest.html`) logic.
    *   If a contest's assigned judge is 'AI', this view should *not* show the manual evaluation form. Instead, it should:
        *   Display a button "Run AI Evaluation" if not yet evaluated.
        *   Show the results from the `AIEvaluation` table once evaluation is complete.
    *   Create a new route/endpoint (e.g., `/contest/<int:contest_id>/run_ai_evaluation`) triggered by the admin button, which calls the `ai_judge_service`.

## 3. Frontend Implementation

*   **Admin/Judge Management:** Update the user/judge creation/editing forms:
    *   Add a field to select 'Human' or 'AI' judge type.
    *   Conditionally show fields for 'AI Model' (dropdown of available models) and 'AI Personality Prompt' (textarea) if 'AI' is selected.
*   **Admin/Contest Management:**
    *   When assigning a judge to a contest, ensure only appropriate types can be assigned based on contest settings (if any future distinction is made).
    *   On the contest detail or evaluation page for contests with an AI judge:
        *   Display the assigned AI judge's name and model.
        *   Show the "Run AI Evaluation" button if results are pending.
        *   Provide feedback to the admin while evaluation is running (e.g., a loading indicator).
*   **Displaying Results:**
    *   Update contest detail/results pages (`app/templates/contest/detail.html`, potentially new templates) to display AI-generated rankings and justifications when applicable.
    *   Clearly indicate that the results were generated by an AI judge, mentioning the judge's name (e.g., "Evaluation by AI Judge: Sigmund").
    *   Display the total cost of the AI evaluation for the contest on the results page (perhaps visible only to admins).
    *   Consider showing detailed cost and token usage per evaluation in an admin-only view or log.

## 4. Considerations

*   **Cost:** API calls can be expensive. Tracking cost per evaluation (as planned in Data Storage) is crucial. Admins should be aware of potential costs when triggering evaluations.
*   **Latency:** AI evaluations can take time. The manual trigger approach avoids blocking web requests, but the admin interface needs to handle the wait gracefully (e.g., background task initiation, status updates, perhaps via polling or websockets if desired later).
*   **Bias and Fairness:** AI models can inherit biases. The personality prompt adds another layer. While human oversight isn't mandated in this plan, be aware of potential issues. Results should be reviewed periodically.
*   **Consistency and Reliability:** AI responses can vary. Implement robust parsing and error handling. Test prompts thoroughly. Retries might be needed.
*   **Prompt Security:** *User instruction: De-prioritize advanced prompt injection mitigation for now.* However, basic input sanitization should still be applied to text going into prompts.
*   **Scalability:** The manual trigger limits concurrent runs. If usage grows, consider a background job queue (like Celery) even for manual triggers to manage load.
*   **Token Limits:** Be mindful of model context window limits. The `ai_judge_service` must handle cases where the combined prompt and submissions exceed the limit for the selected model. Strategies: evaluate in batches, summarization (with caveats), or restricting model choices.

## 5. Initial Seeding

*   **Seed Script:** Create a Python script (`seed_ai_judges.py`) that uses the application's models (e.g., `User` or `Judge`) to create 5 initial AI judges:
    *   **Sigmund:** Personality inspired by Freud (e.g., "Focus on the underlying subconscious motivations and symbolism in the text. Analyze the emotional depth and psychological complexity.")
    *   **Alfred:** Personality inspired by Einstein (e.g., "Evaluate the text's logical structure, clarity of thought, and the elegance of its core ideas. Look for originality and intellectual rigor.")
    *   **Pablo:** Personality inspired by Picasso (e.g., "Judge the text based on its originality, boldness, and departure from convention. Value unique style and artistic risk-taking.")
    *   **Charles:** Personality inspired by Darwin (e.g., "Assess the text's adaptability and fitness for its purpose. How well does it evolve its themes and narrative? Focus on development and thematic survival.")
    *   **Igor:** Personality inspired by Stravinsky (e.g., "Analyze the text's rhythm, pacing, and structural innovation. Look for dissonant ideas resolved in interesting ways and a strong, perhaps unconventional, narrative pulse.")
    *   Assign a default available AI model (e.g., the cheapest or fastest one configured) to these initial judges.

## 6. Testing

*   Develop unit and integration tests for the AI evaluation service and prompt generation.
*   Test the manual trigger flow and result display.
*   Test with various numbers of submissions and text lengths to check token handling.
*   Test different personality prompts and models.
*   Test error handling (API errors, parsing errors).
*   Manually review AI results on test contests for quality, fairness, and adherence to both instruction and personality prompts.

Let's review this updated plan and refine it further if needed. 