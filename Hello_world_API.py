from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Home!"

@app.route("/world")
def world():
    return "Hello world!"

if __name__ == '__main__':
    app.run(debug=True)