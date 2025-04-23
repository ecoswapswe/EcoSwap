
from flask import Flask, render_template, request, g
from flask_login import LoginManager
import firebase_admin
from firebase_admin import credentials
from config import settings
from app.userModel import User
from bson import ObjectId
from app.routes import routes_blueprint
from pymongo import MongoClient  # Import MongoClient

app = Flask(__name__)
app.config["MONGO_URI"] = settings.MONGO_URI 
app.secret_key = settings.SECRET_KEY

# Set up MongoDB with MongoClient
client = MongoClient("mongodb+srv://aditya8mal:5H9LQHZqYl33mYlu@ecoswap.rodew.mongodb.net/")
db = client["ecoswap"]
user_collection = db["users"]

# Set up Firebase
cred = credentials.Certificate(settings.FIREBASE_CREDENTIAL_PATH)
firebase_admin.initialize_app(cred)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = "routes.login"
login_manager.init_app(app)

app.register_blueprint(routes_blueprint)

@login_manager.user_loader
def load_user(user_id):
    user_doc = user_collection.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        return None
    return User(
        user_doc["_id"],
        user_doc["username"],    # ← pull the username
        user_doc["password"]
    )


@app.before_request
def before_request():
    g.user_collection = user_collection  # Store MongoDB collection in g


# **Updated Home Route: Fetch Listings from Users**
@app.route('/')
def home():
    search_query = request.args.get('search', '').strip()

    # Use `$unwind` to get all listings from all users
    pipeline = [
        {"$unwind": "$listings"},  # Extract listings from each user
        {"$replaceRoot": {"newRoot": "$listings"}}  # Convert listings into top-level results
    ]

    if search_query:
        pipeline.append({
             "$match": {
                "$or": [
                    {"title": {"$regex": search_query, "$options": "i"}},
                    {"location": {"$regex": search_query, "$options": "i"}}
                ]
            }
        })

    listings = list(user_collection.aggregate(pipeline))

    return render_template('index.html', products=listings, search_query=search_query)


# **Route to Add a New Listing to a User**
@app.route('/add_listing', methods=['POST'])
def add_listing():
    if not request.form.get("user_id"):
        return "User ID required", 400

    user_id = ObjectId(request.form["user_id"])
    new_listing = {
        "title": request.form["title"],
        "description": request.form["description"],
        "category": request.form["category"],
        "condition": request.form["condition"],
        "location": request.form["location"],
        "image_link": request.form["image_link"],
        "date_posted": request.form["date_posted"],
        "price": float(request.form["price"])
    }

    user_collection.update_one(
        {"_id": user_id},
        {"$push": {"listings": new_listing}}
    )

    return "Listing added successfully!", 200
