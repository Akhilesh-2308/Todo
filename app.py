from flask import Flask, render_template, request, redirect
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = 'Todo'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db = SQLAlchemy(app)

class Todo(db.Model):
    Sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self) -> str:
        return f"{self.Sno} - {self.title}"


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo(title=title, desc=desc, user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()
    allTodo= Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', allTodo=allTodo)

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')


@app.route('/update/<int:Sno>' , methods=['GET', 'POST'])
@login_required
def update(Sno):
    todo= Todo.query.filter_by(Sno=Sno, user_id=current_user.id).first()
    if not todo:
        return "Todo not found or you don't have permission to edit this todo."
    if request.method == 'POST':
        todo.title = request.form['title']
        todo.desc = request.form['desc']
        db.session.commit()
        return redirect('/')
    return render_template('update.html', todo=todo)


@app.route('/delete/<int:Sno>')
@login_required
def delete(Sno):
    todo= Todo.query.filter_by(Sno=Sno, user_id=current_user.id).first()
    if not todo:
        return "Todo not found or you don't have permission to delete this todo."
    db.session.delete(todo)
    db.session.commit()  
    return redirect('/')  
    
@app.route('/about')
def about():
    return render_template('about.html')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            error = 'User already exists!'
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit() 
            return redirect('/login')
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template('login.html',error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
