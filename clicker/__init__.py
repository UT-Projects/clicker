from flask import Flask, g, render_template, request, session, redirect, url_for, jsonify
from flask_restful import Resource, Api, reqparse
from flask_pymongo import PyMongo
import json
import pymongo
import random
import string
import json
import bcrypt
from os import path
from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'clicker'                  # mongoDB authentication to be moved to config file and enconded
app.config['MONGO_URI'] = 'mongodb+srv://db:db@clicker-ancot.mongodb.net/clicker?retryWrites=true&w=majority'
api = Api(app)

mongo = PyMongo(app)

@app.route("/")
def index():                    # Default path open swagger API docs
  f = open("swagger.json", 'r')
  return json.load(f)

@app.route("/home")             # Homepage for registering and loggin in
def home():
    return render_template("home.html")

@app.route("/register", methods=['POST', 'GET'])        # Registering page, to be changed to Google Log in 
def register():
    return render_template('register.html')

@app.route("/poll")     # Answering page
def poll():
    return render_template("poll.html")

@app.route("/user")     # Professor Overview page
def user():
    return render_template("user.html")

@app.route("/classes")  # Classes display page
def classes():
    return render_template("classes.html")

@app.route("/client")   # Student main page
def client():
    return render_template("client.html")

@app.route("/userHome")
def userHome():
    return render_template("userHome.html")

@app.route('/userSettings')
def userSettings():
    return render_template("settings.html")

def randomStringDigits(length):     # Code Generation for class ids 
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(length))

