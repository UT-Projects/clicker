from flask import Flask, g, render_template
from flask_restful import Resource, Api, reqparse
import json
import pymongo
import random
import string

app = Flask(__name__)
api = Api(app)

@app.route("/")
def index():
    return render_template("index.html")

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
            classes.insert_one({"_id":code, "user": username,"class": className, "answers": {}, "status":False})
            collection.update_one({"_id": 0}, {"$addToSet": {"ids": code}})
        else:
            mapping.insert_one({"_id": username, "Classes" : {code: className}})
            classes.insert_one({"_id":code, "user": username,"class": className, "answers": {}, "status":False})
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
        except Exception as e:
            return str(e)
        return 200

class deleteClass(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', required=True)
        parser.add_argument('className', required=True)
        args = parser.parse_args()
        client = pymongo.MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
        db = client['clicker']
        return self.deleteClass(args['user'], args['className'], db)

    def deleteClass(self, username, className, db):
        mapping = db['mapping']
        classes = db['classes']
        collection = db['ids']
        try:
            ids = mapping.find_one({"_id":username})['Classes']
            for tag in ids.keys():
                if ids.get(tag) == className:
                    targetId = tag
                    break
            mapping.update({"_id": username}, {"$unset": {"Classes." + str(targetId): ""}})
            results = classes.delete_one({"_id": targetId})
            collection.update({"_id": 0}, {"$pull": {"ids": targetId}})
        except Exception as e:
            return str(e)
        return 200

class pollStatus(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', required=True)
        parser.add_argument('className', required=True)
        args = parser.parse_args()
        client = pymongo.MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
        classes = client['clicker']['classes']
        mapping = client['clicker']['mapping']
        try:
            targetId = self.getID(mapping, args)
            return classes.find_one({"_id": targetId})['status']
        except Exception as e:
            return str(e)

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', required=True)
        parser.add_argument('className', required=True)
        parser.add_argument('status', required=True)
        args = parser.parse_args()
        client = pymongo.MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
        classes = client['clicker']['classes']
        mapping = client['clicker']['mapping']
        try:
            targetId = self.getID(mapping, args)
            classes.update({"_id": targetId}, {"$set": {"status": bool(args['status'] == "true")}})
            return classes.find_one({"_id": targetId})['status']
        except Exception as e:
            return str(e)

    def getID(self, mapping, args):
        ids = mapping.find_one({"_id":args['user']})['Classes']
        targetId = None
        for tag in ids.keys():
            if ids.get(tag) == args['className']:
                targetId = tag
                break
        return targetId

class answer(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('client', required=True)
        parser.add_argument('user', required=True)
        parser.add_argument('className', required=True)
        parser.add_argument('answer', required=True)
        args = parser.parse_args()
        client = pymongo.MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
        classes = client['clicker']['classes']
        mapping = client['clicker']['mapping']
        targetId = pollStatus.getID(self, mapping, args)
        if classes.find_one({"_id": targetId})['status']:
            if args['client'] not in classes.find_one({"_id": targetId})['answers'].keys():
                classes.update_one({"_id": targetId}, {"$set": {"answers." + args['client']: args['answer']}})
                return 200
            return "name taken"
        return "not open"

api.add_resource(createClass, '/createClass')
api.add_resource(deleteUser, '/deleteUser')
api.add_resource(deleteClass, '/deleteClass')
api.add_resource(pollStatus, '/pollStatus')
api.add_resource(answer, '/answer')