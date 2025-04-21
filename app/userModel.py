import certifi
from pymongo import MongoClient
from flask_login import UserMixin
from config.settings import MONGO_URI

# -----------------------------------------------------------------------------
# Initialize MongoDB client with TLS/SSL using the certifi CA bundle:
# -----------------------------------------------------------------------------
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where()
)

db = client.get_database("ecoswap")
# -----------------------------------------------------------------------------
# Select your database and users collection
# -----------------------------------------------------------------------------
# If your URI includes "/ecoswap", then get_database() will pick that up.
# You can also do client.get_database("ecoswap") explicitly.
db = client.get_database()

user_collection     = db.users
user_collection.create_index("username", unique=True)
listings_collection = db.listings

# -----------------------------------------------------------------------------
# Flask‑Login user class
# -----------------------------------------------------------------------------
class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id       = str(user_id)
        self.username = username
        self.password = password

    def get_id(self):
        return self.id

# -----------------------------------------------------------------------------
# (Optional) helper functions for interacting with your users collection
# -----------------------------------------------------------------------------
def find_user_by_email(email):
    """Return the raw Mongo document for a given email, or None."""
    return user_collection.find_one({"email": email})

def create_user(email, password):
    """
    Insert a new user document (with plaintext or hashed password).
    Returns the inserted_id.
    """
    result = user_collection.insert_one({"email": email, "password": password})
    return result.inserted_id
