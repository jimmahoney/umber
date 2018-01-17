# flask hello world - sort of. For debugging.

from flask import Flask
app = Flask('hello')

print "==>  hello.py"
print "==>  app={}".format(app)

@app.route('/', defaults={'path':''})
@app.route('/<path:path>')
def catchall(path):
    print "==> catchall('{}')".format(path)
    return "hello path '{}'".format(path)
