from app import create_app, db
from app.models import User, Contest, UserRole, JudgeType
import sys

app = create_app()

def assign_judge(contest_id, judge_username):
    with app.app_context():
        # Get the contest
        contest = db.session.get(Contest, contest_id)
        if not contest:
            print(f"Contest with ID {contest_id} not found")
            return
            
        # Get the judge
        judge = User.query.filter_by(username=judge_username).first()
        if not judge:
            print(f"User with username '{judge_username}' not found")
            return
            
        # Check if judge is already assigned
        if judge in contest.judges:
            print(f"Judge '{judge_username}' is already assigned to this contest")
            return
            
        # Assign judge to contest
        contest.judges.append(judge)
        db.session.commit()
        print(f"Judge '{judge_username}' assigned to contest '{contest.title}' successfully")
        
        # Check assignment
        print(f"\nJudges for contest '{contest.title}':")
        for j in contest.judges:
            print(f"  - {j.username} (role: {j.role.value}, type: {j.judge_type.value if j.judge_type else 'None'})")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 assign_judge.py <contest_id> <judge_username>")
        print("Example: python3 assign_judge.py 1 222")
        sys.exit(1)
        
    contest_id = int(sys.argv[1])
    judge_username = sys.argv[2]
    assign_judge(contest_id, judge_username) 