from flask import Flask, g, render_template
from flask_restful import Resource, Api, reqparse
import json
import pymongo
import random
import string
import json

app = Flask(__name__)
api = Api(app)

@app.route("/")
def index():
  f = open("swagger.json", 'r')
  return json.load(f)

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/createClass")
def user():
    return render_template("createClass.html")

@app.route("/client")
def client():
    return render_template("client.html")

def randomStringDigits(length):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(length))

def getDB():
    client = pymongo.MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
    db = client['clicker']
    collection = db['ids']
    classes = db['classes']
    mapping = db['mapping']
    return collection, classes, mapping

class createClass(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', required=True)
        parser.add_argument('className', required=True)
        args = parser.parse_args()
        return self.createNewClass(args)
        
    def createNewClass(self, args):
        collection, classes, mapping = getDB()
        username = args['user']
        className = args['className']
        code = self.getCode(collection)
        if self.checkUserName(collection, username):
            if self.checkClass(mapping, username, className):
                return 400
            mapping.update_one({"_id": username},  {"$set": {"Classes." + code: className}})
            classes.insert_one({"_id":code, "user": username,"class": className, "answers": {}, "status":False})
            collection.update_one({"_id": 0}, {"$addToSet": {"ids": code}})
        else:
            mapping.insert_one({"_id": username, "Classes" : {code: className}})
            classes.insert_one({"_id":code, "user": username,"class": className, "answers": {}, "status":False})
            collection.update_one({"_id": 0}, {"$addToSet": {"ids": code}})
            collection.update_one({"_id": 0}, {"$addToSet": {"names": username}})
        return 200

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

    def checkClass(self, mapping, username, name):
        data = mapping.find_one({'_id': username})['Classes']
        for className in data.keys():
            if data.get(className) == name:
                return True
        return False


class deleteUser(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', required=True)
        args = parser.parse_args()
        return self.deleteUser(args['user'])

    def deleteUser(self, username):
        collection, classes, mapping = getDB()
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
        return self.deleteClass(args['user'], args['className'])

    def deleteClass(self, username, className):
        collection, classes, mapping = getDB()
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
    def get(self, user, className):
        collection, classes, mapping = getDB()
        try:
            targetId = self.getID(mapping, user, className)
            return str(classes.find_one({"_id": targetId})['status'])
        except Exception as e:
            return str(e)

    def post(self, user, className):
        parser = reqparse.RequestParser()
        parser.add_argument('status', required=True)
        args = parser.parse_args()
        collection, classes, mapping = getDB()
        try:
            targetId = self.getID(mapping, user, className)
            classes.update({"_id": targetId}, {"$set": {"status": bool(args['status'] == "true")}})
            return classes.find_one({"_id": targetId})['status']
        except Exception as e:
            return str(e)

    def getID(self, mapping, user, className):
        ids = mapping.find_one({"_id":user})['Classes']
        targetId = None
        for tag in ids.keys():
            if ids.get(tag) == className:
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
        collection, classes, mapping = getDB()
        targetId = pollStatus.getID(self, mapping, args['user'], args['className'])
        if classes.find_one({"_id": targetId})['status']:
            if args['client'] not in classes.find_one({"_id": targetId})['answers'].keys():
                classes.update_one({"_id": targetId}, {"$set": {"answers." + args['client']: args['answer']}})
                return 200
            return "name taken"
        return "not open"

class report(Resource):
    def get(self, user, className):
        collection, classes, mapping = getDB()
        targetId = pollStatus.getID(self, mapping, user, className)
        try:
            classData = classes.find_one({"_id": targetId})
            if not classData['status']:
                return classData['answers']
            else:
                return "poll still open"
        except Exception as e:
            return str(e)

api.add_resource(createClass, '/createClass')
api.add_resource(deleteUser, '/deleteUser')
api.add_resource(deleteClass, '/deleteClass')
api.add_resource(pollStatus, '/pollStatus/<string:user>/<string:className>')
api.add_resource(answer, '/answer')
api.add_resource(report, '/report/<string:user>/<string:className>')