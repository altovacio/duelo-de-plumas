from app import create_app, db
from app.models import User, UserRole, JudgeType
import sys

app = create_app()

def check_users():
    with app.app_context():
        # Get all users
        users = User.query.all()
        print(f"All users ({len(users)}):")
        for user in users:
            print(f"  - {user.username} (role: {user.role.value}, email: {user.email})")
    
        # Check if there's an admin user
        admin_users = User.query.filter(User.role == UserRole.ADMIN).all()
        if not admin_users:
            print("\nNo admin users found. You should create one.")
            print("To create an admin, run:")
            print('python3 -c "from app import create_app, db; from app.models import User, UserRole; app = create_app(); with app.app_context(): user = User(username=\'admin\', email=\'admin@example.com\', role=UserRole.ADMIN); user.set_password(\'password\'); db.session.add(user); db.session.commit(); print(\'Admin user created\')"')
        else:
            print(f"\nAdmin users found: {len(admin_users)}")
            
        # Check if there are any judge users
        judge_users = User.query.filter(User.role == UserRole.JUDGE).all()
        if not judge_users:
            print("\nNo judge users found. You should create one.")
            print("To create a judge, run:")
            print('python3 -c "from app import create_app, db; from app.models import User, UserRole, JudgeType; app = create_app(); with app.app_context(): user = User(username=\'judge\', email=\'judge@example.com\', role=UserRole.JUDGE, judge_type=JudgeType.HUMAN); user.set_password(\'password\'); db.session.add(user); db.session.commit(); print(\'Judge user created\')"')
        else:
            print(f"\nJudge users found: {len(judge_users)}")
    
if __name__ == "__main__":
    check_users() 