from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def judge_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allows admins OR judges
        if not current_user.is_authenticated or not (current_user.role == 'judge' or current_user.is_admin()):
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# Add other decorators here if needed (e.g., judge_required) 