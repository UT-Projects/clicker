import pymongo
from pymongo import MongoClient
import string
import random

def randomStringDigits(length):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(length))

client = pymongo.MongoClient("mongodb+srv://db:db@clicker-ancot.mongodb.net/test?retryWrites=true&w=majority")
db = client['clicker'] 
collection = db['mapping']

# collection.insert_one({"_id":0, "name": "documenting class ids", "ids":[0]})
while True:
    name = "john"
    result = collection.find({"name": name})
    print(result)