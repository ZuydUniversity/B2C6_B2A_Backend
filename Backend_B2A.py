from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL

app = Flask(__name__, template_folder='templates')
CORS(app)

#Connectie met database
app.config['MYSQL_HOST'] = '20.16.87.228'
app.config['MYSQL_USER'] = 'Userb2a'
app.config['MYSQL_PASSWORD'] = 'DitIsEchtHeelLeukBlok3006'
app.config['MYSQL_DB'] = 'your_database_name'
mysql = MySQL(app)


@app.route("/login", methods=["POST"])
def login():
    email = request.json["email"]
    password = request.json["password"]
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT COUNT(*) FROM User WHERE Email = %s AND BINARY Password = %s''', (email, password,))
    Exists = cursor.fetchone()[0]
    if(Exists == 0):
        return "", 400
    else:
        return  "", 200



def emailCheck(email):
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT COUNT(*) FROM User WHERE Email = %s''', (email,)) 
    EmailUsed = cursor.fetchone()[0]
    cursor.close()
    return EmailUsed

@app.route("/register", methods=["POST"])
def register():
    form_data = request.form.copy()
    for x in form_data:
        if form_data[x] == "":
            form_data[x] = None

    email = form_data["email"]
    emailUsed = emailCheck(email)
    if(emailUsed == 0):
        password = form_data["password"]
        firstName = form_data["firstName"]
        lastName = form_data["lastName"]
        accountType = form_data["accountType"]
        role = None
        if accountType == "Doctor":
            role = 1
        elif accountType == "Patient":
            role = 2
        elif accountType == "Admin":
            role = 3
        elif accountType == "Researcher":
            role = 4
        employeeNumber = form_data["employeeNumber"]
        specialization = form_data["specialization"]
        patientNumber = form_data["patientNumber"]
        gender = form_data["gender"]
        birthDate = form_data["birthDate"]
        phoneNumber = form_data["phoneNumber"]
        photo = request.files["photo"]
        contact_name = form_data["contact_name"]
        contact_email = form_data["contact_email"]
        contact_phone = form_data["contact_phone"]
        photo_data = photo.read()
        cursor = mysql.connection.cursor()
        
        try:
            cursor.execute('''INSERT INTO User (Role, Email, Password, Name, Lastname, Employee_number, Specialization, Patient_number, Gender, Birthdate, Phone_number, Photo, Contactperson_email, Contactperson_name, Contactperson_phone_number) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', (role, email, password, firstName, lastName, employeeNumber, specialization, patientNumber, gender, birthDate, phoneNumber, photo_data, contact_email, contact_name, contact_phone,))
            mysql.connection.commit()
            cursor.close()
            return "", 200
        except Exception as e:
            return "", 500  

        
    else:
        return "", 400

@app.route("/forgotpassword", methods=["POST"])
def forgot():  
    email = request.json["email"]
    emailUsed = emailCheck(email)
    if(emailUsed == 1):
        password = request.json["password"]
        cursor = mysql.connection.cursor()
        cursor.execute('''UPDATE User SET Password = %s WHERE Email = %s''', (password, email))
        mysql.connection.commit()
        cursor.close()
        return "", 200
    else:
        return "", 500 




if __name__ == "__main__":
    app.run(debug=True)
