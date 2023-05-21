import ssl
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi

ca = certifi.where()
uri = "mongodb+srv://adminuser2:adminuser2@softwareengineeringcoin.8oragfn.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, tls=True, tlsCAFile=ca)

db = client['account']
collection = db['account']
doc_count = collection.count_documents({})

#post = {"_id":0, "name":"WoongSup", "score": 90}
post = {"name":"qw2e", "score": 820}


collection.insert_one(post)

results = collection.find({"name":"qwe"})
for results in results:
    print(results)

