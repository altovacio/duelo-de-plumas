from flask import render_template, url_for, redirect, request, session, jsonify
from flask_login import current_user
from app.main import bp
from app.models import Contest, User, Submission, Vote # Import Vote
from app import db
from datetime import datetime, timezone
from sqlalchemy import or_ # Import or_
# Import specific functions from the refactored config
from app.roadmap.config import (
    get_roadmap_items as config_get_items,
    add_roadmap_item as config_add_item,
    delete_roadmap_item as config_delete_item,
    update_single_item_status as config_update_status
)

@bp.route('/')
@bp.route('/index')
def index():
    current_time = datetime.utcnow() # Naive datetime
    aware_current_time = datetime.now(timezone.utc) # Aware datetime for comparison
    
    # Build the base query for active contests - show ALL contests (public and private)
    # Include contests with no end date
    active_contests_query = db.select(Contest) \
        .where(Contest.status == 'open') \
        .where(or_(Contest.end_date > aware_current_time, Contest.end_date.is_(None))) \
        .order_by(Contest.end_date.asc()) # Nulls likely first, which is ok
    
    # Fetch all contests - both public and private
    active_contests = db.session.scalars(active_contests_query).all()

    # Fetch recently closed contests - all of them
    closed_contests = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'closed')
        .order_by(Contest.end_date.desc()) # Nulls likely last here
    ).all()

    # Fetch pending evaluations for the current judge
    judge_assigned_evaluations = []
    if current_user.is_authenticated and current_user.role == 'judge':
        judge_assigned_evaluations = db.session.scalars(
            db.select(Contest)
            .where(Contest.status == 'evaluation')
            .where(Contest.judges.any(User.id == current_user.id))
            .order_by(Contest.end_date.asc()) # Nulls likely first
        ).all()
    
    # Fetch contests requiring AI evaluations (for admins) and expired open contests
    pending_ai_evaluations = []
    expired_open_contests = [] # Initialize list for expired open contests
    if current_user.is_authenticated and current_user.is_admin():
        # --- Find Expired Open Contests ---
        expired_open_contests = db.session.scalars(
            db.select(Contest)
            .where(Contest.status == 'open')
            .where(Contest.end_date.is_not(None))
            .where(Contest.end_date <= aware_current_time) # Compare with aware time
            .order_by(Contest.end_date.asc())
        ).all()

        # --- Find Contests Pending AI Evaluation ---
        # Get contests in evaluation phase with assigned AI judges
        evaluation_contests = db.session.scalars(
            db.select(Contest)
            .where(Contest.status == 'evaluation')
            .order_by(Contest.end_date.asc())
        ).all()
        
        for contest in evaluation_contests:
            # Get AI judges assigned to the contest
            ai_judges = db.session.scalars(
                db.select(User)
                .where(User.role == 'judge', User.judge_type == 'ai')
                .join(User.judged_contests)
                .where(Contest.id == contest.id)
            ).all()
            
            if ai_judges:
                # Get judges that have already voted
                judges_with_votes = set(db.session.scalars(
                    db.select(Vote.judge_id).distinct()
                    .join(Vote.submission)
                    .where(Submission.contest_id == contest.id)
                ).all())
                
                # Check if any AI judge hasn't voted yet
                for ai_judge in ai_judges:
                    if ai_judge.id not in judges_with_votes:
                        # Found an AI judge that hasn't evaluated yet
                        if contest not in pending_ai_evaluations:
                            pending_ai_evaluations.append(contest)
                            break

    return render_template('main/index.html', 
                           title='Inicio', 
                           active_contests=active_contests,
                           closed_contests=closed_contests,
                           judge_assigned_evaluations=judge_assigned_evaluations,
                           pending_ai_evaluations=pending_ai_evaluations,
                           expired_open_contests=expired_open_contests, 
                           Submission=Submission,
                           aware_now=aware_current_time, # Pass aware time for macro
                           timezone=timezone)          # Pass timezone object for macro

