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

post = {"username": "marketplace", }


collection.insert_one(post)

# Retrieve the last entered document in the collection
last_document = collection.find_one(sort=[("$natural", pymongo.DESCENDING)])

# Print the last document
print(last_document)

results = collection.find({"pricePerCoin": 100},{ "RemainingCoins": 1, "createdAt": 2})

#results = collection.find().sort({'_id':-1}).limit(1)
for results in results:
    print(results)

