from datetime import datetime

import pymongo
from bson import ObjectId
from flask import Flask, render_template, request, current_app, g, redirect, session, jsonify

import ssl
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi


ca = certifi.where()
uri = "mongodb+srv://adminuser2:adminuser2@softwareengineeringcoin.8oragfn.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, tls=True, tlsCAFile=ca)
db = client['account']
collection = db['account']
collectionMarketplace = db ['marketplace']
collectionPosts = db['posts']

"""
def get_db():
   
   Configuration method to return db instance
   
   db = getattr(g, "_database", None)

   if db is None:
      db = g._database = PyMongo(current_app).db

   return db

# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)
"""

app = Flask(__name__)
app.secret_key = 'software_engineering'

@app.route('/')
def index():
   userid=session.get('username',None)
   if 'username' in session: 
       return render_template('index.html', currentCoinPrice =  collection.find_one({'username': 'marketplace'})['coins'], currentCoinAmount = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])['pricePerCoin'], userid=session['username'])
   else:
      return render_template('index.html', currentCoinPrice =  collection.find_one({'username': 'marketplace'})['coins'], currentCoinAmount = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])['pricePerCoin'])

@app.route('/login', methods = ['POST', 'GET'])
def login():
   if request.method =='GET':
      return render_template('login.html')
   elif request.method=='POST':
      val = request.form
      results = collection.find({"$and":[{"username":val["username"]}, {"password": val['password']}]})
      for result in results:
         if result:
            session['username'] = val['username']
            return redirect('/')
      return render_template('login.html')
   

@app.route('/signup', methods = ['POST', 'GET'])
def signup():
   if request.method == 'POST':
      post={}
      val = request.form
      results = collection.find({"username":val["username"]})
      for result in results:
         if result:
            return render_template('signup.html', alert = True)
      for key, value in val.items():
         post[key] = value
      post['balance'] = 0
      post['coins'] = 0
      collection.insert_one(post)
      return redirect('/')
   else:
      return render_template('signup.html')

@app.route('/logout')
def logout():
   session.pop('username', None)
   return redirect('/')


@app.route('/user', methods = ['POST', 'GET'])
def user():
   results = collection.find({"username":session["username"]})
   myquery = { "username": session['username'] }
   bal = 0
   if request.method == 'POST':
      val = request.form
      results = collection.find({"username":session["username"]})
      print(val)

      if val['account'] == 'depo':
         newvalues = {'$inc': {'balance': int(val['balance'])}}
      elif val['account'] == 'withdraw':
         newvalues = {'$inc': {'balance': -1 * int(val['balance'])}}

      collection.update_one(myquery, newvalues)
      for result in results:
         if result:
            username = result['username']
            email = result['email']
            bal = result['balance']
            co = result['coins']
      return render_template('user.html', username = username, email = email,  bal = bal, co = co)
   else:
      for result in results:
         if result:
            username = result['username']
            email = result['email']
            bal = result['balance']
            co = result['coins']
      return render_template('user.html', username = username, email = email,  bal = bal, co = co)

@app.route('/marketplace', methods = ['POST', 'GET'])
def marketplace():
   results = collection.find_one({"username":session["username"]})
   resultsMarketplace = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])
   remainingCoins = collection.find_one({"username":'marketplace'})
   val = request.form
   if results:
      bal = results['balance']
      co = results['coins']
      username = results['username']
      email = results['email']
      resultsMarketplace = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])
      coinsMarketplace = remainingCoins['coins']
      price = resultsMarketplace['pricePerCoin']
   if request.method == 'POST':
      if 'buyCoins' in request.form:
         if int(val['buyfromwebsite']) > int(remainingCoins['coins']):
            return render_template('marketplace.html',username = username, email = email, bal = bal, co = co, coins = coinsMarketplace, price = price, alert=True)
         elif int(results['balance']) < int(val['buyfromwebsite']) * int(resultsMarketplace['pricePerCoin']):
            return render_template('marketplace.html',username = username, email = email, bal = bal, co = co, coins = coinsMarketplace, price = price, alert=True)
         # Update User Coins
         filter = {"username":session["username"]}
         update = {"$set": {"coins": results['coins'] +  int(val['buyfromwebsite'])}}
         re = collection.update_one(filter, update)
         # Update User Balance
         update = {"$set": {"balance": int(results['balance']) - (int(val['buyfromwebsite']) * int(resultsMarketplace['pricePerCoin'])) }}
         re = collection.update_one(filter, update)

         # Update Marketplace Coins
         filter = {"username":'marketplace'}
         update = {"$set": {"coins": int(remainingCoins['coins']) - int(val['buyfromwebsite'])  }}
         re = collection.update_one(filter, update)
         results = collection.find_one({"username": session["username"]})
         if results:
            bal = results['balance']
            co = results['coins']
   resultsMarketplace = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])
   remainingCoins = collection.find_one({"username": 'marketplace'})
   coinsMarketplace = remainingCoins['coins']
   price = resultsMarketplace['pricePerCoin']
   return render_template('marketplace.html', username = username, email = email,  bal = bal, co = co, coins = coinsMarketplace, price = price)

