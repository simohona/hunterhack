# HunterConnect 🎪

**Discover. Connect. Engage.**  
HunterConnect is a campus event management platform for Hunter College students to browse and share upcoming events.

## Key Features
- 🔍 Browse events with filters (club, location, date)
- 🔐 Secure user authentication (login/register)
- ➕ Add/edit/delete your events
- 🖼️ Event flyer/image support
- 📱 Fully responsive design

  ## Tech Stack
| Component       | Technology           |
|-----------------|----------------------|
| **Frontend**    | HTML5, CSS           |
| **Backend**     | Python (Flask)       |
| **Database**    | PostgreSQL           |
| **Auth**        | Flask-Login          |
| **Templates**   | Jinja2               |
| **Deployment**  | Render/Fly.io        |

## Quick Start
1. Clone repo:
   ```bash
   git clone https://github.com/your-username/HunterConnect.git

Install dependencies:
pip install -r requirements.txt

Configure environment:
echo "FLASK_APP=app.py" > .env
echo "SECRET_KEY=your_key" >> .env

Initialize DB:
flask init-db

Run:
flask run

Visit http://127.0.0.1:5000
