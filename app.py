from flask import Flask, render_template, request, url_for, redirect, send_from_directory, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from questions import Questions
from models import db, User, UserProgress, UserSession
from leaderboard import IQRanking
import settings

from pathlib import Path
from waitress import serve
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a random secret key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rankyourbrain.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize the Questions class
questions = Questions()

# Create database tables
@app.before_request # changed form before_first_request which is deprecated.
def create_tables():
    db.create_all()

@app.route('/')
@app.route('/index')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered.')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(first_name=first_name, last_name=last_name, email=email)
        new_user.set_password(password)

        # Add user to database
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log in a user"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if user and user.check_password(password):
            login_user(user)

            # Check if user has an active session
            user_session = UserSession.query.filter_by(user_id=user.id).first()
            if not user_session:
                user_session = UserSession(user_id=user.id)
                db.session.add(user_session)
                db.session.commit()

            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

        flash('Invalid email or password')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Log out a user"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """Display user profile and progress"""
    user_progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    user_session = UserSession.query.filter_by(user_id=current_user.id).first()

    # Calculate STEM and verbal IQ scores
    iq_ranking = IQRanking()
    stem_iq = iq_ranking.calculate_stem_iq(current_user.id)
    verbal_iq = iq_ranking.calculate_verbal_iq(current_user.id)

    return render_template('profile.html', 
                          user=current_user, 
                          progress=user_progress, 
                          session=user_session,
                          stem_iq=stem_iq,
                          verbal_iq=verbal_iq)

@app.route('/iq_scale')
def iq_scale():
    """Display information about IQ scale"""
    return render_template('iq_scale.html')

@app.route('/get_question', methods=['GET', 'POST'])
@login_required
def get_question():
    """Get a random question that the user hasn't answered yet and display it"""
    # Get user session
    user_session = UserSession.query.filter_by(user_id=current_user.id).first()

    # Get a random unanswered question
    question = questions.select_unanswered_question(current_user.id)

    # If all questions have been answered, show a message
    if question is None:
        flash('You have answered all available questions! Check your profile to review your progress.')
        return redirect(url_for('profile'))

    # Update user session with current question
    user_session.last_question_subject = question.subject
    user_session.last_question_name = question.name
    db.session.commit()

    # Render the question template with the question data
    return render_template('question.html', question=question)

@app.route('/get_specific_question', methods=['POST'])
@login_required
def get_specific_question():
    """Get a specific question by subject and name"""
    subject = request.form.get('subject')
    name = request.form.get('name')

    # Find the question in the questions collection
    question = None
    for q in questions.questions.get(subject, []):
        if q.name == name:
            question = q
            break

    if not question:
        flash('Question not found.')
        return redirect(url_for('profile'))

    # Get user session
    user_session = UserSession.query.filter_by(user_id=current_user.id).first()

    # Update user session with current question
    user_session.last_question_subject = question.subject
    user_session.last_question_name = question.name
    db.session.commit()

    # Render the question template with the question data
    return render_template('question.html', question=question)

@app.route('/question_image/<path:filename>')
def question_image(filename):
    """Serve question images from the question_bank directory"""
    # Use the static/question_bank directory directly
    return send_from_directory('static/question_bank', filename)

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    """Process the submitted answer"""
    user_answer = request.form.get('answer')
    question_id = request.form.get('question_id')

    # Parse question_id to get subject and name
    parts = str(question_id).split('_')
    if len(parts) >= 2:
        subject = parts[0]
        name = parts[1]

        # Get the question to check the answer
        for q in questions.questions.get(subject, []):
            if q.name == name:
                correct = (q.answer.lower() == user_answer.lower())
                stem_score = q.stem_weight if correct else q.stem_weight*(-0.2)
                verbal_score = q.verbal_weight if correct else q.verbal_weight*(-0.2)

                # Check if this question was previously answered or skipped by this user
                existing_progress = UserProgress.query.filter_by(
                    user_id=current_user.id,
                    subject=subject,
                    question_name=name
                ).first()

                # Update user session
                user_session = UserSession.query.filter_by(user_id=current_user.id).first()

                if existing_progress:
                    # Update the existing record
                    existing_progress.correct = correct
                    existing_progress.stem_score = stem_score
                    existing_progress.verbal_score = verbal_score
                    existing_progress.status = 'answered'
                    existing_progress.answered_at = datetime.datetime.now(datetime.UTC)

                    # Only increment total_questions if it was previously skipped
                    # and not counted as answered
                    if existing_progress.status == 'skipped':
                        user_session.total_questions += 1
                        if correct:
                            user_session.correct_answers += 1
                else:
                    # Create a new progress record
                    progress = UserProgress(
                        user_id=current_user.id,
                        subject=subject,
                        question_name=name,
                        correct=correct,
                        stem_score=stem_score,
                        verbal_score=verbal_score,
                        status='answered',
                    )
                    db.session.add(progress)

                    # Increment counters for new questions
                    user_session.total_questions += 1
                    if correct:
                        user_session.correct_answers += 1

                db.session.commit()

                # Flash message about the answer
                if correct:
                    flash('Correct answer!')
                else:
                    flash(f'Incorrect. The correct answer is {q.answer}.')

                break

    # Redirect to a new question
    return redirect(url_for('get_question'))

