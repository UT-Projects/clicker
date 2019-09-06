import pymongo
from pymongo import MongoClient

client = MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
db = client['clicker'] 
collection = db['clicker']

post = {"_id": "fkdslarel324k32", "type": "class", "code": "fdkasfs", "status": False}
collection.insert_one(post)