from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS
import base64
from flask import send_file
from fpdf import FPDF
import io

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

# DOCTOR FUNCTIONS

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
    
# PATIENT FUNCTIONS

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

# delete a patient
@app.route('/delete_patient/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "DELETE FROM User WHERE Id = %s"
        cur.execute(query, (patient_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Patient deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

# Get a patient their diagnosis
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
    
# Get a patient their test results
@app.route('/patients/<int:patient_id>/test_results', methods=['GET'])
def get_patient_test_results(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM TestResults WHERE PatientId = %s"
        cur.execute(query, (patient_id,))
        test_results = cur.fetchall()

        if not test_results:
            return jsonify({"error": "No test results found for this patient"}), 404

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        test_results_list = [dict(zip(column_names, row)) for row in test_results]

        return jsonify(test_results_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Add a note for a specific patient's test result
@app.route('/add_note/<int:patient_id>/<int:test_result_id>', methods=['POST'])
def add_note(patient_id, test_result_id):
    try:
        # Get the note from the request body
        note = request.get_json()['note']

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
        query = "SELECT * FROM TestResults WHERE Id = %s AND PatientId = %s"
        cur.execute(query, (test_result_id, patient_id))
        test_result = cur.fetchone()
        cur.close()

        if not test_result:
            return jsonify({"message": "Test result not found"})

        # Add the note to the test result
        cur = mysql.connection.cursor()
        query = "UPDATE TestResults SET Note = %s WHERE Id = %s"
        cur.execute(query, (note, test_result_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Note added successfully"})

    except Exception as e:
        return jsonify({"message": "An error occurred"})
    
# Get the notes belonging to a test result
@app.route('/test_results/<int:test_result_id>/notes', methods=['GET'])
def get_test_result_notes(test_result_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Notes WHERE TestResultId = %s"
        cur.execute(query, (test_result_id,))
        notes = cur.fetchall()

        if not notes:
            return jsonify([])

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        notes_list = [dict(zip(column_names, row)) for row in notes]

        return jsonify(notes_list)
    except Exception as e:
        return jsonify({"message": "An error occurred"})
    
# Get a patient's appointments
@app.route('/patients/<int:patient_id>/appointments', methods=['GET'])
def get_patient_appointments(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Appointments WHERE PatientId = %s"
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
    
# Get a patient's performed exercises
@app.route('/patients/<int:patient_id>/exercises', methods=['GET'])
def get_patient_exercises(patient_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT * FROM Exercises WHERE PatientId = %s"
        cur.execute(query, (patient_id,))
        exercises = cur.fetchall()

        if not exercises:
            return jsonify([])

        column_names = [desc[0] for desc in cur.description]
        cur.close()

        exercises_list = [dict(zip(column_names, row)) for row in exercises]

        return jsonify(exercises_list)
    except Exception as e:
        return

# Function to generate a PDF of a specific patient's data (Needs testing and probably some adjustments)
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

if __name__ == '__main__':  # Uitvoeren
    app.run(debug=True)
