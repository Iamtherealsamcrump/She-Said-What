from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin():
    if not User.query.filter_by(username='admin').first():
        pwd = generate_password_hash('changeme')
        db.session.add(User(username='admin', password_hash=pwd))
        db.session.commit()
        print("Admin user 'admin' with password 'changeme' created!")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    questions = Question.query.order_by(Question.id.desc()).all()
    return render_template('question_list.html', questions=questions)

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        db.session.add(Post(title=request.form['title'], body=request.form['body']))
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('new_post.html')

@app.route('/ask', methods=['POST'])
def ask():
    db.session.add(Question(body=request.form['question']))
    db.session.commit()
    flash('Question submitted!')
    return redirect(url_for('index'))

@app.route('/answer/<int:q_id>', methods=['GET', 'POST'])
@login_required
def answer(q_id):
    q = Question.query.get_or_404(q_id)
    if request.method == 'POST':
        q.answer = request.form['answer']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('answer.html', q=q)

@app.route('/')
def index():
    # Check if the Post table exists
    try:
        posts = Post.query.all()
        questions = Question.query.all()
    except:
        return '⚠️ Database not initialized. Visit /init-db first.'
    return render_template('index.html', posts=posts, questions=questions)

@app.route('/init-db')
def init_db():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        hashed = generate_password_hash('changeme')
        db.session.add(User(username='admin', password_hash=hashed))
        db.session.commit()
    return 'Database initialized!'

@app.route('/reset-admin')
def reset_admin():
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password_hash=generate_password_hash('changeme'))
        db.session.add(admin)
    else:
        admin.password_hash = generate_password_hash('changeme')
    db.session.commit()
    return '✅ Admin password reset to changeme'
    
if __name__ == '__main__':
    if not os.path.exists('blog.db'):
        db.create_all()
        create_admin()
    app.run(debug=True)
