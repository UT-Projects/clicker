from flask import Flask, g
from flask_restful import Resource, Api, reqparse
import json
import pymongo

app = Flask(__name__)
api = Api(app)

@app.route("/")
def index():
    return "HELLO WOLRD"

class poll(Resource):
    def post(self):
        client = pymongo.MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
        db = client['clicker'] 
        collection = db['clicker']
        parser = reqparse.RequestParser()
        parser.add_argument('pollStatus', required=True)
        parser.add_argument('classCode', required=True)
        args = parser.parse_args()
        return "" + args['classCode'] + " :: " + args['pollStatus']

api.add_resource(poll, '/poll')