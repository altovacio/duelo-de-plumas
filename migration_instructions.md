# Migration and Installation Instructions

## Changes Made

1. **Added Version Tracking**:
   - Added `app_version` field to `Vote`, `AIEvaluation`, and `AIWritingRequest` models
   - Created a central `APP_VERSION` constant in `models.py` set to "v1.02"
   - Updated templates to display version information

2. **Updated UI**:
   - Modified hero banner on the homepage
   - Added version tracking display for AI-generated texts
   - Added version tracking display for judge evaluations

3. **Updated Changelog**:
   - Added v1.02 entry with new features

## Required Actions

To complete the implementation, please follow these steps:

### 1. Apply Database Migrations

Run these commands in your project directory to create and apply the database migrations:

```bash
# Initialize migrations (only needed if this is your first migration)
flask db init

# If you see a message about editing alembic.ini, ensure your 
# Flask app's SQLALCHEMY_DATABASE_URI is properly configured and 
# that the app is correctly importing the config.

# Create migration
flask db migrate -m "Add app_version tracking to Vote, AIEvaluation, and AIWritingRequest models"

# Apply migration
flask db upgrade
```

#### Configuration Note
If you encounter issues with the database connection, you may need to ensure:

1. Your Flask app properly initializes Flask-Migrate with your Flask app and SQLAlchemy instance
2. The SQLALCHEMY_DATABASE_URI in your app's config points to a valid database
3. The environment variable for development/production mode is correctly set

If using a development environment, your setup might look like this in your app's __init__.py:

```python
from flask_migrate import Migrate
# ...other imports...

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    # ...
```

### 2. Testing

Please test the following functionality:

1. Verify the new hero section appears correctly on the homepage
2. Create a new submission with AI (as admin)
3. Evaluate submissions as a judge
4. Check the contest results page to verify version information appears for:
   - AI-generated text submissions
   - Judge evaluations

### 3. Additional Considerations

- If you're using SQLite as your database, the migration should be straightforward.
- If you're using a production database like PostgreSQL or MySQL, make sure to back up your database before applying migrations.
- Existing votes and AI-generated texts won't have version information until they're recreated.

## Future Enhancements

Consider these future enhancements to build upon this feature:

1. Add more detailed version tracking (git commit hash, deployment timestamp)
2. Create an admin dashboard to view version statistics
3. Add version filtering capability for contest evaluations 