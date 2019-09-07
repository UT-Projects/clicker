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
mapping = db['mapping']

mapping.insert_one({"_id": 0, "classes": 0})