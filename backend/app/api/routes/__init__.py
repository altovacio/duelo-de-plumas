from fastapi import APIRouter

# Remove the following problematic line:
# from app.api.routes import auth, users, texts, contests, votes, admin, dashboard, agents

# Keep the individual router imports if api_router is meant to aggregate them,
# but ensure they use relative imports if needed or that Python can find them.
# For now, assuming app.main.py directly imports the submodules like auth.py,
# this __init__.py doesn't strictly need to import them for app.main.py to work.

# If the intent is for app.main.py to import this api_router, then this part is fine.
from . import auth
from . import users
from . import texts
from . import contests
from . import votes
from . import admin
from . import dashboard
from . import agents

api_router = APIRouter()
# The following lines are commented out because app.main.py currently includes
# each router individually with its own prefix. If api_router is to be used
# as a central router, then app.main.py should include api_router, and these
# lines here should specify prefixes for each sub-router.
# api_router.include_router(auth.router)
# api_router.include_router(users.router)
# api_router.include_router(texts.router)
# api_router.include_router(contests.router)
# api_router.include_router(votes.router)
# api_router.include_router(admin.router)
# api_router.include_router(dashboard.router)
# api_router.include_router(agents.router) 