# New Route for listing all contests by status
@bp.route('/contests')
def list_contests():
    now = datetime.utcnow() # Naive
    aware_now = datetime.now(timezone.utc) # Aware for comparisons
    
    # Show ALL contests - both public and private (Still Open)
    contests_open = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'open')
        .where(or_(Contest.end_date > aware_now, Contest.end_date.is_(None))) # Compare with aware time
        .order_by(Contest.end_date.asc()) # Nulls likely first
    ).all()
    
    # --- New: Fetch Expired Open Contests ---
    contests_expired_open = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'open')
        .where(Contest.end_date.is_not(None))
        .where(Contest.end_date <= aware_now) # Compare with aware time
        .order_by(Contest.end_date.asc())
    ).all()
    
    # Show ALL contests in evaluation - both public and private
    contests_evaluation = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'evaluation')
        .order_by(Contest.end_date.desc()) # Nulls likely last
    ).all()
    
    # Show ALL closed contests - both public and private
    contests_closed = db.session.scalars(
        db.select(Contest)
        .where(Contest.status == 'closed')
        .order_by(Contest.end_date.desc()) # Nulls likely last
    ).all()
    
    # Judge specific list remains unchanged
    judge_assigned_evaluations = []
    if current_user.is_authenticated and current_user.role == 'judge':
        judge_assigned_evaluations = db.session.scalars(
            # Select contests where status is evaluation AND current user is in the judges list
            db.select(Contest)
            .where(Contest.status == 'evaluation')
            .where(Contest.judges.any(User.id == current_user.id)) # Check relationship
            .order_by(Contest.end_date.asc()) # Nulls likely first
        ).all()
    
    return render_template('main/contests.html', 
                           title='Concursos Literarios', 
                           contests_open=contests_open,
                           contests_expired_open=contests_expired_open, 
                           contests_evaluation=contests_evaluation,
                           contests_closed=contests_closed,
                           judge_assigned_evaluations=judge_assigned_evaluations,
                           Submission=Submission,
                           aware_now=aware_now,  # Pass aware time for macro
                           timezone=timezone)   # Pass timezone object for macro

# Hidden roadmap page - accessible via URL but not linked in navigation
@bp.route('/roadmap')
def roadmap():
    # Load roadmap items using the safe getter
    items = config_get_items()
    return render_template('main/roadmap.html', title='Roadmap', items=items)

# API endpoints for the roadmap items
@bp.route('/api/roadmap/items', methods=['GET'])
def get_roadmap_items_api():
    # Use the safe getter for the API as well
    return jsonify(config_get_items())

# Route for adding a new item
@bp.route('/api/roadmap/item', methods=['POST'])
def add_roadmap_item_api():
    item_data = request.json
    if not item_data or 'text' not in item_data:
        return jsonify({"success": False, "error": "Missing item text"}), 400
    
    new_item = config_add_item(item_data)
    # Return the full new item, including its ID, so the frontend can update
    return jsonify({"success": True, "item": new_item}), 201 # 201 Created

# Route for deleting an item
@bp.route('/api/roadmap/item/<int:item_id>', methods=['DELETE'])
def delete_roadmap_item_api(item_id):
    deleted = config_delete_item(item_id)
    if deleted:
        return jsonify({"success": True})
    else:
        # Item not found or error during deletion
        return jsonify({"success": False, "error": "Item not found or could not be deleted"}), 404

# New route for updating item status
@bp.route('/api/roadmap/item/<int:item_id>/status', methods=['PUT'])
def update_roadmap_item_status_api(item_id):
    data = None
    try:
        data = request.json
    except Exception as e:
        # Return a custom JSON error if parsing fails
        return jsonify({"success": False, "error": f"Failed to parse JSON body: {e}"}), 400

    if not data or 'status' not in data:
        return jsonify({"success": False, "error": "Missing status field"}), 400

    new_status = data['status']
    # Basic validation for status
    valid_statuses = {'backlog', 'in-progress', 'completed'}
    if new_status not in valid_statuses:
         return jsonify({"success": False, "error": f"Invalid status: {new_status}"}), 400

    updated = config_update_status(item_id, new_status)
    if updated:
        return jsonify({"success": True})
    else:
        # Item not found or error during update
        return jsonify({"success": False, "error": "Item not found or could not be updated"}), 404

# Add other main routes here (e.g., about page) 