class registerUser(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('_id', required=True)
        parser.add_argument('type', required=True)
        parser.add_argument('name', required=True)
        args = parser.parse_args()
        mongo.db.users.insert_one(args)
        return 201

class verifyUser(Resource):
    def get(self, idtoken):
        owd = path.dirname(__file__)
        credFile = owd[:owd.rfind("clicker")] + "credentials.json"
        with open(credFile) as f:
            data = json.load(f)
        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            idinfo = id_token.verify_oauth2_token(idtoken, requests.Request(), data.get('web').get('client_id'))

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # ID token is valid. Get the user's Google Account ID from the decoded token.
            userid = idinfo['sub']
            test = self.checkUser(userid)
            # print(mongo.db.users.find_one({"_id": userid}), flush=True)
            if(mongo.db.users.find_one({"_id": userid}) == None):
                return jsonify(dict(redirect='register'))
            else:
                # return mongo.db.users.find({"_id": userid})
                return jsonify(dict(redirect='userHome'))
        except Exception as e:
            print("Error:: ", flush=True)
            print(e, flush=True)
            # Invalid token
            return jsonify(dict(redirect='home', logout='True'))
    
    def checkUser(self, userid):
        if mongo.db.users.find({"_id": userid}) != None:
            return
        else:
            register(userid)

class createClass(Resource):        # Endpoint creates a class object in the db
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', required=True)
        parser.add_argument('className', required=True)
        args = parser.parse_args()
        return self.createNewClass(args)
        
    def createNewClass(self, args):
        username = args['user']
        className = args['className']
        code = self.getCode()
        if self.checkUserName(username):    # Check if username exists; add to existing user data or create new user
            if self.checkClass(username, className):
                return 400
            mongo.db.mapping.update_one({"_id": username},  {"$set": {"Classes." + code: className}})
            mongo.db.classes.insert_one({"_id":code, "user": username,"class": className, "answers": {}, "status":False})
            mongo.db.ids.update_one({"_id": 0}, {"$addToSet": {"ids": code}})
        else:
            mongo.db.mapping.insert_one({"_id": username, "Classes" : {code: className}})
            mongo.db.classes.insert_one({"_id":code, "user": username,"class": className, "answers": {}, "status":False})
            mongo.db.ids.update_one({"_id": 0}, {"$addToSet": {"ids": code}})
            mongo.db.ids.update_one({"_id": 0}, {"$addToSet": {"names": username}})
        return 200

    def checkUserName(self, username):      # Check if username exists
        ids = mongo.db.ids.find({"_id": 0})
        if username in ids[0]["names"]:
            return True
        else:
            return False
    
    def getCode(self):      # Retrieve code for class ids
        while True:
            code = randomStringDigits(10)
            ids = mongo.db.ids.find({"_id": 0})
            if code not in ids[0]["ids"]:
                return code

    def checkClass(self, username, name):       # Check if a class name exists in the db
        data = mongo.db.mapping.find_one({'_id': username})['Classes']
        for className in data.keys():
            if data.get(className) == name:
                return True
        return False

class deleteUser(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('userid', required=True)
        args = parser.parse_args()
        print(args['userid'], flush=True)
        username = mongo.db.users.find_one({'_id': args['userid']})['name']
        print(username, flush=True)
        return self.deleteUser(args['userid'], username)

    def deleteUser(self, userid, username):     # Delete the user entirely from the backend
        try:
            ids = mongo.db.mapping.find_one({"_id":username})['Classes']
            results = mongo.db.mapping.delete_one({"_id": username})
            results = mongo.db.classes.find({"user": username})
            for result in results:
                data = mongo.db.classes.delete_one({"_id": result['_id']})
            mongo.db.ids.update({"_id": 0}, {"$pull": {"names": username}})
            for tag in ids.keys():
                mongo.db.ids.update({"_id": 0}, {"$pull": {"ids": tag}})
            mongo.db.users.delete_one({"_id": userid})
            return 202
        except Exception as e:
            print(e, flush=True)
            return str(e)
        return 200

class deleteClass(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user', required=True)
        parser.add_argument('className', required=True)
        args = parser.parse_args()
        return self.deleteClass(args['user'], args['className'])

    def deleteClass(self, username, className): # Delete a specific class from a user
        try:
            ids = mongo.db.mapping.find_one({"_id":username})['Classes']
            for tag in ids.keys():
                if ids.get(tag) == className:
                    targetId = tag
                    break
            mongo.db.mapping.update({"_id": username}, {"$unset": {"Classes." + str(targetId): ""}})
            results = mongo.db.classes.delete_one({"_id": targetId})
            mongo.db.ids.update({"_id": 0}, {"$pull": {"ids": targetId}})
        except Exception as e:
            return str(e)
        return 200

class pollStatus(Resource):     # Return or update the status of a poll given user and class data
    def get(self, user, className):
        try:
            targetId = self.getID(user, className)
            return str(mongo.db.classes.find_one({"_id": targetId})['status'])
        except Exception as e:
            return e

    def post(self, user, className):        # Update the status of the poll
        parser = reqparse.RequestParser()
        parser.add_argument('status', required=True)
        args = parser.parse_args()
        try:
            targetId = self.getID(user, className)
            mongo.db.classes.update({"_id": targetId}, {"$set": {"status": bool(args['status'] == "true")}})
            return mongo.db.classes.find_one({"_id": targetId})['status']
        except Exception as e:
            return str(e)

    def getID(self, user, className):       # Get the ID of a specific class
        ids = mongo.db.mapping.find_one({"_id":user})['Classes']
        targetId = None
        for tag in ids.keys():
            if ids.get(tag) == className:
                targetId = tag
                break
        return targetId

class answer(Resource):     # Answer a given poll if it is open
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('client', required=True)
        parser.add_argument('user', required=True)
        parser.add_argument('className', required=True)
        parser.add_argument('answer', required=True)
        args = parser.parse_args()
        targetId = pollStatus.getID(self, args['user'], args['className'])
        if mongo.db.classes.find_one({"_id": targetId})['status']:
            if args['client'] not in mongo.db.classes.find_one({"_id": targetId})['answers'].keys():
                mongo.db.classes.update_one({"_id": targetId}, {"$set": {"answers." + args['client']: args['answer']}})
                return 200
            return "name taken"
        return "not open"

class report(Resource):     # Return a dictionary of the answers collected
    def get(self, user, className):
        targetId = pollStatus.getID(self, user, className)
        try:
            classData = mongo.db.classes.find_one({"_id": targetId})
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
api.add_resource(verifyUser, '/validate/tokensignin/<string:idtoken>')
api.add_resource(registerUser, '/registerUser')