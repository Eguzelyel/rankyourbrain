from flask import Flask, render_template, request, url_for, redirect, send_from_directory, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from questions import Questions
from models import db, User, UserProgress, UserSession
import settings
import os
from pathlib import Path
from waitress import serve

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

    return render_template('profile.html', 
                          user=current_user, 
                          progress=user_progress, 
                          session=user_session)

@app.route('/get_question', methods=['GET', 'POST'])
@login_required
def get_question():
    """Get a random question and display it"""
    # Get user session
    user_session = UserSession.query.filter_by(user_id=current_user.id).first()

    # Get a random question
    question = questions.select_question_random()

    # Update user session with current question
    user_session.last_question_subject = question.subject
    user_session.last_question_name = question.name
    db.session.commit()

    # Render the question template with the question data
    return render_template('question.html', question=question)

@app.route('/question_image/<path:filename>')
def question_image(filename):
    """Serve question images from the question_bank directory"""
    question_bank_dir = Path(settings.questions_path).parent
    return send_from_directory(question_bank_dir, filename)

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

                # Record the user's progress
                progress = UserProgress(
                    user_id=current_user.id,
                    subject=subject,
                    question_name=name,
                    correct=correct
                )
                db.session.add(progress)

                # Update user session
                user_session = UserSession.query.filter_by(user_id=current_user.id).first()
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

@app.route('/leaderboard')
def get_leaderboard():
    """Display the leaderboard"""
    # Get all users and their sessions
    users = User.query.all()
    sessions = UserSession.query.all()

    # Create a list of users with their scores
    leaderboard = []
    for user in users:
        session = next((s for s in sessions if s.user_id == user.id), None)
        if session:
            leaderboard.append({
                'user': user,
                'correct': session.correct_answers,
                'total': session.total_questions,
                'score': session.correct_answers / max(1, session.total_questions) * 100
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
                          competition="Brain Quiz")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=8000, debug=True)
    # serve(app, host="0.0.0.0", port=8000)
