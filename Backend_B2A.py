from flask import Flask, jsonify, request, send_file
from flask_mysqldb import MySQL
from flask_cors import CORS
from fpdf import FPDF
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
import base64
from io import BytesIO
import logging
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
import os
from imgurpython import ImgurClient
import tempfile
import json  # Import the json module
from reportlab.pdfgen import canvas

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
CORS(app, supports_credentials=True)

imgurClient = ImgurClient(os.getenv('imgur_client_id'), os.getenv('imgur_client_secret'))




# Determine the environment based on an environment variable; default to 'development'
# environment = os.getenv('FLASK_ENV', 'dev')

# Use the loaded configuration for the specified environment to set up your app
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')

mysql = MySQL(app)

app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
mail = Mail(app)
URLserializer = URLSafeTimedSerializer('sdge%t564@57214@#457trh$rt5y')




logging.basicConfig(level=logging.DEBUG)

initialization_flag = False

@app.before_request
def before_request_func():
    global initialization_flag
    if not initialization_flag:
        try:
            cur = mysql.connection.cursor()
            cur.execute('SELECT 1')
            cur.close()
            app.logger.debug('MySQL connection is established and working.')
            initialization_flag = True
        except Exception as e:
            app.logger.error(f'Error connecting to MySQL: {e}')
            return jsonify({"Error connecting to MySQL": str(e)}), 500

def serialize_data(data):
    if isinstance(data, bytes):
        # Convert bytes to base64-encoded string
        return base64.b64encode(data).decode('utf-8')
    elif isinstance(data, dict):
        # Recursively process dictionary values
        return {k: serialize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Recursively process list elements
        return [serialize_data(item) for item in data]
    else:
        # Return data as is if it's not bytes
        return data

@app.route("/login", methods=["POST"])
def login():
    try:
        email = request.json["email"]
        password = request.json["password"]
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT Role, Id FROM User WHERE Email = %s AND BINARY Password = %s''', (email, password,))
        result = cursor.fetchone()
        if(result == None):
            return "", 400
        else:
            role = result[0]
            id = result[1]
            return jsonify({"role": role, "user_id": id}), 200
    except Exception as e:
        app.logger.error(f'Error during login: {e}')
        return "", 500
        



def emailCheck(email):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT COUNT(*) FROM User WHERE Email = %s''', (email,)) 
        EmailUsed = cursor.fetchone()[0]
        cursor.close()
        return EmailUsed
    except Exception as e:
        return -1

