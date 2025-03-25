
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import current_user, login_required, login_user, logout_user
from app.userModel import User
from bson import ObjectId

routes_blueprint = Blueprint("routes", __name__, template_folder="templates")


# ---------- LOGIN ROUTE ----------
@routes_blueprint.route("/login", methods=["GET", "POST"])
def login():
    user_collection = g.user_collection  # Access MongoDB collection
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user_data = user_collection.find_one({"email": email})  

        if user_data and check_password_hash(user_data["password"], password):
            user = User(user_data["_id"], user_data["email"], user_data["password"])
            login_user(user)

            flash("Login successful!", "success")
            return redirect(url_for("routes.landing_page"))  
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template("login.html")  


# ---------- REGISTER ROUTE ----------
@routes_blueprint.route("/register", methods=["GET", "POST"])
def register():
    user_collection = g.user_collection  
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        #username = request.form["username"]  # Get username from form

        existing_user = user_collection.find_one({"email": email})

        if existing_user:
            flash("Account already exists. Please log in.", "warning")
            return redirect(url_for("routes.login"))

        hashed_password = generate_password_hash(password)  
        user_collection.insert_one({
            "email": email, 
            "password": hashed_password, 
            #"username": username, 
            "listings": []  # Initialize empty listings array
        })  
        
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("routes.login"))

    return render_template("register.html")


# ---------- LANDING PAGE ROUTE ----------
@routes_blueprint.route("/landing")
@login_required 
def landing_page():
    user_collection = g.user_collection  # Ensure we use MongoDB collection
    search_query = request.args.get('search', '').strip().lower()

    # Aggregation to fetch listings with user details
    listings = user_collection.aggregate([
        {"$unwind": "$listings"},
        {"$project": {
            "_id": 0,
            "title": "$listings.title",
            "description": "$listings.description",
            "category": "$listings.category",
            "condition": "$listings.condition",
            "location": "$listings.location",
            "image_link": "$listings.image_link",
            "date_posted": "$listings.date_posted",
            "posted_by": "$username"  # Add seller's username
        }}
    ])

    # Convert cursor to list & filter search results
    all_listings = list(listings)
    if search_query:
        all_listings = [l for l in all_listings if search_query in l["title"].lower()]

    return render_template('index.html', products=all_listings, search_query=search_query)


# ---------- ADD LISTING ROUTE ----------
@routes_blueprint.route("/add_listing", methods=["POST"])
@login_required
def add_listing():
    user_collection = g.user_collection  
    title = request.form["title"]
    description = request.form["description"]
    category = request.form["category"]
    condition = request.form["condition"]
    location = request.form["location"]
    image_link = request.form["image_link"]
    date_posted = request.form["date_posted"]

    # Create new listing object
    new_listing = {
        "title": title,
        "description": description,
        "category": category,
        "condition": condition,
        "location": location,
        "image_link": image_link,
        "date_posted": date_posted
    }

    # Add listing to the logged-in user's document
    user_collection.update_one(
        {"_id": ObjectId(current_user.get_id())},
        {"$push": {"listings": new_listing}}
    )

    flash("Listing added successfully!", "success")
    return redirect(url_for("routes.landing_page"))


# ---------- LOGOUT ROUTE ----------
@routes_blueprint.route("/logout")
@login_required 
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("routes.login"))  # Fixed redirect


# ---------- HOME PAGE ROUTE ----------
@routes_blueprint.route("/")
def home():
    return redirect(url_for("routes.login"))  # Redirect to login
