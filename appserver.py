from flask import Flask
from testmachine import main
from ProductTrials import main as productdetail
from flask import jsonify
from flask_caching import Cache
from flask_cors import CORS

app = Flask(__name__)
cache = Cache(app,config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
CORS(app)
@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/company/<name>')
@cache.cached(timeout=50000)
def company(name):
    try:
        return jsonify(main(name))
    except Exception as Ex:
        return jsonify({"error":str(Ex)})
        
@app.route('/trial/<name>')
@cache.cached(timeout=50000)
def product(name):
    try:    
        return jsonify(productdetail(name))
    except Exception as Ex:
        return jsonify({"error":str(Ex)})
        
if  __name__=='__main__':
    app.run(host="0.0.0.0",port=5555,threaded=True)