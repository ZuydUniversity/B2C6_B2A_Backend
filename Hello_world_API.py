from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Home!"

@app.route("/world")
def world():
    return "Hello world!"

if __name__ == '__main__':
    app.run(debug=True)