from app import create_app, db
from app.models import User, Contest, UserRole, JudgeType
import sys
from flask_login import current_user

app = create_app()

def check_contest_judges(contest_id):
    with app.app_context():
        # Get contest details
        contest = db.session.get(Contest, contest_id)
        if not contest:
            print(f"Contest with ID {contest_id} not found")
            return
            
        print(f"Contest: {contest.title}")
        print(f"Status: {contest.status}")
        print(f"Required judges: {contest.required_judges}")
        
        # Get assigned judges
        judges = list(contest.judges)
        print(f"Assigned judges ({len(judges)}):")
        for judge in judges:
            print(f"  - {judge.username} (role: {judge.role.value}, type: {judge.judge_type.value if judge.judge_type else 'None'})")
            
        # Get all users with judge role
        all_judges = User.query.filter(User.role == UserRole.JUDGE).all()
        print(f"\nAll users with JUDGE role ({len(all_judges)}):")
        for judge in all_judges:
            print(f"  - {judge.username} (type: {judge.judge_type.value if judge.judge_type else 'None'})")
            
        # Get all admins
        admins = User.query.filter(User.role == UserRole.ADMIN).all()
        print(f"\nAll users with ADMIN role ({len(admins)}):")
        for admin in admins:
            print(f"  - {admin.username}")
        
        # Get all users
        users = User.query.all()
        print(f"\nAll users ({len(users)}):")
        for user in users:
            print(f"  - {user.username} (role: {user.role.value}, type: {user.judge_type.value if user.judge_type else 'None'})")
            
        print("\nTo assign a judge to this contest, use the admin panel or run this command:")
        print(f"python3 -c \"from app import create_app, db; from app.models import User, Contest; app = create_app(); with app.app_context(): contest = db.session.get(Contest, {contest_id}); judge = User.query.filter_by(username='JUDGE_USERNAME').first(); contest.judges.append(judge); db.session.commit(); print('Judge assigned successfully')\"")
            
if __name__ == "__main__":
    contest_id = 1  # Default contest ID
    if len(sys.argv) > 1:
        contest_id = int(sys.argv[1])
    check_contest_judges(contest_id) 