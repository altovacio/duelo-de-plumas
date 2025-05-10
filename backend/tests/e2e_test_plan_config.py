# backend/tests/e2e_test_plan_config.py

e2e_test_plan = """
# E2E Test Plan: Full Application Workflow

## 1. Setup & User Registration
    1.01- Admin logs in (obtain admin_token).
    1.02- User 1 registers themselves.
            - Verify successful registration and initial credit balance (should be 0).
    1.03- Obtain user1_token after login.
    1.04- Admin registers User 2.
            - Verify successful registration and initial credit balance (should be 0).
    1.05- User 2 logs in (obtain user2_token).
    1.06- Admin verifies User 1 and User 2 details and credit balances. Get user1_id and user2_id.

## 2. AI Agent Creation
    2.01- User 1 creates an AI Writer (writer1). Get writer1_id.
    2.02- User 1 creates an AI Judge (judge1). Get judge1_id.
    2.03- Admin creates a global AI Writer (writer_global). Get writer_global_id.
    2.04- Admin creates a global AI Judge (judge_global). Get judge_global_id.
    2.05- User 1 lists their AI agents, verifies writer1 and judge1 are present and also the global writer and judge are present.
    2.06- User 2 lists their AI agents, verifies they see none but the global writer and judge.
    2.07- Admin lists global AI agents, verifies they see all four agents.

## 3. Contest Creation & Management
    3.01- User 1 creates a public Contest (contest1). Get contest1_id.
            - They do not limit the number of submissions per user.
            - They do not restrict judges from participating as text submitters.
            - They assign judge_global as judge.
    3.02- Admin creates a private Contest (contest2), setting a password.
            - They assign User 2, judge1 and judge_global as judges.
            - They restrict judges from participating as text submitters.
            - They restrict the number of submissions per user to 1.
    3.03- User 2 creates a contest (contest3) with no judges assigned. Succeeds
    3.04- User 2 attempts to edit contest1 -> Should fail.
    3.05- User 1 edits contest1 (updates description). Verify success.
    3.06- Admin edits contest3 (updates description). Verify success.
    3.07- User 2 attempts to assign judge1 to contest 3. Fails
    3.08- User 1 attempts to assign judge1 to contest 3. Fails
    3.09- User 1 attempts to assign user 1 to contest 3. Fails
    3.10- User 1 attempts to assign judge1 and user 2 as judges to contest 1. Succeeds
    3.11- User 2 attempts to assign user 2 as a judge to contest 3. Succeeds
    3.12- Visitor lists contests. Sees all but the private contest with limited details.
    3.13- User 1 lists contests. Sees all but the private contest with limited details.
    3.14- Visitor attempts to view contest2 details with wrong password -> Fails
    3.15- Visitor attempts to view contest2 details with correct password -> Succeeds.
    3.16- User 1 attempts to view contest2 details with wrong password -> Fails
    3.17- User 1 attempts to view contest2 details with correct password -> Succeeds.
    3.18- Admin attempts to view contest 2 details with no password -> Succeeds.

## 4. Text Creation
    4.01- User 1 creates a text (Text 1.1) using the manual text editor. Get text1_1_id.
            - Verify text title, content, and author fields are correctly stored.
    4.02- User 2 creates a text (Text 2.1) using the manual text editor. Get text2_1_id.
            - Verify text title, content, and author fields are correctly stored.
    4.03- User 1 attempts to view Text 2.1 details -> Succeeds (texts are public by default).
    4.04- User 1 tries to edit Text 2.1 -> Fails (only owners can edit their texts).
    4.05- User 2 edits Text 2.1 -> Succeeds.
    4.06- User 1 tries to use writer1 to generate a text -> Fails (no credits)
            - Verify User 1\'s credit balance is not affected.
    4.07- Admin assigns 50 credits to User 1 and 100 credits to User 2.
    4.08- User 1 attempts to use writer1 to generate a text -> Succeeds, creating Text 1.2.
            - Verify User 1\'s credit balance decreases. Get record of transaction cost.
            - Verify User 2\'s credit balance is not affected.
    4.09- User 2 attempts to use writer1 to generate a text -> Fails (no access to User 1\'s private agent).
    4.10- User 2 uses the global writer (writer_global) to generate a text (Text 2.2).
            - Verify User 2\'s credit balance decreases. Get record of transaction cost.
            - Verify User 1\'s credit balance is not affected.
    4.11- User 1 creates another text (Text 1.3) manually.
    4.12- User 2 creates another text (Text 2.3) manually.
    4.13- Admin creates a text (Text 3.1) manually.
    4.14- Admin uses writer_global to create a text (Text 3.2).
            - Verify transaction is recorded against admin\'s account.
    4.15- Admin uses writer1 to create a text (Text 3.3).
            - Verify transaction is recorded against admin\'s account.
            - Verify User 1\'s credit balance is not affected.

## 5. Text Submission Phase (Contest Open)
    # Testing multiple submissions per user allowed (Contest 1 - no owner_restrictions)
    5.01- User 2 submits Text 2.1 to contest1. Get submission_id_c1_t2_1.
    5.02- User 2 submits Text 2.2 to contest1. Get submission_id_c1_t2_2. Verify success.
            - Verify contest1 shows updated text count and participant count.
    5.03- User 1 submits AI-generated Text 1.2 to contest1. Get submission_id_c1_t1_2. Verify success.
            - Verify contest1 shows updated text count and participant count.
    5.04- User 1 submits manual Text 1.3 to contest1. Get submission_id_c1_t1_3. Verify success.
            - Verify contest1 shows updated text count and participant count.
    5.05- User 2 submits manual Text 2.3 to contest1. Get submission_id_c1_t2_3. Verify success.
            - Verify contest1 shows updated text count and participant count.

    # Testing multiple submissions per user not allowed (Contest 2 - owner_restrictions=True)
    5.06- User 1 submits Text 1.1 to contest2. Get submission_id_c2_t1_1. Verify success.
    5.07- User 1 attempts to submit Text 1.3 (another owned text) to contest2 -> Fails due to owner_restrictions.
            - Note: Tests restriction for texts owned by the same user.

    # Testing judge participation restriction (Contest 2 - judge_restrictions=True)
    5.08- User 2 (who is a judge for contest2) attempts to submit Text 2.3 to contest2 -> Fails due to judge_restrictions.

    # Testing AI-generated text submissions (continued)
    5.09- Admin submits AI-generated Text 3.2 to contest1. Get submission_id_c1_t3_2. Verify success.
            - Verify contest1 shows updated text count and participant count.

    # Testing submission visibility rules (Contest 1 - Open Phase)
    5.10- User 1 (creator) views submissions for contest1 -> Should succeed, details unmasked.
    5.11- User 2 (non-creator participant) attempts to view submissions for contest1 -> Should fail.
    5.12- Visitor attempts to view submissions for contest1 -> Should fail.
    5.13- Admin views submissions for contest1 -> Should succeed, details unmasked.
            - Verify only accepted submissions are present.

    # Testing submission management
    5.14- User 1 deletes their own AI-text submission (submission_id_c1_t1_2) from contest1.
            - Verify success and updated contest counts.
            - Verify User 1\'s credits are NOT affected (AI generation cost is sunk and not refunded).
    5.15- User 2 deletes their own manual submission (submission_id_c1_t2_1) from contest1.
            - Verify success and updated contest counts.
    5.16- User 1 deletes their own manual submission (submission_id_c2_t1_1) from contest2.
            - Verify success and updated contest counts.
            - Verify updated submission list no longer contains the text.
    5.17- User 1 (creator of contest1) deletes User 2\'s submission (submission_id_c1_t2_2) from contest1.
            - Verify success and updated contest counts.
    5.18- User 1 re-submits AI-generated Text 1.2 to contest1. Get new submission_id_c1_t1_2_v2.
            - Verify User 1 credits are NOT charged again for re-submission of existing AI text.
    5.19- Admin deletes User 1\'s re-submitted AI text submission (submission_id_c1_t1_2_v2) from contest1.
            - Verify success.
            - Verify the actual Text 1.2 still exists (only submission removed).
            - Verify User 1\'s credits are NOT affected.

## 6. Evaluation Phase (Contest in Evaluation)
    6.01- User 1 sets contest1 status to \'Evaluation\'.
    6.02- User 1 attempts to submit a new text to contest1 -> Should fail due to contest being in evaluation phase.
    6.03- Visitor attempts to view submissions for contest1 -> Should succeed, user and author names masked.
    6.04- User 2 (human judge) views submissions for contest1 -> Should succeed, user and author names masked.
    6.05- User 1 attempts to vote in contest 1 -> Should fail (is not a judge).
    6.06- User 2 attempts to vote in contest 1 -> Should succeed.
    6.07- User 1 triggers judge_global evaluation for contest1. Succeeds.
            - Verify User 1\'s credit balance decreased.
    6.08- Admin triggers human judge evaluation for contest1. Succeeds.
    6.09- Admin triggers judge_1 (AI judge) evaluation for contest1. Succeeds.
            - Verify User 1\'s credit balance is not decreased. Verify transaction cost is recorded.
    6.10- Admin triggers judge_global (AI judge) evaluation for contest2. Fails. Contest is not in evaluation. Verify no cost is recorded.
    6.11- Admin sets contest2 status to \'Evaluation\'.
    6.12- Admin sets contest3 status to \'Evaluation\'.
    6.13- Admin assigns User 1 as a human judge for contest2.
    6.14- User 1 submits votes/evaluation for contest2.

## 7. Contest Closure & Results
    7.01- Admin sets contest1, contest2 and contest3 status to \'Closed\'.
    7.02- Visitor views contest1 details -> Should see results, user and author names revealed.
    7.03- User 1 changes contest 1 to private.
    7.04- Visitor attempts to view contest1 details with no password -> Fails
    7.05- Visitor attempts to view contest1 details with correct password -> Succeeds. User and author names revealed.
    7.06- User 1 returns contest1 to public.
    7.07- Visitor attempts to view contest1 details with no password -> Succeeds. User and author names revealed.
    7.08- User 2 deletes their own Text 2.1 from contest1 -> Should succeed.
    7.09- User 1 attempts to delete Text 2.2 from contest1 -> Should succeed.
            - Verify Cost records are not affected.
   
## 8. Cost & Usage Monitoring (Pre-Cleanup)
    8.01- Admin checks AI costs summary.
    8.02- Admin checks User 1\'s credit history.
    8.03- Admin checks User 2\'s credit history.
    8.04- User 1 checks their credit balance.
    8.05- User 2 checks their credit balance.

## 9. Cleanup Routine
    9.01- User 2 tries to delete contest 1 -> Should fail.
    9.02- User 1 deletes contest 1 -> Should succeed.
            - Verify associated votes are deleted.
    9.03- User 2 attempts to delete judge1 -> Should fail.
    9.04- User 1 deletes their AI writer (writer1).
            - Verify associated submissions are not deleted.
    9.05- User 1 deletes their AI judge (judge1).
            - Verify associated votes are not deleted.
            - Verify costs are not affected
    9.06- Admin deletes contest2 and contest3.
    9.07- User 2 attempts to delete writer_global -> Should fail.
    9.08- Admin deletes global AI writer (writer_global).
    9.09- Admin deletes global AI judge (judge_global).
    9.10- User 1 deletes User 1.
            - Verify associated submissions are deleted from him and from his AI agents.
    9.11- Admin deletes User 2.
            - Verify associated submissions are deleted from him and from his AI agents.

## 10. Final State Verification & Cost Monitoring (Post-Cleanup)
    10.01- Verify all users, contests, AI agents, submissions, votes created in the test are deleted.
    10.02- Admin checks AI costs summary again, it is not affected.
"""

# This file can also include common configurations or imports if needed later,
# but for now, it primarily serves to hold the e2e_test_plan. 