@app.route('/posts', methods = ['POST', 'GET'])
def posts():
   results = collection.find_one({"username":session["username"]})
   resultsMarketplace = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])
   val = request.form

   # add all info to the site
   bal = results['balance']
   co = results['coins']
   username = results['username']
   email = results['email']
   coinsMarketplace = collection.find_one({"username": 'marketplace'})['coins']
   price = resultsMarketplace['pricePerCoin']
   documents = list(collectionPosts.find())
   if request.method == 'POST':
      # make a post
      if 'offerCoins' in request.form:
         # Error Handling
         # checks if user doesn't offer to many coins
         resultyPosts = collectionPosts.find({'user': session["username"] })
         remainingCoins = results['coins']
         for result in resultyPosts:
            remainingCoins -= int(result['amountOfCoins'])
         if remainingCoins < int(val['AmountSelling']):
            return render_template('post.html', username=username, email=email, bal=bal, co=co, coins=coinsMarketplace,
                                   price=price, documents=documents, alert = True)
         # End Error Handling
         post = {"pricePerCoin": val['PriceSelling'], "amountOfCoins": val['AmountSelling'], "user": session["username"], "createdAt": datetime.now()}
         collectionPosts.insert_one(post)
      # buys coins
      elif 'buyPost' in request.form:
         data = collectionPosts.find_one({"_id": ObjectId(val["buyPost"])} )
         # Error Handling
         # Not enough Money
         if bal < int(data['amountOfCoins']) * int(data['pricePerCoin']):
            return render_template('post.html', username=username, email=email, bal=bal, co=co, coins=coinsMarketplace,
                                   price=price, documents=documents, alert=True)
         # End Error handling
         # Update Buyer Coins
         filter = {"username":session["username"]}
         update = {"$set": {"coins": int(data['amountOfCoins']) + int(results['coins'])}}
         re = collection.update_one(filter, update)
         # Update Buyer Balance
         update = {"$set": {"balance": int(results['balance']) - (int(data['amountOfCoins']) * int(data['pricePerCoin']))}}
         re = collection.update_one(filter, update)
         # Update Seller Coins
         filter = {"username": data['user']}
         update = {"$set": {"coins": int(results['coins']) - int(data['amountOfCoins'])}}
         re = collection.update_one(filter, update)
         # Update Seller Balance
         update = {"$set": {"balance": int(results['balance']) + (int(data['amountOfCoins']) * int(data['pricePerCoin']))}}
         re = collection.update_one(filter, update)
         # Update Price
         post = {"pricePerCoin": data['pricePerCoin'], "createdAt": datetime.now()}
         collectionMarketplace.insert_one(post)
         # delete the Post
         collectionPosts.delete_one({"_id": ObjectId(val["buyPost"])})
   # Retrieve all documents from the collection
   results = collection.find_one({"username": session["username"]})
   resultsMarketplace = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])
   val = request.form

   # add all info to the site
   bal = results['balance']
   co = results['coins']
   username = results['username']
   email = results['email']
   coinsMarketplace = collection.find_one({"username": 'marketplace'})['coins']
   price = resultsMarketplace['pricePerCoin']
   documents = list(collectionPosts.find())
   documents = list(collectionPosts.find())
   return render_template('post.html', username = username, email = email,  bal = bal, co = co, coins = coinsMarketplace, price = price, documents=documents)



if __name__ == '__main__':
   app.run(debug = True)


