from flask import Flask
from flask_restful import Api

from urls import apply_resources


app = Flask(__name__)
api = Api(app)

apply_resources(api)

if __name__ == '__main__':
    app.run(debug=True)
