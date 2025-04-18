#!/usr/bin/env python
import sys
import os
# Add project root to path if necessary (if running from different directory)
# sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, Contest, Submission, Vote
from app.contest.routes import calculate_contest_results
from datetime import datetime, timedelta, timezone

# Create app instance and push context
app = create_app()
app_context = app.app_context()
app_context.push()

def seed_data():
    """Creates mock users, contest, submissions, votes and calculates results."""
    print("--- Starting Mock Data Seeding ---")

    print("--- Step 1: Clearing existing data --- ")
    try:
        # Clear votes first
        num_votes = db.session.query(Vote).delete()
        # Clear submissions
        num_submissions = db.session.query(Submission).delete()
        # Detach judges
        db.session.execute(db.text('DELETE FROM contest_judges'))
        # Clear contests
        num_contests = db.session.query(Contest).delete()
        # Clear users (except maybe keep admin? No, clear all for clean slate)
        num_users = db.session.query(User).delete()
        db.session.commit()
        print(f"Cleared: {num_users} users, {num_contests} contests, {num_submissions} submissions, {num_votes} votes.")
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing data (might be empty already or DB doesn't exist): {e}")
        print("Please ensure the database exists (run flask run/python run.py once) before seeding.")
        # Optional: Exit if clearing fails and we need a clean slate
        # return

    print("--- Step 2: Creating Admin and Judges --- ")
    admin = None
    j1, j2, j3 = None, None, None
    try:
        admin = User(username='Hefesto', email='admin@example.com', role='admin')
        admin.set_password('itaca')
        j1 = User(username='juez1', email='juez1@example.com', role='judge')
        j1.set_password('password')
        j2 = User(username='juez2', email='juez2@example.com', role='judge')
        j2.set_password('password')
        j3 = User(username='juez3', email='juez3@example.com', role='judge')
        j3.set_password('password')
        db.session.add_all([admin, j1, j2, j3])
        db.session.commit()
        print("Admin and Judges created.")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating users: {e}")
        return # Stop if users can't be created

    print("--- Step 3: Creating Contest --- ")
    contest = None
    try:
        past_date = datetime.utcnow() - timedelta(days=1)
        contest = Contest(
            title='Concurso Simulado Completo',
            description='Este es un concurso de prueba con datos simulados.',
            end_date=past_date,
            status='evaluation',
            required_judges=3,
            contest_type='public'
        )
        db.session.add(contest)
        db.session.flush() # Ensure contest gets an ID before assigning judges
        contest.judges.append(j1)
        contest.judges.append(j2)
        contest.judges.append(j3)
        db.session.commit()
        print(f"Contest '{contest.title}' created (ID: {contest.id}) and judges assigned.")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating contest: {e}")
        return # Stop if contest can't be created

    print("--- Step 4: Creating Submissions --- ")
    submissions_data = [
        {'author': 'Autor Uno', 'title': 'Poema del Alba', 'text': 'Texto del poema del alba...'},        # ID -> 1 (likely)
        {'author': 'Autor Dos', 'title': 'Relato Nocturno', 'text': 'Texto del relato nocturno...'},     # ID -> 2
        {'author': 'Autor Tres', 'title': 'Ensayo Breve', 'text': 'Texto del ensayo breve...'},        # ID -> 3
        {'author': 'Autor Cuatro', 'title': 'Microrrelato Fugaz', 'text': 'Texto del microrrelato...'}, # ID -> 4
        {'author': 'Autor Cinco', 'title': 'Canción Olvidada', 'text': 'Texto de la canción...'}           # ID -> 5
    ]
    submissions = []
    try:
        for i, data in enumerate(submissions_data):
            sub = Submission(
                author_name=data['author'],
                title=data['title'],
                text_content=data['text'],
                contest_id=contest.id
            )
            submissions.append(sub)
        db.session.add_all(submissions)
        db.session.commit()
        # Refresh submissions to get IDs correctly assigned by DB
        submissions = db.session.scalars(db.select(Submission).where(Submission.contest_id == contest.id)).all()
        print(f"{len(submissions)} submissions created.")
        if len(submissions) != 5:
            print("Warning: Less than 5 submissions created/found.")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating submissions: {e}")
        return # Stop if submissions fail

    print("--- Step 5: Creating Votes (Rankings) --- ")
    # Define rankings using Submission IDs (more robust than index)
    # Ensure the submissions list is correctly populated with IDs
    sub_ids = {s.title: s.id for s in submissions}
    if len(sub_ids) != 5:
         print("Error: Could not get IDs for all 5 submissions. Aborting vote creation.")
         return

    rankings = {
        j1.id: [(sub_ids['Poema del Alba'], 1), (sub_ids['Relato Nocturno'], 2), (sub_ids['Ensayo Breve'], 3), (sub_ids['Microrrelato Fugaz'], 4), (sub_ids['Canción Olvidada'], None)],
        j2.id: [(sub_ids['Canción Olvidada'], 1), (sub_ids['Poema del Alba'], 2), (sub_ids['Microrrelato Fugaz'], 3), (sub_ids['Relato Nocturno'], 4), (sub_ids['Ensayo Breve'], None)],
        j3.id: [(sub_ids['Poema del Alba'], 1), (sub_ids['Ensayo Breve'], 2), (sub_ids['Canción Olvidada'], 3), (sub_ids['Microrrelato Fugaz'], 4), (sub_ids['Relato Nocturno'], None)]
    }
    comments = {
        j1.id: "Buenos textos en general, destacando el primero.",
        j2.id: "Variedad interesante, el quinto me pareció el más original.",
        j3.id: "Decisión difícil, varios con mérito."
    }

    votes_to_add = []
    try:
        for judge_id, judge_ranking in rankings.items():
            comment_added = False
            vote_for_comment = None # Track the vote object to add comment to
            highest_rank = 5

            for sub_id, place in judge_ranking:
                comment_text = None
                vote = Vote(
                    judge_id=judge_id,
                    submission_id=sub_id,
                    place=place,
                    comment=None # Assign later
                )
                votes_to_add.append(vote)
                # Track highest ranked vote to add comment later
                if place is not None and place < highest_rank:
                    highest_rank = place
                    vote_for_comment = vote

            # Add the comment to the highest ranked vote
            if vote_for_comment and judge_id in comments:
                 vote_for_comment.comment = comments[judge_id]

        db.session.add_all(votes_to_add)
        db.session.commit()
        print("Votes created.")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating votes: {e}")
        return

    print("--- Step 6: Calculating Results --- ")
    try:
        success = calculate_contest_results(contest.id)
        if success:
            print("Results calculated successfully. Contest should now be closed.")
            # Verify ranks (optional)
            final_submissions = db.session.scalars(db.select(Submission).where(Submission.contest_id == contest.id).order_by(Submission.final_rank.asc().nulls_last())).all()
            for sub in final_submissions:
                print(f"  Submission '{sub.title}': Rank={sub.final_rank}, Points={sub.total_points}")
        else:
            print("Result calculation failed or not triggered (maybe not enough judges voted according to logic?).")
    except Exception as e:
        print(f"Error calculating results: {e}")

    print("--- Mock Data Seeding Complete ---")

if __name__ == '__main__':
    seed_data()
    # Pop the context
    app_context.pop() 