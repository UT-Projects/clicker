from flask import Flask, g
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

@app.route("/")
def index():
    return "HELLO WOLRD"

class getString(Resource):
    def get(self, identifier):
        return identifier

api.add_resource(getString, '/getString/<string:identifier>')