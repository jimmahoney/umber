# flask hello world - sort of

from flask import Flask
app = Flask(__name__)

print "==>  hello.py"
print "==>  app={}".format(app)

@app.route('/', defaults={'path':''})
@app.route('/<path:path>')
def catchall(path):
    print "==> catchall('{}')".format(path)
    return "hello path '{}'".format(path)
