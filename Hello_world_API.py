from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
import urllib

app = Flask(__name__)
CORS(app)

params = urllib.parse.quote_plus("DRIVER={SQL Server};SERVER=.;DATABASE=Flasktesting;Trusted_Connection=yes")
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc:///?odbc_connect=%s" % params
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class DataTable(db.Model):
    __tablename__ = 'DataTable'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(255))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

@app.route('/Hello_World')
def hello():
    return 'Hello, World!'

@app.route('/post_data', methods=['POST'])
def post_data():
    data = request.json.get('value')  # Changed 'data' to 'value'
    print("Received data: ", data)
    if data:
        try:
            new_data = DataTable(data=data)
            print("New data object: ", new_data)
            db.session.add(new_data)
            db.session.commit()
            return 'Data posted successfully'
        except Exception as e:
            print("An error occurred: ", str(e))
            return 'An error occurred while posting data: ' + str(e)
    else:
        return 'Invalid data'

@app.route('/data', methods=['GET'])
def get_data():
    data = DataTable.query.all()
    print("Data", data)
    return jsonify([datum.to_dict() for datum in data])

if __name__ == '__main__':
    app.run()