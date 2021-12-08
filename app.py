from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError
import os


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///flask_feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'hellosecret1')
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
toolbar = DebugToolbarExtension(app)

@app.route('/')
def home():
    """redirects to /register"""

    return redirect('/register')


@app.route('/users/<username>')
def show_secret(username):
    """shows secret page once logged in"""

    if "current_user" not in session:
        flash("Please login first!", 'error')
        return redirect('/login')
    
    feedback = Feedback.query.filter_by(username=username)
    user = User.query.filter_by(username=username).first()

    return render_template('user-info.html', feedback=feedback, user=user)


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """form to register user"""

    if "current_user" in session:
        return redirect(f'/users/{session["current_user"]}')

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('This username is already taken. Please choose another.')
            return render_template('register.html', form=form)
        session['current_user'] = new_user.username
        flash("Welcome! Thank you for creating an account!", 'success')
        return redirect(f'/users/{new_user.username}')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """shows form to login user"""

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f'Welcome Back, {user.username}', 'primary')
            session['current_user'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid username/password']

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_user():
    """logs out current user"""

    session.pop('current_user')
    return redirect('/login')


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """deletes a user"""

    if 'current_user' not in session:
        flash("Please login first.", 'error')
        return redirect('/login')

    user = User.query.get_or_404(username)
    feedback = Feedback.query.filter_by(username=username)
    if username == session['current_user']:
        for post in feedback:
            db.session.delete(post)
            db.session.commit()
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash('You have successfully deleted your account', 'info')
        return redirect('/')

    flash("You don't have permission to perform this action", 'error')
    return redirect('/login')
    

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def get_feedback(username):
    """displays form to add feedback, and sends POST request to add new feedback"""

    if "current_user" not in session:
        flash("Please login first!", 'error')
        return redirect('/login')

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(title=title, content=content, username=session["current_user"])
        db.session.add(new_feedback)
        db.session.commit()
        flash("Feedback posted!", 'success')
        return redirect(f'/users/{username}')
    
    return render_template('feedback-form.html', form=form)


@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    """shows form to update feedback and updates it"""

    if "current_user" not in session:
        flash("Please login first!", 'error')
        return redirect('/login')

    feedback = Feedback.query.get_or_404(feedback_id)
    form = FeedbackForm(obj=feedback)

    if feedback.username != session['current_user']:
        flash("You don't have permission to perform this action", 'error')
        return redirect('/')
    else:
        if form.validate_on_submit():
            feedback.title = form.title.data
            feedback.content = form.content.data
            db.session.commit()
            flash('Feedback successfully edited!', 'success')
            return redirect('/')
    
    return render_template('edit-feedback-form.html', form=form, feedback=feedback)


@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    """deletes a user's feedback"""

    if 'current_user' not in session:
        flash("Please login first.", 'error')
        return redirect('/login')

    feedback = Feedback.query.get_or_404(feedback_id)
    if feedback.username == session['current_user']:
        db.session.delete(feedback)
        db.session.commit()
        flash('Feedback deleted!', 'info')
        return redirect(f'/users/{session["current_user"]}')
        
    flash("You don't have permission to perform this action", 'error')
    return redirect('/login')


    





