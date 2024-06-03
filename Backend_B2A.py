from flask import Flask, jsonify, request, send_file
from flask_mysqldb import MySQL
from flask_cors import CORS
from fpdf import FPDF
import base64
import io
import logging

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = '20.16.87.228'
app.config['MYSQL_USER'] = 'Userb2a'
app.config['MYSQL_PASSWORD'] = 'DitIsEchtHeelLeukBlok3006'
app.config['MYSQL_DB'] = 'your_database_name'
mysql = MySQL(app)

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
    try:
        # Get the updated data from the request body
        updated_data = request.get_json()

        # Check if the patient exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()

        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Update the patient's information
        cur = mysql.connection.cursor()
        query = "UPDATE User SET "
        values = []
        for key, value in updated_data.items():
            query += f"{key} = %s, "
            values.append(value)
        query = query[:-2]  # Remove the trailing comma and space
        query += " WHERE Id = %s"
        values.append(patient_id)
        cur.execute(query, tuple(values))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Patient information updated successfully"})

    except Exception as e:
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
        required_fields = ['name', 'dosage', 'start_date', 'frequency']
        for field in required_fields:
            if field not in medication_data:
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
        query = "INSERT INTO Medication (PatientId, Name, Dosage, StartDate, Frequency) VALUES (%s, %s, %s, %s, %s)"
        cur.execute(query, (patient_id, medication_data['name'], medication_data['dosage'], medication_data['start_date'], medication_data['frequency']))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Medication added successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update medication for a patient
@app.route('/patients/<int:patient_id>/medication/<int:medication_id>', methods=['PUT'])
def update_medication(patient_id, medication_id):
    try:
        medication_data = request.get_json()

        # Validate medication data
        required_fields = ['name', 'dosage', 'start_date', 'frequency']
        for field in required_fields:
            if field not in medication_data:
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

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
        query = "UPDATE Medication SET Name = %s, Dosage = %s, StartDate = %s, Frequency = %s WHERE Id = %s"
        cur.execute(query, (medication_data['name'], medication_data['dosage'], medication_data['start_date'], medication_data['frequency'], medication_id))
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
    
# Add a diagnosis for a patient
@app.route('/patients/<int:patient_id>/diagnosis', methods=['POST'])
def add_diagnosis(patient_id):
    try:
        diagnosis_data = request.get_json()

        # Validate diagnosis data
        required_fields = ['doctor_id', 'diagnosis', 'description', 'date']
        for field in required_fields:
            if field not in diagnosis_data:
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Check if the patient exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM User WHERE Id = %s AND Role = '2'"
        cur.execute(query, (patient_id,))
        patient = cur.fetchone()
        cur.close()

        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        # Add diagnosis for the patient
        cur = mysql.connection.cursor()
        query = "INSERT INTO Diagnosis (PatientId, DoctorId, Diagnosis, Description, Date) VALUES (%s, %s, %s, %s, %s)"
        cur.execute(query, (patient_id, diagnosis_data['doctor_id'], diagnosis_data['diagnosis'], diagnosis_data['description'], diagnosis_data['date']))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Diagnosis added successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a diagnosis for a patient
