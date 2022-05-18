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

class AdmissionInfo(object):
    def __init__(self):
        self.stage = ""
        self.year = ""
        self.state = ""
        self.total = 0

class AdmissionsInfo(object):
    def __init__(self):
        self.stages = list()
        self.years = list()
        self.states = list()
        self.admissions = list()

@app.route('/school/<code>')
def school_by_code(code):
    conn = get_db_connection()
    req = 'SELECT * FROM COLEGIOS WHERE Codigo_Centro=' + str(code)
    school_info = conn.execute(req).fetchall()
    admissions = conn.execute('SELECT * FROM PROCESO_ADMISION WHERE Codigo_Centro=' + str(code) + ' ORDER BY Etapa,Periodo,Estado').fetchall()
    conn.close()

    return render_template('school.html', info=school_info[0], admissions=admissions)
