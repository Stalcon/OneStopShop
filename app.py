from datetime import datetime
from bson import ObjectId
import pymongo, random
from pymongo.server_api import ServerApi
from flask import Flask, redirect, render_template, request, flash, session
from passlib.hash import sha256_crypt 

app = Flask(__name__)
app.config["SECRET_KEY"] = "MJBULED ODSRW"

client = pymongo.MongoClient(
    "mongodb+srv://Stalcon:3rorLQbbs8YMCeQU@cluster0.szmcpfm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    server_api=ServerApi('1')
    )

db = client.one_stop_shop

def AddToCart(id, quantity, session_id):
    product = db.products.find_one({"_id": ObjectId(id)})
    product_to_add = {}
    product_to_add["name"] = product["product_name"]
    product_to_add["quantity"] = int(quantity)
    product_to_add["price"] = product["price"]
    db.cart.update_one({"_id": ObjectId(session_id)},
                       {"$addToSet": {"cart": product_to_add}})
    db.products.update_one({"_id": ObjectId(id)},
                           {"$inc": {"quantity": -1*int(quantity)}})

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        if "user_id" not in session: 
            result = db.cart.insert_one({"cart": []})
            session["user_id"] = str(result.inserted_id)
        cart_count = len(db.cart.find_one({"_id": ObjectId(session["user_id"])})["cart"])
        items = list(db.products.find())
        stores = list(db.accounts.find())
        return render_template("index.html", items = items, stores = stores, cart_count = cart_count)
    if request.method == "POST":
        print(request.form)
        if "register" in request.form:
            shop_name = request.form["ShopName"]
            owner_name = request.form["OwnerName"]
            email = request.form["Email"]
            phone_number = request.form["Phone"]
            password = request.form["Password"]
            user_info = db.accounts.find_one({"email":email})
            if user_info:
                flash("Cannot register account!! Email already in use!!")
            else:
                document = {}
                document["shop_name"] = shop_name
                document["owner_name"] = owner_name
                document["email"] = email
                document["phone_number"] = phone_number
                document["password"] = sha256_crypt.hash(password)
                db.accounts.insert_one(document)
                flash("Registration Sucessful")
        if "login" in request.form:
            email = request.form["Email"]
            password = request.form["Password"]
            user_info = db.accounts.find_one({"email":email})
            if user_info:
                if sha256_crypt.verify(password, user_info["password"]):
                    flash("Login Sucessful!!")
                    session["email"] = email
                    return redirect("/shophome")
            flash("Unsucessful Login!! Username or password incorrect!!")
        if "AddToCart" in request.form:
            AddToCart(request.form["id"], request.form["Quantity"], session["user_id"])
        return redirect("/")

@app.route("/shophome", methods=["GET", "POST"])
def shophome():
    if request.method == "GET":
        if "email" not in session:
            flash("You must login!!")
            return redirect("/")
        items = db.products.find()
        print(items)
        return render_template("shophome.html", session = session, items = items)
    if request.method == "POST":
        if "AddProduct" in request.form:
            name = request.form["ProductName"]
            description = request.form["Description"]
            price = request.form["Price"]
            quantity = request.form["Quantity"]
            image = request.form["Image"]
            document = {}
            document["product_name"] = name
            document["description"] = description
            document["price"] = float(price)
            document["quantity"] = int(quantity)
            document["image_url"] = image
            document["shop_email"] = session["email"]
            db.products.insert_one(document)
            flash("Product Added!")
        if "AddStock" in request.form:
            id = ObjectId(request.form["id"])
            stock = request.form["Quantity"]
            db.products.update_one({"_id":id}, {"$inc": {"quantity":int(stock)}})
            flash("Stock Added!")
        if "Logout" in request.form:
            del session["email"]
            return redirect("/")
        return redirect("/shophome")

@app.route("/shop/<email>", methods=["GET", "POST"])
def shop(email):
    if request.method == "GET":
        store = dict(db.accounts.find_one({"email":email}))
        store_name = store["shop_name"]
        items = list(db.products.find({"shop_email":email}))
        return render_template("shop.html", items=items, name=store_name)
    if request.method == "POST":
        if "AddToCart" in request.form:
            AddToCart(request.form["id"], request.form["Quantity"], session["user_id"])
        return redirect("/shop/"+email)

@app.route("/cart", methods=["GET", "POST"])
def cart():
    if request.method == "GET":
        cart = db.cart.find_one({"_id": ObjectId(session["user_id"])})["cart"]
        total = 0
        for item in cart:
            itemcost= item["price"]*item["quantity"]
            total += itemcost
        return render_template("cart.html", cart=cart, total_cost=total)
    if request.method == "POST":
        if "Checkout" in request.form:
            db.cart.update_one({"_id": ObjectId(session["user_id"])},
                               {"$set": {"cart": []}})
            del session["user_id"]
            flash("Checkout Sucessful")
            return redirect("/")
        return redirect("/cart")

app.run(debug=True)