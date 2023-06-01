from datetime import datetime

import pymongo
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
def indexpage():
   userid=session.get('username',None)
   if 'username' in session: 
       return render_template('index.html', userid=session['username'])
   else:
      return render_template('index.html')

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
   val = request.form

   if request.method == 'POST':
      if 'buyCoins' in request.form:
         # Update User Coins
         filter = {"username":session["username"]}
         update = {"$set": {"coins": results['coins'] +  int(val['buyfromwebsite'])}}
         re = collection.update_one(filter, update)
         # Update User Balance
         if int(results['balance']) < int(val['buyfromwebsite']) * int(resultsMarketplace['pricePerCoin']):
            return render_template('signup.html', alert=True)
         update = {"$set": {"balance": int(results['balance']) - (int(val['buyfromwebsite']) * int(resultsMarketplace['pricePerCoin'])) }}
         re = collection.update_one(filter, update)

         # Update Marketplace Coins
         if int(val['buyfromwebsite']) > int(resultsMarketplace['RemainingCoins']):
            return render_template('signup.html', alert=True)
         post = {"pricePerCoin": resultsMarketplace['pricePerCoin'], "RemainingCoins": int(resultsMarketplace['RemainingCoins']) - int(val['buyfromwebsite']) , "createdAt": datetime.now()}
         collectionMarketplace.insert_one(post)

         results = collection.find_one({"username": session["username"]})
         if results:
            bal = results['balance']
            co = results['coins']
   else:
      if results:
         bal = results['balance']
         co = results['coins']
   if results:
      username = results['username']
      email = results['email']
   resultsMarketplace = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])
   coinsMarketplace = resultsMarketplace['RemainingCoins']
   price = resultsMarketplace['pricePerCoin']
   return render_template('marketplace.html', username = username, email = email,  bal = bal, co = co, coins = coinsMarketplace, price = price)




if __name__ == '__main__':
   app.run(debug = True)