@app.route('/patients/<int:patient_id>/diagnosis/<int:diagnosis_id>', methods=['PUT'])
def update_diagnosis(patient_id, diagnosis_id):
    try:
        diagnosis_data = request.get_json()

        # Validate diagnosis data
        required_fields = ['doctor_id', 'diagnosis', 'description', 'date']
        for field in required_fields:
            if field not in diagnosis_data:
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Check if the diagnosis exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Diagnosis WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (diagnosis_id, patient_id))
        diagnosis = cur.fetchone()
        cur.close()

        if not diagnosis:
            return jsonify({"error": "Diagnosis not found for this patient"}), 404

        # Update diagnosis for the patient
        cur = mysql.connection.cursor()
        query = "UPDATE Diagnosis SET DoctorId = %s, Diagnosis = %s, Description = %s, Date = %s WHERE Id = %s"
        cur.execute(query, (diagnosis_data['doctor_id'], diagnosis_data['diagnosis'], diagnosis_data['description'], diagnosis_data['date'], diagnosis_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Diagnosis updated successfully"})

    except Exception as e:
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
    
# Create an Exercise
@app.route('/patients/<int:patient_id>/exercises', methods=['POST'])
def add_patient_exercise(patient_id):
    try:
        exercise_data = request.get_json()

        # Validate exercise data
        required_fields = ['name', 'description', 'cmas_id']
        for field in required_fields:
            if field not in exercise_data:
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Check if the CMAS exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM CMAS WHERE Id = %s"
        cur.execute(query, (exercise_data['cmas_id'],))
        cmas = cur.fetchone()
        cur.close()

        if not cmas:
            return jsonify({"error": "CMAS not found"}), 404

        # Add exercise for the patient
        cur = mysql.connection.cursor()
        query = "INSERT INTO Exercise (Name, Description, CMASId) VALUES (%s, %s, %s)"
        cur.execute(query, (exercise_data['name'], exercise_data['description'], exercise_data['cmas_id']))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Exercise added successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Get a patient's exercises
@app.route('/patients/<int:patient_id>/exercises', methods=['GET'])
def get_patient_exercises(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT E.* 
            FROM Exercise E
            INNER JOIN CMAS C ON E.CMASId = C.Id
            INNER JOIN Result R ON C.ResultId = R.Id
            WHERE R.PatientId = %s
        """
        cur.execute(query, (patient_id,))
        exercises = cur.fetchall()

        if not exercises:
            return jsonify([])

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        exercises_list = [dict(zip(column_names, row)) for row in exercises]

        return jsonify(exercises_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get a specific exercise
@app.route('/patients/<int:patient_id>/exercises/<int:exercise_id>', methods=['GET'])
def get_patient_exercise(patient_id, exercise_id):
    try:
        cur = mysql.connection.cursor()
        query = """
            SELECT E.* 
            FROM Exercise E
            INNER JOIN CMAS C ON E.CMASId = C.Id
            INNER JOIN Result R ON C.ResultId = R.Id
            WHERE R.PatientId = %s AND E.Id = %s
        """
        cur.execute(query, (patient_id, exercise_id))
        exercise = cur.fetchone()

        if not exercise:
            return jsonify({"error": "Exercise not found"}), 404

        column_names = [desc[0] for desc in cur.description]
        exercise_dict = dict(zip(column_names, exercise))
        cur.close()

        return jsonify(exercise_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update a patient's exercise
@app.route('/patients/<int:patient_id>/exercises/<int:exercise_id>', methods=['PUT'])
def update_patient_exercise(patient_id, exercise_id):
    try:
        exercise_data = request.get_json()

        # Validate exercise data
        required_fields = ['name', 'description', 'cmas_id']
        for field in required_fields:
            if field not in exercise_data:
                return jsonify({"error": f"{field.capitalize()} is a required field"}), 400

        # Check if the exercise exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = """
            SELECT E.* 
            FROM Exercise E
            INNER JOIN CMAS C ON E.CMASId = C.Id
            INNER JOIN Result R ON C.ResultId = R.Id
            WHERE R.PatientId = %s AND E.Id = %s
        """
        cur.execute(query, (patient_id, exercise_id))
        exercise = cur.fetchone()
        cur.close()

        if not exercise:
            return jsonify({"error": "Exercise not found for this patient"}), 404

        # Update exercise for the patient
        cur = mysql.connection.cursor()
        query = "UPDATE Exercise SET Name = %s, Description = %s, CMASId = %s WHERE Id = %s"
        cur.execute(query, (exercise_data['name'], exercise_data['description'], exercise_data['cmas_id'], exercise_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Exercise updated successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Delete a patient's exercise
@app.route('/patients/<int:patient_id>/exercises/<int:exercise_id>', methods=['DELETE'])
def delete_patient_exercise(patient_id, exercise_id):
    try:
        # Check if the exercise exists and belongs to the patient
        cur = mysql.connection.cursor()
        query = """
            SELECT E.* 
            FROM Exercise E
            INNER JOIN CMAS C ON E.CMASId = C.Id
            INNER JOIN Result R ON C.ResultId = R.Id
            WHERE R.PatientId = %s AND E.Id = %s
        """
        cur.execute(query, (patient_id, exercise_id))
        exercise = cur.fetchone()
        cur.close()

        if not exercise:
            return jsonify({"error": "Exercise not found for this patient"}), 404

        # Delete the exercise
        cur = mysql.connection.cursor()
        query = "DELETE FROM Exercise WHERE Id = %s"
        cur.execute(query, (exercise_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Exercise deleted successfully"})

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
    
# Function to generate a PDF of a specific test result belonging to a patient
@app.route('/download_test_result_pdf/<int:patient_id>/<int:test_result_id>', methods=['GET'])
def download_test_result_pdf(patient_id, test_result_id):
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

        # Check if the test result exists
        cur = mysql.connection.cursor()
        query = "SELECT * FROM TestResults WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (test_result_id, patient_id))
        test_result = cur.fetchone()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()

        if not test_result:
            return jsonify({"message": "Test result not found"})

        # Check if there are any notes attached to the test result
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Notes WHERE TestResultId = %s"
        cur.execute(query, (test_result_id,))
        notes = cur.fetchall()
        column_names = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()

        # Convert the test result and notes to dictionaries
        test_result_dict = dict(zip(column_names, test_result))
        notes_list = [dict(zip(column_names, row)) for row in notes]

        # Create a PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add a title
        pdf.cell(200, 10, txt="Test Result Data", ln=True, align='C')

        # Add test result data
        for key, value in test_result_dict.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

        # Add notes
        pdf.cell(200, 10, txt="Notes:", ln=True)
        for note in notes_list:
            pdf.cell(200, 10, txt=f"- {note['note']}", ln=True)

        # Save the PDF to a bytes buffer
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, as_attachment=True, download_name=f'test_result_{test_result_id}_data.pdf', mimetype='application/pdf')

    except Exception as e:
        return jsonify({"message": "An error occurred"})
    
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


if __name__ == '__main__':  # Uitvoeren
    app.run(debug=True)