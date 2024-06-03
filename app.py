from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL

app = Flask(__name__, template_folder='templates')
CORS(app)

#Connectie met database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'
app.config['MYSQL_DB'] = 'logindatabase' #aanpassen naar eigen database
mysql = MySQL(app)


@app.route("/login", methods=["POST"])
def login():
    email = request.json["email"]
    password = request.json["password"]
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT COUNT(*) FROM User2 WHERE email = %s AND BINARY password = %s''', (email, password,))
    Exists = cursor.fetchone()[0]
    if(Exists == 0):
        print("failed")
        return "", 400
    else:
        print("success")
        return  "", 200



def emailCheck(email):
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT COUNT(*) FROM User2 WHERE email = %s''', (email,)) 
    EmailUsed = cursor.fetchone()[0]
    cursor.close()
    return EmailUsed

@app.route("/register", methods=["POST"])
def register():
    print("register")  #test
    email = request.form["email"]
    emailUsed = emailCheck(email)
    print(email, emailUsed)
    if(emailUsed == 0):
        password = request.form["password"]
        firstName = request.form["firstName"]
        lastName = request.form["lastName"]
        accountType = request.form["accountType"]
        role = None
        if accountType == "Doctor":
            role = 1
        elif accountType == "Patient":
            role = 2
        elif accountType == "Admin":
            role = 3
        elif accountType == "Researcher":
            role = 4
        employeeNumber = request.form["employeeNumber"]
        if(employeeNumber == ""):
            employeeNumber = None
        specialization = request.form["specialization"]
        if(specialization == ""):
            specialization = None
        patientNumber = request.form["patientNumber"]
        if(patientNumber == ""):
            patientNumber = None
        gender = request.form["gender"]
        if(gender == ""):
            gender = None
        birthDate = request.form["birthDate"]
        if(birthDate == ""):
            birthDate = None
        phoneNumber = request.form["phoneNumber"]
        if(phoneNumber == ""):
            phoneNumber = None
        photo = request.files["photo"]
        photo_data = photo.read()

        cursor = mysql.connection.cursor()
        
        try:
            cursor.execute('''INSERT INTO User2 (Role, Email, Password, FirstName, LastName, EmployeeNumber, Specialization, PatientNumber, Gender, BirthDate, PhoneNumber, Photo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s)''', (role, email, password, firstName, lastName, employeeNumber, specialization, patientNumber, gender, birthDate, phoneNumber, photo_data))
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
    print(email, emailUsed)
    if(emailUsed == 1):
        password = request.json["password"]
        cursor = mysql.connection.cursor()
        cursor.execute('''UPDATE User2 SET Password = %s WHERE Email = %s''', (password, email))
        mysql.connection.commit()
        cursor.close()
        return "", 200
    else:
        return "", 500 




if __name__ == "__main__":
    app.run(debug=True)