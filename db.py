from pymongo import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://softwareengineeringcoin.8oragfn.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
client = MongoClient(uri,
                     tls=True,
                     tlsCertificateKeyFile='X509-cert-1187672352362768358.pem',
                     server_api=ServerApi('1'))

db = client['testDB']
collection = db['testCol']
doc_count = collection.count_documents({})

#post = {"_id":0, "name":"WoongSup", "score": 90}
post1 = {"name":"YeHyun", "score": 80}
post2 = {"name":"JiYoung", "score": 70}

#collection.insert_one(post)
collection.insert_many([post1,post2])

results = collection.find({"name":"JiYoung"})
for results in results:
    print(results)
