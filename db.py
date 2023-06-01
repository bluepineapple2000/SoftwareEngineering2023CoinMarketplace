# this is just a test file
# nothing important here

import ssl
from datetime import datetime

import certifi
import pymongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi

ca = certifi.where()
uri = "mongodb+srv://adminuser2:adminuser2@softwareengineeringcoin.8oragfn.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, tls=True, tlsCAFile=ca)

db = client['account']
collection = db['posts']

post = {"pricePerCoin": 110, "amountOfCoins": 4, "user": "qwe", "createdAt": datetime.now()}

collection.insert_one(post)

results = collection.find()

#results = collection.find().sort({'_id':-1}).limit(1)
for results in results:
    print(results)

