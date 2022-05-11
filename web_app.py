import sqlite3
from flask import Flask, render_template

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('coles_cam.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    conn = get_db_connection()
    schools = conn.execute('SELECT * FROM COLEGIOS').fetchall()
    conn.close()
    return render_template('index.html', schools=schools)

@app.route('/school/<code>')
def school_by_code(code):
    return render_template('school.html')
