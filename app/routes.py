from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.userModel import User, user_collection, listings_collection
from bson import ObjectId
from datetime import datetime

routes_blueprint = Blueprint("routes", __name__, template_folder="templates")


# ---------- LOGIN ROUTE ----------
@routes_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("routes.landing_page"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user_data = user_collection.find_one({"email": email})
        if user_data and check_password_hash(user_data["password"], password):
            user = User(user_data["_id"], user_data["username"], user_data["password"])
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("routes.landing_page"))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template("login.html")


# ---------- REGISTER ROUTE ----------
@routes_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("routes.landing_page"))

    if request.method == "POST":
        username = request.form["username"].strip()
        email    = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm  = request.form["confirm_password"]

        # 1) Password match?
        if password != confirm:
            flash("Passwords do not match.", "warning")
            return redirect(url_for("routes.register"))

        # 2) Unique username?
        if user_collection.find_one({"username": username}):
            flash("Username already taken.", "warning")
            return redirect(url_for("routes.register"))

        # 3) Unique email?
        if user_collection.find_one({"email": email}):
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("routes.login"))

        # 4) All clear: create user
        hashed = generate_password_hash(password)
        user_collection.insert_one({
            "username": username,
            "email":    email,
            "password": hashed,
            "listings": []
        })

        flash("Account created! You can now log in.", "success")
        return redirect(url_for("routes.login"))

    return render_template("register.html")

# ---------- LANDING PAGE (requires login) ----------
@routes_blueprint.route("/landing")
@login_required
def landing_page():
    search_query = request.args.get("search", "").strip().lower()

    # pull every document from listings, then coerce user_id to str
    raw = list(listings_collection.find({}))
    products = []
    for l in raw:
        l["user_id"] = str(l.get("user_id", ""))
        products.append(l)

    # optional title filter
    if search_query:
        products = [
            p for p in products
            if search_query in p.get("title", "").lower()
        ]

    return render_template(
        "index.html",
        products=products,
        search_query=search_query
    )

# ---------- ADD LISTING ----------
@routes_blueprint.route("/add_listing", methods=["GET","POST"])
@login_required
def add_listing():
    if request.method == "GET":
        # render a form template to post a new listing
        return render_template("add_listing.html")

    # 1) Gather form data
    title       = request.form["title"]
    description = request.form["description"]
    category    = request.form["category"]
    condition   = request.form["condition"]
    location    = request.form["location"]
    image_link  = request.form["image_link"]
    # you can also auto‑stamp:
    date_posted = datetime.utcnow()

    # 2) Build your new listing document
    new_listing = {
        "title":       title,
        "description": description,
        "category":    category,
        "condition":   condition,
        "location":    location,
        "image_link":  image_link,
        "date_posted": date_posted,
        "user_id":     ObjectId(current_user.get_id()),
        "username":    current_user.username
    }

    # 3a) Insert into the top‑level listings collection
    result = listings_collection.insert_one(new_listing)
    listing_id = result.inserted_id

    # 3b) Also push a (lighter) copy into the user’s own document
    user_collection.update_one(
        {"_id": ObjectId(current_user.get_id())},
        {"$push": {"listings": {
            "_id":         listing_id,
            "title":       title,
            "description": description,
            "image_link":  image_link,
            "date_posted": date_posted
        }}}
    )

    flash("Listing added successfully!", "success")
    return redirect(url_for("routes.landing_page"))

#-----------MY LISTINGS------------------

@routes_blueprint.route("/my_listings")
@login_required
def my_listings():
    # Fetch the user's own document:
    user_doc = user_collection.find_one({
        "_id": ObjectId(current_user.get_id())
    })
    # Get their array of listings (or empty list)
    listings = user_doc.get("listings", [])
    return render_template("my_listings.html", listings=listings)

#-----------DELETE LISTINGS------------------
from flask import jsonify
from bson import ObjectId

@routes_blueprint.route("/delete_listing/<listing_id>", methods=["POST"])
@login_required
def delete_listing(listing_id):
    user_oid = ObjectId(current_user.get_id())
    list_oid = ObjectId(listing_id)

    # 1) Remove from global listings
    listings_collection.delete_one({"_id": list_oid})

    # 2) Pull it from the user’s listings array
    user_collection.update_one(
        {"_id": user_oid},
        {"$pull": {"listings": {"_id": list_oid}}}
    )

    return jsonify({"status": "ok"}), 200


# ---------- LOGOUT ----------
@routes_blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("routes.login"))



@routes_blueprint.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("routes.landing_page"))
    return redirect(url_for("routes.login"))
