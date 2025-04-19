from app import create_app, db
from app.models import Contest
import datetime

app = create_app()

# This script extends the end date of contest #1 by 30 days
with app.app_context():
    contest = db.session.get(Contest, 1)
    if contest:
        old_date = contest.end_date
        print(f'Old end date: {old_date}')
        contest.end_date = datetime.datetime.now() + datetime.timedelta(days=30)
        db.session.commit()
        # Reload the contest to confirm changes
        contest = db.session.get(Contest, 1)
        print(f'New end date: {contest.end_date}')
    else:
        print("Contest #1 not found") 