@app.route("/register", methods=["POST"])
def register():
    form_data = request.form.copy()
    for x in form_data:
        if form_data[x] == "":
            form_data[x] = None

    email = form_data["email"]
    emailUsed = int(emailCheck(email))

    if(emailUsed == -1):
        return "", 500
    elif(emailUsed == 0):
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
            
        specialization = form_data["specialization"]
        gender = form_data["gender"]
        birthDate = form_data["birthDate"]
        phoneNumber = form_data["phoneNumber"]
        contact_name = form_data["contact_name"]
        contact_lastname = form_data["contact_lastname"]
        contact_email = form_data["contact_email"]
        contact_phone = form_data["contact_phone"]
        
        photo_url = None
        if 'photo' in request.files:
            photo = request.files["photo"]
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            photo.save(temp_file.name)
            try:
                uploaded = imgurClient.upload_from_path(temp_file.name, anon=True)
                photo_url = uploaded['link']
            finally:
                temp_file.close()
                os.unlink(temp_file.name)

        cursor = mysql.connection.cursor()
        try:
            cursor.execute('''INSERT INTO User (Role, Email, Password, Name, Lastname, Specialization, Gender, Birthdate, Phone_number, Photo, Contactperson_email, Contactperson_name, Contactperson_lastname, Contactperson_phone_number) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', (role, email, password, firstName, lastName, specialization, gender, birthDate, phoneNumber, photo_url, contact_email, contact_name, contact_lastname, contact_phone,))
            mysql.connection.commit()
            cursor.close()
            return "", 200
        except Exception as e:
            app.logger.error(f'Error during registration: {e}')
            return "", 500       
    else:
        return "", 400

 

## DOES NOT WORK ON SCHOOL INTERNET!
@app.route("/send_password_reset_email", methods=["POST"])
def send_password_reset_email():
    email = request.json["email"]
    exists = emailCheck(email)
    if exists == 1:
        token = URLserializer.dumps(email, salt='ghi3yt7yhg874g89(*uh)')
        ## have to replace the url with the actual url when using on azure
        reset_url = f"http://localhost:5173/reset-password/{token}"
        html = f'<p>Uw link om een nieuwe wachtwoord te maken is: <a href="{reset_url}">Link</a></p>'
        msg = Message('Nieuwe wachtwoord link', sender='Zuydb2a@proton.me', recipients=[email])
        msg.body = 'Druk op de link om een nieuwe wachtwoord te maken.'
        msg.html = html
        mail.send(msg)
        return "", 200 
    elif(exists == 0):
        return "", 400
    else:
        return "", 500


@app.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    try:
        email = URLserializer.loads(token, salt="ghi3yt7yhg874g89(*uh)", max_age=600)
    except SignatureExpired:
        return "", 400

    new_password = request.json["password"]

    try:
        cursor = mysql.connection.cursor()
        cursor.execute('''UPDATE User SET Password = %s WHERE Email = %s''', (new_password, email))
        mysql.connection.commit()
        cursor.close()
        return "", 200
    except Exception as e:
        return "", 500  






#   --------------------------
#   |   User API Functions   |   
#   -------------------------- 

# gets all doctors
@app.route('/get_doctors', methods=['GET'])
def get_doctors():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM User WHERE Role = '1'")
        doctors = cur.fetchall()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()
        
        if not doctors:
            return jsonify({"error": "No doctors found"}), 404

        # Convert the result to a list of dictionaries
        doctors_list = [dict(zip(column_names, row)) for row in doctors]

        # Serialize data to handle binary fields
        serialized_doctors = serialize_data(doctors_list)

        return jsonify(serialized_doctors)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# gets a doctor by ID
@app.route('/get_doctor/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '1'"
        cur.execute(query, (doctor_id,))
        doctor = cur.fetchone()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()
        
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404

        # Convert the result to a dictionary
        doctor_dict = dict(zip(column_names, doctor))

        # Serialize data to handle binary fields
        serialized_doctor = serialize_data(doctor_dict)

        return jsonify(serialized_doctor)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Update doctor information
@app.route('/update_doctor/<int:doctor_id>', methods=['PUT'])
def update_doctor(doctor_id):
    try:
        # Get the updated data from the request body
        updated_data = request.get_json()

        # Check if the patient exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '1'"
        cur.execute(query, (doctor_id,))
        doctor = cur.fetchone()
        cur.close()

        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404

        # Update the doctor's information
        cur = mysql.connection.cursor()
        query = "UPDATE User SET "
        values = []
        for key, value in updated_data.items():
            query += f"{key} = %s, "
            values.append(value)
        query = query[:-2]  # Remove the trailing comma and space
        query += " WHERE Id = %s"
        values.append(doctor_id)
        cur.execute(query, tuple(values))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Doctor information updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# delete a doctor
@app.route('/delete_doctor/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    try:
        # Delete the doctor from the patient_doctor table first
        cur = mysql.connection.cursor()
        query = "DELETE FROM `Patient-Doctor` WHERE DoctorId = %s"
        cur.execute(query, (doctor_id,))
        mysql.connection.commit()
        cur.close()

        # Then, delete the doctor from the User table
        cur = mysql.connection.cursor()
        query = "DELETE FROM User WHERE Id = %s"
        cur.execute(query, (doctor_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Doctor and associated links deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# gets all patients
@app.route('/get_patients', methods=['GET'])
def get_patients():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM User WHERE Role = '2'")
        patients = cur.fetchall()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()
        
        if not patients:
            return jsonify({"error": "No patients found"}), 404

        # Convert the result to a list of dictionaries
        patients_list = [dict(zip(column_names, row)) for row in patients]

        # Serialize data to handle binary fields
        serialized_patients = serialize_data(patients_list)

        return jsonify(serialized_patients)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# gets a patient by ID
@app.route('/get_patient/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()
        
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Convert the result to a dictionary
        patient_dict = dict(zip(column_names, patient))

        # Serialize data to handle binary fields
        serialized_patient = serialize_data(patient_dict)

        return jsonify(serialized_patient)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Update patient information
@app.route('/update_patient/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    print("Starting update_patient function")
    try:
        # Get the updated data from the request body
        updated_data = request.get_json()
        print("Received updated data:", updated_data)

        # Convert Birthdate from 'Wed Jul 03 2019' to 'YYYY-MM-DD'
        if 'Birthdate' in updated_data and updated_data['Birthdate']:
            try:
                print(f"Original Birthdate: {updated_data['Birthdate']}")
                birthdate_str = updated_data['Birthdate']
                # Parse the incoming date string without expecting time or GMT
                birthdate_obj = datetime.strptime(birthdate_str, '%a %b %d %Y')
                # Format it to the database's expected format 'YYYY-MM-DD'
                updated_data['Birthdate'] = birthdate_obj.strftime('%Y-%m-%d')
                print(f"Formatted Birthdate for DB: {updated_data['Birthdate']}")
            except ValueError as e:
                print(f"Error parsing Birthdate: {e}")
                # Handle the error appropriately, maybe set Birthdate to None or use a default value

        # Check if the patient exists
        print("Checking if patient exists in the database")
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()

        if not patient:
            print("Patient not found")
            return jsonify({"error": "Patient not found"}), 404

        # Update the patient's information
        print("Updating patient information in the database")
        cur = mysql.connection.cursor()
        query = "UPDATE User SET "
        values = []
        for key, value in updated_data.items():
            if value:  # Skip fields with empty values
                query += f"{key} = %s, "
                values.append(value)
        if not values:  # If no values to update, return a message
            print("No information updated due to empty values")
            return jsonify({"message": "No information updated due to empty values"})

        query = query[:-2]  # Remove the trailing comma and space
        query += " WHERE Id = %s"
        values.append(patient_id)
        cur.execute(query, tuple(values))
        mysql.connection.commit()
        cur.close()

        print("Patient information updated successfully")
        return jsonify({"message": "Patient information updated successfully"})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500
    
# delete a patient
@app.route('/delete_patient/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        # Delete the patient from the patient_doctor table first
        cur = mysql.connection.cursor()
        query = "DELETE FROM `Patient-Doctor` WHERE PatientId = %s"
        cur.execute(query, (patient_id,))
        mysql.connection.commit()
        cur.close()

        # Then, delete the patient from the User table
        cur = mysql.connection.cursor()
        query = "DELETE FROM User WHERE Id = %s"
        cur.execute(query, (patient_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Patient and associated links deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# gets a user by ID
@app.route('/get_user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s"
        cur.execute(query, (user_id,))
        user = cur.fetchone()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()
        
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Convert the result to a dictionary
        user_dict = dict(zip(column_names, user))

        # Serialize data to handle binary fields
        serialized_user = serialize_data(user_dict)

        return jsonify(serialized_user)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# update user by ID
@app.route('/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    try:
        data = request.get_json()
        Name = data.get('Name')
        Lastname = data.get('Lastname')
        Gender = data.get('Gender')
        Email = data.get('Email')
        Phone_number = data.get('Phone_number')
        AccessibilityMode = data.get('AccessibilityMode')
        EmailNotifications = data.get('EmailNotifications')
        
        # Check if all required fields are provided
        if not all([Name, Lastname, Gender, Email, Phone_number, AccessibilityMode is not None, EmailNotifications is not None]):
            return jsonify({"error": "Missing required fields"}), 400
        
        cur = mysql.connection.cursor()
        query = """
            UPDATE User 
            SET Name = %s, 
                Lastname = %s, 
                Gender = %s, 
                Email = %s, 
                Phone_number = %s, 
                AccessibilityMode = %s, 
                EmailNotifications = %s 
            WHERE Id = %s
        """
        cur.execute(query, (Name, Lastname, Gender, Email, Phone_number, AccessibilityMode, EmailNotifications, user_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({"success": "User updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#   -----------------------------------------
#   |   Patient Information API Functions   |   
#   -----------------------------------------

# Get a patient their medication
@app.route('/patients/<int:patient_id>/medication', methods=['GET'])
def get_patient_medication(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Medication WHERE PatientId = %s"
        cur.execute(query, (patient_id,))
        medications = cur.fetchall()

        if not medications:
            return jsonify({"error": "No medications found for this patient"}), 404

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        medications_list = [dict(zip(column_names, row)) for row in medications]

        return jsonify(medications_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Add medication for a patient
@app.route('/patients/<int:patient_id>/medication', methods=['POST'])
def add_medication(patient_id):
    try:
        medication_data = request.get_json()

        # Validate medication data
        required_fields = ['Name', 'Dose', 'Start_date', 'Frequency']
        for field in required_fields:
            if field not in medication_data:
                print(f"Missing required field: {field}")  # Log missing field
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Check if the patient exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()

        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Add medication for the patient
        cur = mysql.connection.cursor()
        query = "INSERT INTO Medication (PatientId, Name, Dose, Start_date, Frequency) VALUES (%s, %s, %s, %s, %s)"
        cur.execute(query, (patient_id, medication_data['Name'], medication_data['Dose'], medication_data['Start_date'], medication_data['Frequency']))
        
        # After executing the insert query
        new_medication_id = cur.lastrowid  # This is an example; the exact method depends on your database adapter
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Medication added successfully", "newId": new_medication_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Update medication for a patient
@app.route('/patients/<int:patient_id>/medication/<int:medication_id>', methods=['PUT'])
def update_medication(patient_id, medication_id):
    try:
        medication_data = request.get_json()

        # Validate medication data
        required_fields = ['Name', 'Dose', 'Start_date', 'Frequency']
        for field in required_fields:
            if field not in medication_data:
                print(f"Missing required field: {field}")  # Log missing field
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Parse and format Start_date
        try:
            received_date_str = medication_data['Start_date']
            received_date = datetime.strptime(received_date_str, '%a, %d %b %Y %H:%M:%S GMT')
            formatted_date = received_date.strftime('%Y-%m-%d')
            medication_data['Start_date'] = formatted_date
        except ValueError as e:
            response = jsonify({"error": "Incorrect date format for Start_date. Expected format: 'Thu, 16 May 2024 00:00:00 GMT'"}), 400
        else:
            # Proceed with the formatted_date for further processing
            response = jsonify({"formatted_date": formatted_date})

        # Check if the medication exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Medication WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (medication_id, patient_id))
        medication = cur.fetchone()
        cur.close()

        if not medication:
            return jsonify({"error": "Medication not found for this patient"}), 404

        # Update medication for the patient
        cur = mysql.connection.cursor()
        query = "UPDATE Medication SET Name = %s, Dose = %s, Start_date = %s, Frequency = %s WHERE Id = %s"
        cur.execute(query, (medication_data['Name'], medication_data['Dose'], medication_data['Start_date'], medication_data['Frequency'], medication_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Medication updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete medication for a patient
@app.route('/patients/<int:patient_id>/medication/<int:medication_id>', methods=['DELETE'])
def delete_medication(patient_id, medication_id):
    try:
        # Check if the medication exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Medication WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (medication_id, patient_id))
        medication = cur.fetchone()
        cur.close()

        if not medication:
            return jsonify({"error": "Medication not found for this patient"}), 404

        # Delete the medication
        cur = mysql.connection.cursor()
        query = "DELETE FROM Medication WHERE Id = %s"
        cur.execute(query, (medication_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Medication deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/patients/<int:patient_id>/diagnosis', methods=['POST'])
def add_diagnosis(patient_id):
    diagnosis_data = request.get_json()

    required_fields = ['DoctorId', 'Diagnosis', 'Description', 'Date']
    for field in required_fields:
        if field not in diagnosis_data:
            return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

    cur = mysql.connection.cursor()
    query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
    cur.execute(query, (patient_id,))
    patient = cur.fetchone()
    cur.close()

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    cur = mysql.connection.cursor()
    query = "INSERT INTO Diagnosis (PatientId, DoctorId, Diagnosis, Description, Date) VALUES (%s, %s, %s, %s, %s)"
    cur.execute(query, (patient_id, diagnosis_data['DoctorId'], diagnosis_data['Diagnosis'], diagnosis_data['Description'], diagnosis_data['Date']))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Diagnosis added successfully"})

@app.route('/patients/<int:patient_id>/diagnosis/<int:diagnosis_id>', methods=['PUT'])
def update_diagnosis(patient_id, diagnosis_id):
    try:
        print("Starting update_diagnosis function")
        diagnosis_data = request.get_json()
        print(f"Received diagnosis data: {diagnosis_data}")

        # Validate diagnosis data
        required_fields = ['DoctorId', 'Diagnosis', 'Description', 'Date']
        for field in required_fields:
            if field not in diagnosis_data:
                print(f"Missing required field: {field}")  # Log missing field
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Parse and format the date
        try:
            print(f"Attempting to parse date: {diagnosis_data['Date']}")
            # Attempt to parse the date with the first expected format
            received_date = datetime.strptime(diagnosis_data['Date'], '%a, %d %b %Y %H:%M:%S GMT')
            print(f"Date parsed successfully with first format: {received_date}")
        except ValueError:
            try:
                print("Attempting to parse date with second expected format")
                # If the first format fails, attempt with the second expected format
                received_date = datetime.strptime(diagnosis_data['Date'], '%Y-%m-%d')
                print(f"Date parsed successfully with second format: {received_date}")
            except ValueError:
                print("Failed to parse date with both expected formats")
                # If both formats fail, return an error message
                return jsonify({"error": "Incorrect date format. Expected formats: 'Fri, 29 Mar 2024 00:00:00 GMT' or '2024-03-20'"}), 400

        # If parsing is successful, format the datetime object to the desired format for the database
        formatted_date = received_date.strftime('%Y-%m-%d')
        diagnosis_data['Date'] = formatted_date  # Update the date in diagnosis_data with the formatted date
        print(f"Formatted date: {formatted_date}")

        # Check if the diagnosis exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Diagnosis WHERE Id = %s AND PatientId = %s"
        print(f"Executing query to check diagnosis existence: {query}")
        cur.execute(query, (diagnosis_id, patient_id))
        diagnosis = cur.fetchone()
        if not diagnosis:
            print("Diagnosis not found for this patient")
            return jsonify({"error": "Diagnosis not found for this patient"}), 404

        # Update diagnosis for the patient
        query = "UPDATE Diagnosis SET DoctorId = %s, Diagnosis = %s, Description = %s, Date = %s WHERE Id = %s"
        print(f"Updating diagnosis with data: {diagnosis_data}")  # Log updating diagnosis
        cur.execute(query, (diagnosis_data['DoctorId'], diagnosis_data['Diagnosis'], diagnosis_data['Description'], diagnosis_data['Date'], diagnosis_id))
        mysql.connection.commit()
        print("Diagnosis updated successfully")  # Log successful update
        cur.close()

        return jsonify({"message": "Diagnosis updated successfully"})

    except Exception as e:
        print(f"Error occurred: {e}")  # Log any exceptions
        return jsonify({"error": str(e)}), 500

      
# Delete a diagnosis for a patient
@app.route('/patients/<int:patient_id>/diagnosis/<int:diagnosis_id>', methods=['DELETE'])
def delete_diagnosis(patient_id, diagnosis_id):
    try:
        # Check if the diagnosis exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Diagnosis WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (diagnosis_id, patient_id))
        diagnosis = cur.fetchone()
        cur.close()

        if not diagnosis:
            return jsonify({"error": "Diagnosis not found for this patient"}), 404

        # Delete the diagnosis
        cur = mysql.connection.cursor()
        query = "DELETE FROM Diagnosis WHERE Id = %s"
        cur.execute(query, (diagnosis_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Diagnosis deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific diagnosis belonging to a patient
@app.route('/patients/<int:patient_id>/diagnosis/<int:diagnosis_id>', methods=['GET'])
def get_specific_diagnosis(patient_id, diagnosis_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Diagnosis WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (diagnosis_id, patient_id))
        diagnosis = cur.fetchone()

        if not diagnosis:
            return jsonify({"error": "Diagnosis not found"}), 404

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        diagnosis_dict = dict(zip(column_names, diagnosis))

        return jsonify(diagnosis_dict)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all diagnoses belonging to a patient
@app.route('/patients/<int:patient_id>/diagnosis', methods=['GET'])
def get_patient_diagnosis(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Diagnosis WHERE PatientId = %s"
        cur.execute(query, (patient_id,))
        diagnoses = cur.fetchall()

        if not diagnoses:
            return jsonify({"error": "No diagnoses found for this patient"}), 404

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        diagnoses_list = [dict(zip(column_names, row)) for row in diagnoses]

        return jsonify(diagnoses_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a patient their results
@app.route('/patients/<int:patient_id>/get_results', methods=['GET'])
def get_patient_results(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Result WHERE PatientId = %s"
        cur.execute(query, (patient_id,))
        results = cur.fetchall()

        if not results:
            return jsonify({"error": "No results found for this patient"}), 404

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        results_list = [dict(zip(column_names, row)) for row in results]

        return jsonify(results_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
# Get a specific result belonging to a patient
@app.route('/patients/<int:patient_id>/get_results/<int:result_id>', methods=['GET'])
def get_patient_result(patient_id, result_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Result WHERE PatientId = %s AND Id = %s"
        cur.execute(query, (patient_id, result_id))
        result = cur.fetchone()

        if not result:
            return jsonify({"message": "Result not found"})

        column_names = [desc[0] for desc in cur.description]
        result_dict = dict(zip(column_names, result))

        # Include resultId in the result dictionary
        result_dict["resultId"] = result_dict.pop("Id")

        cur.close()

        return jsonify(result_dict)
    except Exception as e:
        return jsonify({"message": "An error occurred"})



# Delete a result
@app.route('/delete_result/<int:result_id>', methods=['DELETE'])
def delete_result(result_id):
    try:
        # Check if the test result exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Result WHERE Id = %s"
        cur.execute(query, (result_id,))
        result = cur.fetchone()
        cur.close()
        if not result:
            return jsonify({"message": "Test result not found"})

        # Delete the result
        cur = mysql.connection.cursor()
        query = "DELETE FROM Result WHERE Id = %s"
        cur.execute(query, (result_id,))
        mysql.connection.commit()
        cur.close()

        # Delete any attached notes
        cur = mysql.connection.cursor()
        query = "DELETE FROM Note WHERE ResultId = %s"
        cur.execute(query, (result_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Result deleted successfully"})

    except Exception as e:
        return jsonify({"message": "An error occurred"})

# Add a result for a patient
@app.route('/patients/<int:patient_id>/add_result', methods=['POST'])
def add_patient_result(patient_id):
    try:
        result_data = request.get_json()

        # Validate result data
        required_fields = ['test_name', 'result_value', 'date']
        for field in required_fields:
            if field not in result_data:
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Check if the patient exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()

        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Add result for the patient
        cur = mysql.connection.cursor()
        query = "INSERT INTO Result (PatientId, TestName, ResultValue, Date) VALUES (%s, %s, %s, %s)"
        cur.execute(query, (patient_id, result_data['test_name'], result_data['result_value'], result_data['date']))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Result added successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a result for a patient
@app.route('/patients/<int:patient_id>/update_result/<int:result_id>', methods=['PUT'])
def update_patient_result(patient_id, result_id):
    try:
        result_data = request.get_json()

        # Validate result data
        required_fields = ['test_name', 'result_value', 'date']
        for field in required_fields:
            if field not in result_data:
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Check if the result exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Result WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (result_id, patient_id))
        result = cur.fetchone()
        cur.close()

        if not result:
            return jsonify({"error": "Result not found for this patient"}), 404

        # Update result for the patient
        cur = mysql.connection.cursor()
        query = "UPDATE Result SET TestName = %s, ResultValue = %s, Date = %s WHERE Id = %s"
        cur.execute(query, (result_data['test_name'], result_data['result_value'], result_data['date'], result_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Result updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add a note for a specific patient's result
@app.route('/patient/<int:patient_id>/result/<int:result_id>/add_note', methods=['POST'])
def add_note(patient_id, result_id):
    try:
        note_text = request.get_json().get('note')
        doctor_id = request.get_json().get('doctor_id')  # Assuming you get the doctor's ID from the request

        # Check if the patient exists and has the appropriate role
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()
        if not patient:
            return jsonify({"message": "Patient not found or invalid"})

        # Check if the test result exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Result WHERE Id = %s"
        cur.execute(query, (result_id,))
        result = cur.fetchone()
        cur.close()
        if result is None:
            return jsonify({"message": "Result not found"})
        elif result[2] != patient_id:
            return jsonify({"message": "Result doesn't belong to the patient"})

        # Add the note to the Note table
        cur = mysql.connection.cursor()
        query = "INSERT INTO Note (ResultId, DoctorId, Type, Date) VALUES (%s, %s, %s, NOW())"
        cur.execute(query, (result_id, doctor_id, note_text))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Note added successfully"})

    except mysql.connection.Error as e:
        return jsonify({"message": "MySQL error occurred: {}".format(e)})

    except Exception as e:
        return jsonify({"message": "An error occurred: {}".format(e)})

# Get the notes belonging to a result
@app.route('/results/<int:result_id>/notes', methods=['GET'])
def get_result_notes(result_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Note WHERE ResultId = %s"
        cur.execute(query, (result_id,))
        notes = cur.fetchall()

        if not notes:
            return jsonify([])

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        notes_list = [dict(zip(column_names, row)) for row in notes]

        return jsonify(notes_list)
    except Exception as e:
        return jsonify({"message": "An error occurred"})
    
# Delete a note for a specific patient's result
@app.route('/patient/<int:patient_id>/result/<int:result_id>/delete_note', methods=['DELETE'])
def delete_note(patient_id, result_id):
    try:
        # Check if the patient exists and has the role of patient
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()

        if not patient:
            return jsonify({"message": "Patient not found"})

        # Check if the test result exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Result WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (result_id, patient_id))
        result = cur.fetchone()
        cur.close()

        if not result:
            return jsonify({"message": "Result not found"})

        # Check if the note exists and is associated with the specified result
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Note WHERE ResultId = %s"
        cur.execute(query, (result_id,))
        note = cur.fetchone()
        cur.close()

        if not note:
            return jsonify({"message": "Note not found for this result"})

        # Delete the note for the test result
        cur = mysql.connection.cursor()
        query = "DELETE FROM Note WHERE ResultId = %s"
        cur.execute(query, (result_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Note deleted successfully"})

    except mysql.connection.Error as err:
        return jsonify({"message": "MySQL error: {}".format(err)})
    except Exception as e:
        return jsonify({"message": "An error occurred: {}".format(str(e))})

    
# Edit a note for a specific patient's result
@app.route('/patient/<int:patient_id>/result/<int:result_id>/edit_note', methods=['PUT'])
def edit_note(patient_id, result_id):
    try:
        # Get the updated note from the request body
        updated_note = request.get_json()['note']

        # Check if the patient exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()

        if not patient:
            return jsonify({"message": "Patient not found"})

        # Check if the test result exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Result WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (result_id, patient_id))
        result = cur.fetchone()
        cur.close()

        if not result:
            return jsonify({"message": "Result not found"})

        # Update the note for the test result
        cur = mysql.connection.cursor()
        query = "UPDATE Note SET Type = %s WHERE ResultId = %s"
        cur.execute(query, (updated_note, result_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Note updated successfully"})

    except Exception as e:
        return jsonify({"message": "An error occurred"})
    
# Create an excercise
@app.route('/patients/<int:patient_id>/excercise', methods=['POST'])
def add_patient_excercise():
    try:
        excercise_data = request.get_json()

        # Validate excercise data
        required_fields = ['name', 'description', 'cmas_id']
        for field in required_fields:
            if field not in excercise_data:
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Check if the CMAS exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM CMAS WHERE Id = %s"
        cur.execute(query, (excercise_data['cmas_id'],))
        cmas = cur.fetchone()
        cur.close()

        if not cmas:
            return jsonify({"error": "CMAS not found"}), 404

        # Add excercise for the patient
        cur = mysql.connection.cursor()
        query = "INSERT INTO Excercise (Name, Description, CMASId) VALUES (%s, %s, %s)"
        cur.execute(query, (excercise_data['name'], excercise_data['description'], excercise_data['cmas_id']))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Excercise added successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Get a patient's excercises
@app.route('/patients/<int:patient_id>/excercises', methods=['GET'])
def get_patient_excercises(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT E.* 
            FROM Excercise E
            INNER JOIN CMAS C ON E.CMASId = C.Id
            INNER JOIN Result R ON C.ResultId = R.Id
            WHERE R.PatientId = %s
        """
        cur.execute(query, (patient_id,))
        excercises = cur.fetchall()

        if not excercises:
            return jsonify([])

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        excercises_list = [dict(zip(column_names, row)) for row in excercises]

        return jsonify(excercises_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific excercise
@app.route('/patients/<int:patient_id>/excercises/<int:excercise_id>', methods=['GET'])
def get_patient_excercise(patient_id, excercise_id):
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT E.* 
            FROM Excercise E
            INNER JOIN CMAS C ON E.CMASId = C.Id
            INNER JOIN Result R ON C.ResultId = R.Id
            WHERE R.PatientId = %s AND E.Id = %s
        """
        cur.execute(query, (patient_id, excercise_id))
        excercise = cur.fetchone()

        if not excercise:
            return jsonify({"error": "Excercise not found"}), 404

        column_names = [desc[0] for desc in cur.description]
        excercise_dict = dict(zip(column_names, excercise))
        cur.close()

        return jsonify(excercise_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a patient's excercise
@app.route('/patients/<int:patient_id>/excercises/<int:excercise_id>', methods=['PUT'])
def update_patient_excercise(patient_id, excercise_id):
    try:
        excercise_data = request.get_json()

        # Validate excercise data
        required_fields = ['Left', 'Right', 'Type', 'Gewricht', 'CMASId']
        for field in required_fields:
            if field not in excercise_data:
                return jsonify({"error": f"{field} is a required field"}), 400

        # Check if the excercise exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = """
            SELECT E.* 
            FROM Excercise E
            INNER JOIN CMAS C ON E.CMASId = C.Id
            INNER JOIN Result R ON C.ResultId = R.Id
            WHERE R.PatientId = %s AND E.Id = %s
        """
        cur.execute(query, (patient_id, excercise_id))
        excercise = cur.fetchone()
        cur.close()

        if not excercise:
            return jsonify({"error": "Excercise not found for this patient"}), 404

        # Update excercise for the patient
        cur = mysql.connection.cursor()
        query = "UPDATE Excercise SET `Left` = %s, `Right` = %s, Type = %s, Gewricht = %s, CMASId = %s WHERE Id = %s"
        cur.execute(query, (excercise_data['Left'], excercise_data['Right'], excercise_data['Type'], excercise_data['Gewricht'], excercise_data['CMASId'], excercise_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Excercise updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Delete a patient's excercise
@app.route('/patients/<int:patient_id>/excercises/<int:excercise_id>', methods=['DELETE'])
def delete_patient_excercise(patient_id, excercise_id):
    try:
        # Check if the excercise exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = """
            SELECT E.* 
            FROM Excercise E
            INNER JOIN CMAS C ON E.CMASId = C.Id
            INNER JOIN Result R ON C.ResultId = R.Id
            WHERE R.PatientId = %s AND E.Id = %s
        """
        cur.execute(query, (patient_id, excercise_id))
        excercise = cur.fetchone()
        cur.close()

        if not excercise:
            return jsonify({"error": "Excercise not found for this patient"}), 404

        # Delete the excercise
        cur = mysql.connection.cursor()
        query = "DELETE FROM Excercise WHERE Id = %s"
        cur.execute(query, (excercise_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Excercise deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Get a patient's appointments
@app.route('/patients/<int:patient_id>/appointments', methods=['GET'])
def get_patient_appointments(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Appointment WHERE PatientId = %s"
        cur.execute(query, (patient_id,))
        appointments = cur.fetchall()

        if not appointments:
            return jsonify({"error": "No appointments found for this patient"}), 404

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        appointments_list = [dict(zip(column_names, row)) for row in appointments]

        return jsonify(appointments_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#GETs for patient- and doctordashboard
# Get all notes belonging to a patient
@app.route('/patients/<int:patient_id>/notes', methods=['GET'])
def get_patient_notes(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT Date, Type FROM Note WHERE Id = %s ORDER BY Date desc"
        cur.execute(query, (patient_id,))
        notes = cur.fetchall()

        if not notes:
            return jsonify({"message": "No notes found for this patient"})

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        notes_list = [dict(zip(column_names, row)) for row in notes]

        return jsonify(notes_list)
    except Exception as e:
        return jsonify({"message": "Error occurred while retrieving notes"})

# Get all notes belonging to a doctor
@app.route('/patients/<int:patient_id>/doctornotes', methods=['GET'])
def get_doctor_notes(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT Type, Date, Name, Lastname FROM your_database_name.Note INNER JOIN `User` ON Note.Id = `User`.Id WHERE DoctorId = %s ORDER BY Date desc"
        cur.execute(query, (patient_id,))
        notes = cur.fetchall()

        if not notes:
            return jsonify({"message": "No notes found for this doctor"})

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        doctornotes_list = [dict(zip(column_names, row)) for row in notes]

        return jsonify(doctornotes_list)
    except Exception as e:
        return jsonify({"message": "Error occurred while retrieving notes"})

# Get a patient's UPCOMING appointments (limit of 5, desc order)
@app.route('/patients/<int:patient_id>/upcomingappointments', methods=['GET'])
def get_patient_upcoming_appointments(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT Date, Description 
            FROM your_database_name.Appointment 
            INNER JOIN `Appointment-Users` ON Appointment.Id = `Appointment-Users`.AppointmentId 
            WHERE UserID = %s
            ORDER BY Date desc
            LIMIT 5
        """
        cur.execute(query, (patient_id,))
        appointments = cur.fetchall()

        if not appointments:
            return jsonify({"error": "No appointments found for this user"}), 404

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        appointments_list = [dict(zip(column_names, row)) for row in appointments]

        return jsonify(appointments_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get the name of the user, no matter their role
@app.route('/getuserfirstnamelastname/<int:patient_id>', methods=['GET'])
def get_user_firstnamelastname(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT Name, Lastname FROM User WHERE Id = %s"
        cur.execute(query, (patient_id,))
        notes = cur.fetchall()

        if not notes:
            return jsonify({"message": "No name found for this user"})

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        firstname_lastname = [dict(zip(column_names, row)) for row in notes]

        return jsonify(firstname_lastname)
    except Exception as e:
        return jsonify({"message": "Error occurred while retrieving name"})        
    

# DOWNLOAD FUNCTIONS (PDF) (GONNA NEED SOME SERIOUS TESTING and probably some adjustments to the layout of the pdf)

# Function to generate a PDF of a specific patient's data
@app.route('/download_patient_pdf/<int:patient_id>', methods=['GET'])
def download_patient_pdf(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()

        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Convert the result to a dictionary
        patient_dict = dict(zip(column_names, patient))

        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add a title
        pdf.cell(200, 10, txt="Patient Data", ln=True, align='C')

        # Add patient data
        for key, value in patient_dict.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align='L')

        # Save the PDF to a bytes buffer
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, as_attachment=True, download_name=f'patient_{patient_id}_data.pdf', mimetype='application/pdf')

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def fetch_from_db(query, params):
    cur = mysql.connection.cursor()
    cur.execute(query, params)
    result = cur.fetchall()
    column_names = [desc[0] for desc in cur.description] if cur.description else []
    cur.close()
    return [dict(zip(column_names, row)) for row in result]

# Route voor het genereren van PDF inclusief oefeningen en notities
@app.route('/download_result_pdf/<int:patient_id>/<int:result_id>', methods=['GET'])
def download_result_pdf(patient_id, result_id):
    try:
        # Patiëntgegevens ophalen
        patient_query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        patient = fetch_from_db(patient_query, (patient_id,))
        if not patient:
            return jsonify({"message": "Patiënt niet gevonden"}), 404

        # Resultaatgegevens ophalen
        result_query = "SELECT * FROM Result WHERE Id = %s AND PatientId = %s"
        result = fetch_from_db(result_query, (result_id, patient_id))
        if not result:
            return jsonify({"message": "Resultaat niet gevonden"}), 404

        # Oefeningen ophalen die aan het resultaat van de patiënt zijn gekoppeld
        exercises_query = """
            SELECT E.*
            FROM Excercise E
            INNER JOIN CMAS C ON E.CMASId = C.Id
            INNER JOIN Result R ON C.ResultId = R.Id
            WHERE R.PatientId = %s AND R.Id = %s
        """
        exercises = fetch_from_db(exercises_query, (patient_id, result_id))

        # Notities ophalen die aan het resultaat zijn gekoppeld
        notes_query = "SELECT * FROM Note WHERE ResultId = %s"
        notes = fetch_from_db(notes_query, (result_id,))

        # PDF aanmaken met ReportLab
        response = BytesIO()
        c = canvas.Canvas(response, pagesize=(600, 800))

        # PDF-inhoud schrijven
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "Patiëntgegevens")
        c.drawString(100, 710, f"Patiëntnaam: {patient[0]['Name']} {patient[0]['Lastname']}")
        
        # Datum toevoegen naast de patiëntnaam
        result_date = result[0]['Date'].strftime('%d-%m-%Y')
        c.drawString(450, 710, f"Datum: {result_date}")
        
        c.line(100, 700, 550, 700)

        # Tabel met oefeningen toevoegen
        if exercises:
            c.drawString(100, 690, "Oefeningen:")
            table_header = ["Type", "Gewricht", "Links", "Rechts"]
            table_data = [(exercise['Type'], exercise['Gewricht'], exercise['Left'], exercise['Right']) for exercise in exercises]

            table_start_x = 100
            table_start_y = 670
            row_height = 20
            col_widths = [150, 150, 100, 100] 

            for i, header in enumerate(table_header):
                c.drawString(table_start_x + sum(col_widths[:i]), table_start_y, header)

            for i, data in enumerate(table_data):
                for j, item in enumerate(data):
                    c.drawString(table_start_x + sum(col_widths[:j]), table_start_y - (i + 1) * row_height, str(item))

        if notes:
            c.drawString(100, table_start_y - (len(table_data) + 3) * row_height, "Notities:")
            notes_start_y = table_start_y - (len(table_data) + 4) * row_height
            c.setFont("Helvetica", 12)
            for i, note in enumerate(notes):
                if 'Type' in note:
                    c.drawString(100, notes_start_y - i * row_height, f"- {note['Type']}")

        c.showPage()
        c.save()

        response.seek(0)
        return send_file(
            response,
            as_attachment=True,
            download_name=f'result_{result_id}_data.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"message": f"Fout opgetreden: {str(e)}"}), 500
    
# Function to download a specific research result belonging to a patient
@app.route('/download_research_result_pdf/<int:patient_id>/<int:result_id>', methods=['GET'])
def download_research_result_pdf(patient_id, result_id):
    try:
        # Check if the patient exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()

        if not patient:
            return jsonify({"message": "Patient not found"})

        # Check if the research result exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM ResearchResults WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (result_id, patient_id))
        research_result = cur.fetchone()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()

        if not research_result:
            return jsonify({"message": "Research result not found"})

        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add a title
        pdf.cell(200, 10, txt="Research Result Data", ln=True, align='C')

        # Add research result data
        for key, value in dict(zip(column_names, research_result)).items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

        # Save the PDF to a bytes buffer
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, as_attachment=True, download_name=f'research_result_{result_id}_data.pdf', mimetype='application/pdf')

    except Exception as e:
        return jsonify({"message": "An error occurred"})

#   ----------------------------------
#   |   Appointments API Functions   |   
#   ----------------------------------

# Only use this endpoint for prototype purposes 
# It retrieves all appointments and associating user data 
# This can severly impact your DB if the DB is a large production DB
@app.route('/appointment/get_all', methods=['GET'])
def get_all_appointments():
    try:
        cur = mysql.connection.cursor()
        query = """
                SELECT a.Id as AppointmentId, a.Date, a.Description,
                        u.Id as UserId, u.Name, u.Lastname
                FROM Appointment a
                JOIN `Appointment-Users` au ON a.Id = au.AppointmentId
                JOIN User u ON au.UserId = u.Id
                """
        cur.execute(query)
        data = cur.fetchall()
       
        if not data:
            return jsonify([]), 200

        appointments = defaultdict(lambda: {
            'Date': '',
            'Description': '',
            'participants': {}
        })

        for row in data:
            appointment_id = row[0]
            if not appointments[appointment_id]['Date']:
                appointments[appointment_id].update({
                    'Date': row[1],
                    'Description': row[2]
                })
            user_id = row[3]
            appointments[appointment_id]['participants'][user_id] = {
                'name': row[4],
                'lastname': row[5]
            }

        appointments = dict(appointments)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
    return jsonify(appointments), 200

@app.route('/user/<int:user_id>/appointment', methods=['GET'])
def get_all_user_appointments(user_id):
    try:
        cur = mysql.connection.cursor()
        query = """
                    SELECT a.Id as AppointmentId, a.Date, a.Description,
                        u.Id as UserId, u.Name, u.Lastname, n.Type as NoteType
                    FROM Appointment a
                    JOIN `Appointment-Users` au1 ON a.Id = au1.AppointmentId
                    JOIN User u ON au1.UserId = u.Id
                    LEFT JOIN Note n ON a.Id = n.AppointmentId
                    WHERE a.Id IN (
                        SELECT a2.Id
                        FROM Appointment a2
                        JOIN `Appointment-Users` au2 ON a2.Id = au2.AppointmentId
                        WHERE au2.UserId = %s
                        )
                """
        cur.execute(query, (user_id,))
        rows = cur.fetchall()
        column_names = [desc[0] for desc in cur.description]

        # old code but keeping it incase we need to revert
        #data = [dict(zip(column_names, row)) for row in rows]
        data = [{key: row[key] for key in column_names if key in row} for row in rows]

        if not data:
            return jsonify([]), 200

        appointments = defaultdict(lambda: {
            'Date': '',
            'Description': '',
            'Participants': [],
            'Note': ''
        })

        for row in data:
            appointment_id = row['AppointmentId']
            appointments[appointment_id]['Date'] = row['Date']
            appointments[appointment_id]['Description'] = row['Description']
            
            participant = {'UserId': row['UserId'], 'Name': row['Name'], 'Lastname': row['Lastname']}
            if participant not in appointments[appointment_id]['Participants']:
                appointments[appointment_id]['Participants'].append(participant)
            
            # Check for 'NoteType' instead of 'NoteContent' and assign it to 'Note'
            if 'NoteType' in row and row['NoteType']:
                appointments[appointment_id]['Note'] = row['NoteType']

        appointments_list = list(appointments.values())

        return jsonify(appointments_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/appointment/create', methods=['POST'])
def create_appointment():
    try:
        """Appointment data is expected to be:
        {
            "date": "10-06-2024",
            "description": "CMAS afspraak",
            "participants": [1, 3]
        }
        """
        appointment_data = request.get_json()
        cur = mysql.connection.cursor()

        # Validate appointment data
        required_fields = ['date', 'description', 'participants']
        missing_fields = [field for field in required_fields if field not in appointment_data or (field == 'participants' and not appointment_data.get('participants'))]
        if missing_fields:
            return jsonify({"error": f"Missing required appointment data: {', '.join(missing_fields)}"}), 400

        # Check if all participants exist
        participants_exist = True
        for participant_id in appointment_data.get('participants', []):
            cur.execute("SELECT * FROM User WHERE Id = %s", (participant_id,))
            participant = cur.fetchone()
            if not participant:
                participants_exist = False
                break

        if not participants_exist:
            return jsonify({"error": "One or more participants not found"}), 404

        # Add appointment
        cur.execute("""
                    INSERT INTO Appointment (Date, Description) 
                    VALUES (%s, %s)
                    """, 
                    (appointment_data['date'], appointment_data['description']))
        mysql.connection.commit()

        cur.execute("SELECT LAST_INSERT_ID()")
        appointment_id = cur.fetchone()[0]

        for participant in appointment_data.get('participants'):
            cur.execute("""
                        INSERT into `Appointment-Users` (AppointmentId, UserId)
                        VALUES (%s, %s)
                        """,
                        (appointment_id, participant))
        mysql.connection.commit()

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
    return jsonify({"message": "Appointment added successfully"}), 200

@app.route('/appointment/<int:appointment_id>/update', methods=['PUT'])
def update_appointment(appointment_id):
    try:
        """Appointment data is expected to be:
        {
            "date": "2024-06-11 00:00:00",
            "description": "CMAS afspraak",
            "participants": [1, 3]
        }
        """
        appointment_data = request.get_json()
        cur = mysql.connection.cursor()

        # Validate appointment data
        required_fields = ['date', 'description', 'participants']
        missing_fields = [field for field in required_fields if field not in appointment_data or (field == 'participants' and not appointment_data.get('participants'))]
        if missing_fields:
            return jsonify({"error": f"Missing required appointment data: {', '.join(missing_fields)}"}), 400

        # Check if all participants exist
        participants_exist = True
        for participant_id in appointment_data.get('participants', []):
            cur.execute("SELECT * FROM User WHERE Id = %s", (participant_id,))
            participant = cur.fetchone()
            if not participant:
                participants_exist = False
                break

        if not participants_exist:
            return jsonify({"error": "One or more participants not found"}), 404

        # Check if the appointment exist
        cur.execute("SELECT * FROM Appointment WHERE Id = %s", (appointment_id,))
        result = cur.fetchone()[0]
        appointment = result > 0
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404

        # Update appointment
        cur.execute("""
                    UPDATE Appointment 
                    SET Date = %s, Description = %s 
                    WHERE Id = %s
                    """, 
                    (appointment_data['date'], appointment_data['description'], appointment_id))
        mysql.connection.commit()

        # Retrieve existing participants
        cur.execute("SELECT UserId FROM `Appointment-Users` WHERE AppointmentId = %s", (appointment_id,))
        existing_participants = set(row[0] for row in cur.fetchall())

        # Identify participants
        new_participants = set(appointment_data['participants'])
        participants_to_add = new_participants - existing_participants
        participants_to_remove = existing_participants - new_participants

        for participant_id in participants_to_add:
            cur.execute("INSERT INTO `Appointment-Users` (AppointmentId, UserId) VALUES (%s, %s)", (appointment_id, participant_id))

        for participant_id in participants_to_remove:
            cur.execute("DELETE FROM `Appointment-Users` WHERE AppointmentId = %s AND UserId = %s", (appointment_id, participant_id))

        mysql.connection.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
    return jsonify({"message": "Appointment updated successfully"}), 200

@app.route('/appointment/<int:appointment_id>/delete', methods=['DELETE'])
def delete_appointment(appointment_id):
    try:
        # Check if appointment exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Appointment WHERE Id = %s", (appointment_id,))
        appointment = cur.fetchone()

        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404

        cur.execute("START TRANSACTION")
        cur.execute("""
                    DELETE FROM `Appointment-Users`
                    WHERE AppointmentId = %s
                    """,
                    (appointment_id,))
        cur.execute("""
                    DELETE FROM Appointment
                    WHERE Id = %s
                    """, 
                    (appointment_id,))

        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
    return jsonify({"message": "Appointment deleted successfully"}), 200

@app.route('/user/<int:user_id>/appointment/get', methods=['GET'])
def get_user_appointments(user_id):
    try:
        cur = mysql.connection.cursor()

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({"error": "start_date and end_date are required"}), 400

        # Validate start and end dates as DateTime
        date_format = "%Y-%m-%d"
        try:
            start_date_obj = datetime.strptime(start_date, date_format)
            end_date_obj = datetime.strptime(end_date, date_format)
        except ValueError:
            return jsonify({"error": f"Dates must be in the format {date_format}"}), 400
        
        # Check if user exists in DB
        cur.execute("SELECT * FROM User WHERE Id = %s", (user_id,))
        user = cur.fetchone()

        if not user:
            return jsonify({"error": 'User not found'}), 400

        # Get all appointments of user within a certain timeframe
        cur.execute("""
                    SELECT a.Id as AppointmentId, a.Date, a.Description,
                        u.Id as UserId, u.Name, u.Lastname
                    FROM Appointment a
                    JOIN `Appointment-Users` au ON a.Id = au.AppointmentId
                    JOIN User u ON au.UserId = u.Id
                    WHERE au.UserId = %s AND a.date >= %s AND a.date <= %s
                    """, 
                    (user_id, start_date, end_date))
        data = cur.fetchall()
       
        if not data:
            return jsonify([]), 200

        appointments = defaultdict(lambda: {
            'Date': '',
            'Description': '',
            'participants': {}
        })

        for row in data:
            appointment_id = row[0]
            if not appointments[appointment_id]['Date']:
                appointments[appointment_id].update({
                    'Date': row[1],
                    'Description': row[2]
                })
            user_id = row[3]
            appointments[appointment_id]['participants'][user_id] = {
                'name': row[4],
                'lastname': row[5]
            }

        appointments = dict(appointments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
    return jsonify(appointments), 200

@app.route('/user/search', methods=['POST'])
def get_user_by_string():
    try:
        data = request.get_json()
        search_string = f"%{data['search_string']}%"
        cur = mysql.connection.cursor()
        cur.execute("""
                SELECT u.id, u.name, u.lastname
                FROM User u
                WHERE u.name LIKE %s OR u.lastname LIKE %s
                """, (search_string, search_string))
        data = cur.fetchall()
        if not data:
            return jsonify([]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
    return jsonify(data), 200

if __name__ == '__main__':  # Uitvoeren
    app.run(debug=True)

