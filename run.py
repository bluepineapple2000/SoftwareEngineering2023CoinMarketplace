from datetime import datetime

import pymongo
from bson import ObjectId
from flask import Flask, render_template, request, current_app, g, redirect, session, jsonify, flash, send_file

import ssl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

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

app = Flask(__name__)
app.secret_key = 'software_engineering'
"""
def nocache(view):
  @wraps(view)
  def no_cache(*args, **kwargs):
    response = make_response(view(*args, **kwargs))
    response.headers['Last-Modified'] = datetime.now()
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response      
  return update_wrapper(no_cache, view)
"""
@app.route('/')
def index():
   userid=session.get('username',None)
   if 'username' in session: 
       return render_template('index.html', currentCoinAmount =  collection.find_one({'username': 'marketplace'})['coins'],
                               currentCoinPrice = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])['pricePerCoin'],
                                 userid=session['username'])
   else:
      return render_template('index.html', currentCoinAmount =  collection.find_one({'username': 'marketplace'})['coins'],
                              currentCoinPrice = collectionMarketplace.find_one(sort=[("$natural", pymongo.DESCENDING)])['pricePerCoin'])

@app.route('/fig')
def fig():
   priceList=[]
   timeList=[]
   for item in collectionMarketplace.find({}):
      priceList.append(int(item['pricePerCoin']))
      timeList.append(item['createdAt'].strftime("%B %d. %Hh"))
   x = range(0,len(priceList))
   print(timeList)
   size = [20]
   plt.figure(figsize=(12,4))
   plt.grid(True, color='#2A3459', axis='y', zorder=0)
   plt.gca().set_axisbelow(True)
   plt.plot(timeList, priceList, color='#FFFFFF', marker='.', zorder=1)
   plt.scatter(timeList[-1], priceList[-1], 50, color='r', marker='o', zorder=2)
   plt.gca().set_facecolor('#212946')
   #plt.gca().axes.xaxis.set_visible(False)
   plt.ylabel('Price per Coin')
   img = BytesIO()
   plt.savefig(img, format='png')
   img.seek(0)
   return send_file(img, mimetype='image/png')

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
   temps = collection.find({"username":session["username"]})
   myquery = { "username": session['username'] }
   bal = 0
   temp_bal = 0
   for temp in temps:
      if temp:
         temp_bal = temp['balance']
   if request.method == 'POST':
      val = request.form
      results = collection.find({"username":session["username"]})
      print(val)

      if val['account'] == 'depo':
         newvalues = {'$inc': {'balance': int(val['balance'])}}
         collection.update_one(myquery, newvalues)
      elif val['account'] == 'withdraw':
         if(int(val['balance'])>temp_bal):
            flash("DO NOT WITHDRAW MORE THAN YOU HAVE")
         else:
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
   price = int(marketplace['pricePerCoin'])

   if buyCoins > coinsMarketplace:
      return render_template('marketplace.html', username=username, alert='coinsMarketplace', bal = user['balance'], co = user['coins'],
                             coins=coinsMarketplace, documents=documents, price=price)
   elif int(user['balance']) < int(buyCoins) * price:
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


