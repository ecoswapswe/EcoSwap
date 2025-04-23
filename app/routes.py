from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
import os
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import  secure_filename
from app.userModel import User, user_collection, listings_collection, trades_collection
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
            or search_query in p.get("location", "").lower() # atemot to ad location search functionality as well 
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
    # you can also auto‑stamp:
    date_posted = datetime.utcnow()

    file = request.files.get("image_file")
    if file and file.filename:
        # ensure our upload folder exists
        upload_dir = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        # secure and save
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        # build the public URL for Mongo
        image_link = url_for("static", filename=f"uploads/{filename}")
    else:
        # fallback to any pasted URL (could be empty)
        image_link = request.form.get("image_link", "").strip()

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

#----------- SWAP LISTINGS ------------------

@routes_blueprint.route("/swap/<listing_id>", methods=["GET", "POST"])
@login_required
def swap_listing(listing_id):
    # 1) fetch the other user’s listing
    listing = listings_collection.find_one({"_id": ObjectId(listing_id)})
    # 2) fetch current_user’s own listings
    user_doc  = user_collection.find_one({"_id": ObjectId(current_user.get_id())})
    my_listings = user_doc.get("listings", [])

    if request.method == "POST":
        mine_id = request.form["my_listing_id"]
        # 3) insert a trade proposal
        trades_collection.insert_one({
          "from_user_id":   ObjectId(current_user.get_id()),
          "to_user_id":     listing["user_id"],
          "from_listing":   ObjectId(mine_id),
          "to_listing":     ObjectId(listing_id),
          "status":         "pending",
          "date_proposed":  datetime.utcnow()
        })
        flash("Swap proposal sent!", "success")
        return redirect(url_for("routes.pending_trades"))

    return render_template("swap_listing.html",
                           listing=listing,
                           my_listings=my_listings)

# ---------- PENDING SWAPS ----------

@routes_blueprint.route("/pending_trades")
@login_required
def pending_trades():
    uid = ObjectId(current_user.get_id())

    # Build a list of incoming proposals, with usernames + titles
    incoming = []
    for t in trades_collection.find({"to_user_id": uid, "status": "pending"}):
        sender      = user_collection.find_one({"_id": t["from_user_id"]})
        listing_from = listings_collection.find_one({"_id": t["from_listing"]})
        listing_to   = listings_collection.find_one({"_id": t["to_listing"]})
        if not sender or not listing_from or not listing_to:
            continue
        incoming.append({
            "_id":           t["_id"],
            "from_username": sender["username"],
            "from_title":    listing_from["title"],
            "to_title":      listing_to["title"],
            "status":        t["status"]
        })

    # Build a list of all proposals you’ve made, with titles + status
    outgoing = []
    for t in trades_collection.find({"from_user_id": uid}):
        receiver = user_collection.find_one({"_id": t["to_user_id"]})
        listing_from = listings_collection.find_one({"_id": t["from_listing"]})
        listing_to   = listings_collection.find_one({"_id": t["to_listing"]})
        if not listing_from or not listing_to:
            continue
        
        outgoing.append({
            "_id":        t["_id"],
            "from_title": listing_from["title"],
            "to_title":   listing_to["title"],
            "to_username": receiver["username"],
            "status":     t["status"]
        })

    return render_template(
        "pending_trades.html",
        incoming=incoming,
        outgoing=outgoing
    )

@routes_blueprint.route("/trade/<trade_id>/<action>", methods=["POST"])
@login_required
def respond_trade(trade_id, action):
    # look up the trade
    trade = trades_collection.find_one({"_id": ObjectId(trade_id)})
    if not trade:
        abort(404)

    # only the recipient may respond
    if trade["to_user_id"] != ObjectId(current_user.get_id()):
        abort(403)

    # set new status
    new_status = "accepted" if action == "accept" else "declined"
    trades_collection.update_one(
        {"_id": ObjectId(trade_id)},
        {"$set": {
            "status":         new_status,
            "date_responded": datetime.utcnow()
        }}
    )
    flash(f"Trade {new_status}.", "info")
    return redirect(url_for("routes.pending_trades"))



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

    # 3) CASCADE: remove any pending trades involving this listing
    trades_collection.delete_many({
        "$or": [
            {"proposer_listing_id": list_oid},
            {"receiver_listing_id": list_oid}
        ]
    })

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
