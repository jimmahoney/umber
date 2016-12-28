from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 0 + 'Hello, World!'  # A error for the debugger.
