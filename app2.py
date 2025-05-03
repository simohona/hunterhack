from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import psycopg2  # For PostgreSQL
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'static/flyers'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database configuration (adjust these values)
DB_HOST = os.environ.get('DB_HOST', 'your_db_host')  # Use environment variables for security
DB_NAME = os.environ.get('DB_NAME', 'your_db_name')
DB_USER = os.environ.get('DB_USER', 'your_db_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_db_password')

# ----- Login Manager -----
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ----- User Model -----
class User(UserMixin):
    def __init__(self, id_, username):
        self.id = id_
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))  # Use %s for PostgreSQL
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1])
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        print("Error connecting to database:", e)
        return None

# Initialize the database
def init_db():
    conn = get_db_connection()
    if conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,  -- Use SERIAL for auto-increment in PostgreSQL
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                title TEXT,
                club TEXT,
                location TEXT,
                description TEXT,
                date TEXT,
                user_id INTEGER,
                flyer TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        conn.close()
    else:
        print("Database connection failed, cannot initialize database.")

init_db()


@app.route('/')
def index():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT title, club, location, description, date, flyer FROM events ORDER BY date")
    events = c.fetchall()
    conn.close()
    return render_template('index.html', events=events, user=current_user if current_user.is_authenticated else None)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        title = request.form['title']
        club = request.form['club']
        location = request.form['location']
        description = request.form['description']
        date = request.form['date']
        flyer = request.files['flyer']
        flyer_filename = ''
        if flyer and allowed_file(flyer.filename):
            filename = secure_filename(flyer.filename)
            flyer_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            flyer.save(flyer_path)
            flyer_filename = filename

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO events (title, club, location, description, date, user_id, flyer)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, club, location, description, date, current_user.id, flyer_filename))
        conn.commit()
        conn.close()

        return redirect('/')
    return render_template('add_event.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
        except psycopg2.IntegrityError:
            return "Username already exists"
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = c.fetchone()
        conn.close()
        if user and user[2] == password:
            login_user(User(user[0], user[1]))
            return redirect('/')
        return "Invalid login"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)