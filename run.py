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


@app.route('/marketplace', methods=['POST', 'GET'])
def marketplace():
   username = session.get("username")
   if not username:
      return redirect('./login')
   if request.method == 'POST':
      if 'buyCoins' in request.form:
         return buy_coins(username)
      elif 'offerCoins' in request.form:
         return offer_coins(username)
      elif 'buyPost' in request.form:
         return buy_post(username)
   return render_marketplace(username)

def buy_post(username):
   val = request.form
   post = collectionPosts.find_one({"_id": ObjectId(val["buyPost"])})
   user = collection.find_one({"username": username})
   bal = user['balance']
   co = user['coins']
   username = user['username']
   email = user['email']
   price = post['pricePerCoin']
   coinsMarketplace = collection.find_one({"username": "marketplace"})['coins']
   documents = list(collectionPosts.find())
   if bal < int(post['amountOfCoins']) * int(post['pricePerCoin']):
      return render_template('marketplace.html', username=username, email=email, bal=bal, co=co, coins=coinsMarketplace,
                             alert='balance', price=price, documents=documents)
   buyer_filter = {"username": session["username"]}
   seller_filter = {"username": post['user']}
   amount_of_coins = int(post['amountOfCoins'])
   amount_to_deduct = amount_of_coins * int(post['pricePerCoin'])

   # Update Buyer Coins
   collection.update_one(buyer_filter, {"$inc": {"coins": amount_of_coins}})
   # Update Buyer Balance
   collection.update_one(buyer_filter, {"$inc": {"balance": -amount_to_deduct}})
   # Update Seller Coins
   collection.update_one(seller_filter, {"$inc": {"coins": -amount_of_coins}})
   # Update Seller Balance
   collection.update_one(seller_filter, {"$inc": {"balance": amount_to_deduct}})
   # Update Price
   collectionMarketplace.insert_one({"pricePerCoin": post['pricePerCoin'], "createdAt": datetime.now()})
   # Delete the Post
   collectionPosts.delete_one({"_id": ObjectId(val["buyPost"])})
   return render_marketplace(username)

def offer_coins(username):
   coinsMarketplace = collection.find_one({"username": "marketplace"})['coins']
   user = collection.find_one({"username": username})
   bal = user['balance']
   co = user['coins']
   username = user['username']
   email = user['email']
   remainingCoins = user['coins'] - sum(int(result['amountOfCoins']) for result in collectionPosts.find({'user': session["username"]}))
   val = request.form
   if remainingCoins < int(val['AmountSelling']):
      return render_template('marketplace.html', username=username, email=email, bal=bal, co=co, coins=coinsMarketplace,
                             alert='coinsLeft', price=val['PriceSelling'])
   post = {"pricePerCoin": val['PriceSelling'], "amountOfCoins": val['AmountSelling'], "user": session["username"],
           "createdAt": datetime.now()}
   collectionPosts.insert_one(post)
   return render_marketplace(username)

def buy_coins(username):
   user = collection.find_one({"username": username})
   marketplace = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])
   remainingCoins = collection.find_one({"username": "marketplace"})
   documents = list(collectionPosts.find())
   buyCoins = int(request.form['buyfromwebsite'])
   coinsMarketplace = remainingCoins['coins']
   price = marketplace['pricePerCoin']

   if buyCoins > coinsMarketplace:
      return render_template('marketplace.html', username=username, alert='coinsMarketplace', bal = user['balance'], co = user['coins'],
                             coins=coinsMarketplace, documents=documents, price=price)
   elif user['balance'] < buyCoins * price:
      return render_template('marketplace.html', username=username, alert='balance', bal = user['balance'], co = user['coins'], coins=coinsMarketplace,
                             documents=documents, price=price)

   # Update User Coins
   collection.update_one({"username": username}, {"$inc": {"coins": buyCoins}})
   # Update User Balance
   collection.update_one({"username": username}, {"$inc": {"balance": -buyCoins * price}})
   # Update Marketplace Coins
   collection.update_one({"username": "marketplace"}, {"$inc": {"coins": -buyCoins}})
   user['coins'] += buyCoins
   user['balance'] -= buyCoins * price
   return render_marketplace(username)

def render_marketplace(username):
   user = collection.find_one({"username": username})
   marketplace = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])
   remainingCoins = collection.find_one({"username": "marketplace"})
   documents = list(collectionPosts.find())
   return render_template('marketplace.html', username=username, documents=documents, bal = user['balance'], co = user['coins'],
                          coins=remainingCoins['coins'], price=marketplace['pricePerCoin'])

if __name__ == '__main__':
   app.run(debug = True)


