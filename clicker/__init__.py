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
        self.createNewClass(db, args)
        return 200
        
    def createNewClass(self, db, args):
        username = args['user']
        collection = db['ids']
        className = args['className']
        code = self.getCode(collection)
        classes = db['classes']
        mapping = db['mapping']
        if self.checkUserName(collection, username):
            mapping.update_one({"_id": username},  {"$set": {"Classes." + code: className}})
            classes.insert_one({"_id":code, "user": username,"class": className, "status":False})
            collection.update_one({"_id": 0}, {"$addToSet": {"ids": code}})
        else:
            mapping.insert_one({"_id": username, "Classes" : {code: className}})
            classes.insert_one({"_id":code, "user": username,"class": className, "status":False})
            collection.update_one({"_id": 0}, {"$addToSet": {"ids": code}})
            collection.update_one({"_id": 0}, {"$addToSet": {"names": username}})

    def checkUserName(self, collection, username):
        ids = collection.find({"_id": 0})
        if username in ids[0]["names"]:
            return True
        else:
            return False
    
    def getCode(self, collection):
        while True:
            code = randomStringDigits(10)
            ids = collection.find({"_id": 0})
            if code not in ids[0]["ids"]:
                return code

class deleteUser(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', required=True)
        args = parser.parse_args()
        client = pymongo.MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
        db = client['clicker']
        return self.deleteUser(db, args['user'])

    def deleteUser(self, db, username):
        mapping = db['mapping']
        classes = db['classes']
        collection = db['ids']
        try:
            ids = mapping.find_one({"_id":username})['Classes']
            results = mapping.delete_one({"_id": username})
            results = classes.find({"user": username})
            for result in results:
                data = classes.delete_one({"_id": result['_id']})
            collection.update({"_id": 0}, {"$pull": {"names": username}})
            for tag in ids.keys():
                collection.update({"_id": 0}, {"$pull": {"ids": tag}})
            return 200
        except Exception as e:
            return str(e)

api.add_resource(createClass, '/createClass')
api.add_resource(deleteUser, '/deleteUser')