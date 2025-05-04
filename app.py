from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import psycopg2
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL =", DATABASE_URL)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'static/flyers'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# Initialize Login Manager
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
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1])
    return None

# ----- Utility Functions -----
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----- Initialize Database -----
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
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
            user_id INTEGER REFERENCES users(id),
            flyer TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ----- Routes -----
@app.route('/')
@app.route('/', methods=['GET'])
def index():
    filter_club = request.args.get('club')
    filter_location = request.args.get('location')
    filter_date = request.args.get('date')

    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()

    query = "SELECT title, club, location, description, date, flyer, user_id, id FROM events WHERE 1=1"
    params = []

    if filter_club:
        query += " AND club ILIKE %s"
        params.append(f"%{filter_club}%")  # case-insensitive partial match

    if filter_location:
        query += " AND location ILIKE %s"
        params.append(f"%{filter_location}%")

    if filter_date:
        query += " AND date = %s"
        params.append(filter_date)

    query += " ORDER BY date"
    c.execute(query, tuple(params))
    events = c.fetchall()
    conn.close()

    return render_template('index.html',
                           events=events,
                           filter_club=filter_club,
                           filter_location=filter_location,
                           filter_date=filter_date)


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

        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("INSERT INTO events (title, club, location, description, date, user_id, flyer) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                  (title, club, location, description, date, current_user.id, flyer_filename))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add_event.html')

@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE id = %s AND user_id = %s", (event_id, current_user.id))
    event = c.fetchone()

    if not event:
        conn.close()
        return "Event not found or not authorized", 403

    if request.method == 'POST':
        title = request.form['title']
        club = request.form['club']
        location = request.form['location']
        description = request.form['description']
        date = request.form['date']

        flyer = request.files.get('flyer')
        flyer_filename = event[7]  # existing flyer

        if flyer and allowed_file(flyer.filename):
            filename = secure_filename(flyer.filename)
            flyer.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flyer_filename = filename

        c.execute("""UPDATE events 
                     SET title=%s, club=%s, location=%s, description=%s, date=%s, flyer=%s 
                     WHERE id=%s AND user_id=%s""",
                  (title, club, location, description, date, flyer_filename, event_id, current_user.id))
        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()
    return render_template('edit_event.html', event=event)

@app.route('/delete/<int:event_id>')
@login_required
def delete_event(event_id):
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE id = %s AND user_id = %s", (event_id, current_user.id))
    conn.commit()
    conn.close()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        raw_password = request.form['password']
        hashed_password = generate_password_hash(raw_password)

        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return "Username already exists"
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        raw_password = request.form['password']

        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], raw_password):
            login_user(User(user[0], user[1]))
            return redirect('/')
        return "Invalid login"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')



# @app.route('/', methods=['GET', 'POST'])
# def home():
#     filter_club = request.args.get('club')  # Get the filter by club
#     filter_location = request.args.get('location')  # Get the filter by location
#     filter_date = request.args.get('date')  # Get the filter by date
    
#     # Build the base query
#     query = 'SELECT * FROM events WHERE 1=1'
#     params = []

#     # Add filter conditions if specified
#     if filter_club:
#         query += ' AND club = %s'
#         params.append(filter_club)

#     if filter_location:
#         query += ' AND location = %s'
#         params.append(filter_location)

#     if filter_date:
#         query += ' AND date = %s'
#         params.append(filter_date)

#     # Execute the query
#     cursor = db.cursor()
#     cursor.execute(query, tuple(params))
#     events = cursor.fetchall()

#     return render_template('home.html', events=events, filter_club=filter_club, filter_location=filter_location, filter_date=filter_date)


# ----- Run App -----
if __name__ == '__main__':
    app.run(debug=True)