@app.route('/skip_question', methods=['POST'])
@login_required
def skip_question():
    """Process the skipped question. This should still add a row with -0.1 weight."""

    # Get the question_id from the form
    question_id = request.form.get('question_id')

    # Parse question_id to get subject and name
    parts = str(question_id).split('_')
    if len(parts) >= 2:
        subject = parts[0]
        name = parts[1]

        # Get the question
        for q in questions.questions.get(subject, []):
            if q.name == name:
                # Calculate scores with -0.1 weight
                stem_score = q.stem_weight * (-0.1)
                verbal_score = q.verbal_weight * (-0.1)

                # Check if this question was previously skipped by this user
                existing_progress = UserProgress.query.filter_by(
                    user_id=current_user.id,
                    subject=subject,
                    question_name=name
                ).first()

                if existing_progress:
                    # Update the existing record
                    existing_progress.correct = False
                    existing_progress.stem_score = stem_score
                    existing_progress.verbal_score = verbal_score
                    existing_progress.status = 'skipped'
                    existing_progress.answered_at = datetime.datetime.now(datetime.UTC)
                else:
                    # Create a new progress record
                    progress = UserProgress(
                        user_id=current_user.id,
                        subject=subject,
                        question_name=name,
                        correct=False,
                        stem_score=stem_score,
                        verbal_score=verbal_score,
                        status='skipped',
                    )
                    db.session.add(progress)

                # Update user session
                user_session = UserSession.query.filter_by(user_id=current_user.id).first()
                user_session.total_questions += 1
                db.session.commit()

                # Flash message about skipping
                flash('Question skipped. You can try it again later.')

                break

    # Redirect to a new question
    return redirect(url_for('get_question'))


@app.route('/leaderboard')
@app.route('/leaderboard/<leaderboard_type>')
def get_leaderboard(leaderboard_type='stem'):
    """Display the leaderboard for either STEM or verbal IQ"""
    # Validate leaderboard_type
    if leaderboard_type not in ['stem', 'verbal']:
        leaderboard_type = 'stem'

    # Get all users
    users = User.query.all()

    # Create IQ ranking instance
    iq_ranking = IQRanking()

    # Create a list of users with their IQ scores
    leaderboard = []
    for user in users:
        # Calculate the appropriate IQ score based on leaderboard_type
        if leaderboard_type == 'stem':
            iq_score = iq_ranking.calculate_stem_iq(user.id)
            competition = "STEM IQ Leaderboard"
        else:
            iq_score = iq_ranking.calculate_verbal_iq(user.id)
            competition = "Verbal IQ Leaderboard"

        # Only include users with scores > 0
        if iq_score > 0:
            leaderboard.append({
                'user': user,
                'score': iq_score
            })

    # Sort by score (descending)
    leaderboard.sort(key=lambda x: x['score'], reverse=True)

    # Find current user's rank
    user_rank = next((i+1 for i, entry in enumerate(leaderboard)
                     if entry['user'].id == current_user.id), None) if current_user.is_authenticated else None

    return render_template('leaderboard.html',
                          leaderboard=leaderboard,
                          user=current_user.first_name if current_user.is_authenticated else "Guest",
                          user_rank=user_rank,
                          competition=competition,
                          leaderboard_type=leaderboard_type)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8000, debug=True)
    # serve(app, host="0.0.0.0", port=8000)
