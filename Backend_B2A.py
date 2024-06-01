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
