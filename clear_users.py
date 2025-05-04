import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
c = conn.cursor()
c.execute("DELETE FROM users;")  # This deletes all users
conn.commit()
conn.close()

print("All users deleted.")