Avoid editing or creating in /tests instead of /backend/tests
If running into trouble due to migrations, delete all migrations and build from scratch. Avoid the --> upgrade_head, fail, stamp head, upgrade head, fail cycle. Just delete and start fresh.
When running the tests, the goal is to get the app to work as intended in the project_description.md. So if a test fails, try a solution that is compliant with the project_description.md.
Visitors can indeed see private contests, but to see the detail they need the password. That is it. They do not need to be logged in.
