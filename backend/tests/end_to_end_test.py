e2e_test_plan = """
# E2E Test Plan: Full Application Workflow

## 1. Setup & User Registration
    - Admin logs in (obtain admin_token).
    - User 1 registers themselves.
        - Verify successful registration and initial credit balance (should be 0).
        - Obtain user1_token after login.
    - Admin registers User 2.
        - Verify successful registration and initial credit balance (should be 0).
    - User 2 logs in (obtain user2_token).
    - Admin verifies User 1 and User 2 details and credit balances. Get user1_id and user2_id.

## 2. AI Agent Creation
    - User 1 creates an AI Writer (writer1). Get writer1_id.
    - User 1 creates an AI Judge (judge1). Get judge1_id.
    - Admin creates a global AI Writer (writer_global). Get writer_global_id.
    - Admin creates a global AI Judge (judge_global). Get judge_global_id.
    - User 1 lists their AI agents, verifies writer1 and judge1 are present and also the global writer and judge are present.
    - User 2 lists their AI agents, verifies they see none but the global writer and judge.
    - Admin lists global AI agents, verifies they see all four agents.

## 3. Contest Creation & Management
    - User 1 creates a public Contest (contest1). Get contest1_id.
        - They do not limit the number of submissions per user.
        - They do not restrict judges from participating as text submitters.
        - They assign judge_global as judge.
    - Admin creates a private Contest (contest2), setting a password.
        - They assign User 2, judge1 and judge_global as judges.
        - They restrict judges from participating as text submitters.
        - They restrict the number of submissions per user to 1.
    - User 2 creates a contest (contest3) with no judges assigned. Succeeds
    - User 2 attempts to edit contest1 -> Should fail.
    - User 1 edits contest1 (updates description). Verify success.
    - Admin edits contest3 (updates description). Verify success.
    - User 2 attempts to assign judge1 to contest 3. Fails
    - User 1 attempts to assign judge1 to contest 3. Fails
    - User 1 attempts to assign user 1 to contest 3. Fails
    - User 1 attempts to assign judge1 and user 2 as judges to contest 1. Succeeds
    - User 2 attempts to assign user 2 as a judge to contest 3. Succeeds
    - Visitor lists contests. Sees all but the private contest with limited details.
    - User 1 lists contests. Sees all but the private contest with limited details.
    - Visitor attempts to view contest2 details with wrong password -> Fails
    - Visitor attempts to view contest2 details with correct password -> Succeeds.
    - User 1 attempts to view contest2 details with wrong password -> Fails
    - User 1 attempts to view contest2 details with correct password -> Succeeds.
    - Admin attempts to view contest 2 details with no password -> Succeeds.

## 4. Text Creation
    - User 1 creates a text (Text 1.1) using the manual text editor. Get text1_1_id.
        - Verify text title, content, and author fields are correctly stored.
    - User 2 creates a text (Text 2.1) using the manual text editor. Get text2_1_id.
        - Verify text title, content, and author fields are correctly stored.
    - User 1 attempts to view Text 2.1 details -> Succeeds (texts are public by default).
    - User 1 tries to edit Text 2.1 -> Fails (only owners can edit their texts).
    - User 2 edits Text 2.1 -> Succeeds.
    - User 1 tries to use writer1 to generate a text -> Fails (no credits)
        - Verify User 1's credit balance is not affected.
    - Admin assigns 50 credits to User 1 and 100 credits to User 2.
    - User 1 attempts to use writer1 to generate a text -> Succeeds, creating Text 1.2.
        - Verify User 1's credit balance decreases. Get record of transaction cost.
        - Verify User 2's credit balance is not affected.
    - User 2 attempts to use writer1 to generate a text -> Fails (no access to User 1's private agent).
    - User 2 uses the global writer (writer_global) to generate a text (Text 2.2).
        - Verify User 2's credit balance decreases. Get record of transaction cost.
        - Verify User 1's credit balance is not affected.
    - User 1 creates another text (Text 1.3) manually.
    - User 2 creates another text (Text 2.3) manually.
    - Admin creates a text (Text 3.1) manually.
    - Admin uses writer_global to create a text (Text 3.2).
        - Verify transaction is recorded against admin's account.
    - Admin uses writer1 to create a text (Text 3.3).
        - Verify transaction is recorded against admin's account.
        - Verify User 1's credit balance is not affected.

## 5. Text Submission Phase (Contest Open)
    # Testing multiple submissions per user allowed
    - User 2 submits Text 2.1 to contest1. Get submission_id.
    - User 2 submits Text 2.2 to contest1. Verify success.
        - Verify contest1 shows updated text count and participant count.
    
    # Testing multiple submissions per user not allowed
    - User 1 submits Text 1.1 to contest2. Verify success.
    - User 1 attempts to submit Text 1.2 to contest2 -> Fails due to owner_restrictions.
        - Note: Even though Text 1.1 and 1.2 might have different "author" strings, they're owned by the same user.
    
    # Testing judge participation restriction
    - User 2 attempts to submit Text 2.3 to contest2 -> Fails due to judge_restrictions.
    
    # Testing AI-generated text submissions
    - User 1 submits AI-generated Text 1.2 to contest1. Verify success.
    - Admin submits AI-generated Text 3.2 to contest1. Verify success.
    
    # Testing submission visibility rules
    - User 1 attempts to view all submissions for contest1 -> Should succeed as contest creator.
    - User 2 attempts to view all submissions for contest1 -> Should fail as non-creator during open phase.
    - Visitor attempts to view submissions for contest1 -> Should fail during open phase.
    - Admin views submissions for contest1 -> Should succeed.
        - Verify only accepted submissions are present.
    
    # Testing submission management
    - User 1 deletes their submission of Text 1.1 from contest2 -> Should succeed.
        - Verify updated submission list no longer contains Text 1.1.
    - User 1 attempts to delete User 2's submission (Text 2.1) from contest1 -> Should fail.
    - Admin deletes User 1's submission of Text 1.2 from contest1 -> Should succeed.
        - Verify the actual Text 1.2 still exists, only the submission was removed.
        - Verify the AI generation transaction cost record is not affected.

## 6. Evaluation Phase (Contest in Evaluation)
    - User 1 sets contest1 status to 'Evaluation'.
    - User 1 attempts to submit a new text to contest1 -> Should fail (400/403).
    - Visitor attempts to view submissions for contest1 -> Should succeed, author names masked.
    - User 2 (human judge) views submissions for contest1 -> Should succeed, author names masked.
    - User 1 attempts to vote in contest 1 -> Should fail (is not a judge).
    - User 2 attempts to vote in contest 1 -> Should succeed.
    - User 1 triggers judge_global evaluation for contest1. Succeeds.
        - Verify User 1's credit balance decreased.
    - Admin triggers human judge evaluation for contest1. Succeeds.
    - Admin triggers judge_1 (AI judge) evaluation for contest1. Succeeds.
        - Verify User 1's credit balance is not decreased. Verify transaction cost is recorded.
    - Admin triggers judge_global (AI judge) evaluation for contest2. Fails. Contest is not in evaluation. Verify no cost is recorded.
    - Admin sets contest2 status to 'Evaluation'.
    - Admin sets contest3 status to 'Evaluation'.
    - Admin assigns User 1 as a human judge for contest2.
    - User 1 submits votes/evaluation for contest2.

## 7. Contest Closure & Results
    - Admin sets contest1, contest2 and contest3 status to 'Closed'.
    - Visitor views contest1 details -> Should see results, author names revealed.
    - User 1 changes contest 1 to private.
    - Visitor attempts to view contest1 details with no password -> Fails
    - Visitor attempts to view contest1 details with correct password -> Succeeds. Author names revealed.
    - User 1 returns contest1 to public.
    - Visitor attempts to view contest1 details with no password -> Succeeds. Author names revealed.
    - User 2 deletes their own Text 2.1 from contest1 -> Should succeed.
    - User 1 attempts to delete Text 2.2 from contest1 -> Should succeed as it is its own contest.
   
## 8. Cost & Usage Monitoring (Pre-Cleanup)
    - Admin checks AI costs summary.
    - Admin checks User 1's credit history.
    - Admin checks User 2's credit history.
    - User 1 checks their credit balance.
    - User 2 checks their credit balance.

## 9. Cleanup Routine
    - User 2 tries to delete contest 1 -> Should fail.
    - User 1 deletes contest 1 -> Should succeed.
        - Verify associated votes are deleted.
        - Verify associated submissions are not deleted.
    - User 2 attempts to delete judge1 -> Should fail.
    - User 1 deletes their AI writer (writer1).
        - Verify associated submissions are not deleted.
    - User 1 deletes their AI judge (judge1).
        - Verify associated votes are not deleted.
    - Admin deletes contest2 and contest3.
    - User 2 attempts to delete writer_global -> Should fail.
    - Admin deletes global AI writer (writer_global).
    - Admin deletes global AI judge (judge_global).
    - User 1 deletes User 1.
        - Verify associated submissions are deleted from him and from his AI agents.
    - Admin deletes User 2.
        - Verify associated submissions are deleted from him and from his AI agents.

## 10. Final State Verification & Cost Monitoring (Post-Cleanup)
    - Verify all users, contests, AI agents, submissions, votes created in the test are deleted.
    - Admin checks AI costs summary again, it is not affected.
"""