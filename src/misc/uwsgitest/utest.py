# utest.py - flask application

from flask import Flask
app = Flask(__name__)

@app.route("/utest/")  
def hello():
    return "<h1 style='color:blue'>Hello from 'utest' !</h1>"

if __name__ == "__main__":
    app.run(host='0.0.0.0')
