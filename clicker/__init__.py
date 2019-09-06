from flask import Flask, g
from flask_restful import Resource, Api, reqparse
import json
import pymongo
import random
import string

app = Flask(__name__)
api = Api(app)

@app.route("/")
def index():
    return "HELLO WOLRD"

def randomStringDigits(length):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(length))

class createClass(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', required=True)
        parser.add_argument('className', required=True)
        args = parser.parse_args()
        client = pymongo.MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
        db = client['clicker']
        createNewClass(db, args['user'])
        
    def createNewClass(db, username):
        collection = db['ids']
        code = getCode(collection)
        mapping = db['mapping']
        if checkUserName(collection, username):
            mapping.update_one({"_id": username}, {"$addToSet": {"classes": code}})
        else:
            mapping.insert_one({"_id": username, "classes": [code]})
            classes = db['classes']
            classes.insert_one({"_id":code, "name": username, "status":False})
        
        

    def checkUserName(collection, username):
        ids = collection.find({"_id": 0})
        if username in ids[0]["names"]:
            return False
        else:
            return True
    
    def getCode(collection):
        while True:
            code = randomStringDigits(10)
            ids = collection.find({"_id": 0})
            if code not in ids[0]["ids"]:
                return code

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