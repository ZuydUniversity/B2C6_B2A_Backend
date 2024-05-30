from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS

app = Flask(__name__)  # Initialiseren
CORS(app)

app.config['MYSQL_HOST'] = '20.16.87.228'
app.config['MYSQL_USER'] = 'Userb2a'
app.config['MYSQL_PASSWORD'] = 'DitIsEchtHeelLeukBlok3006'
app.config['MYSQL_DB'] = 'your_database_name'

mysql = MySQL(app)

@app.route('/')
def welcome():
    return "WELKOM"

@app.route('/doctors', methods=['GET'])  # Dit werkt als endpoint van API.
def get_doctors():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM doctor")
    doctors = cur.fetchall()
    cur.close()
    return jsonify(doctors)

@app.route('/doctors/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM doctor WHERE id=%s", (doctor_id,))
    doctor = cur.fetchone()
    cur.close()
    return jsonify(doctor)

if __name__ == '__main__':  # Uitvoeren
    app.run(debug=True)
