import os
from dotenv import load_dotenv

# Load from .env file if it exists
load_dotenv()

# MongoDB Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://aditya8mal:5H9LQHZqYl33mYlu@ecoswap.rodew.mongodb.net/")

# Firebase Config
FIREBASE_CREDENTIAL_PATH = os.getenv("FIREBASE_CREDENTIAL_PATH", "config/ecoswap-5af7e-firebase-adminsdk-fbsvc-077e2513af.json")

# Flask Config
SECRET_KEY = os.getenv("SECRET_KEY", "88c080b87d676d905047fa6c61e738f17f04ea45d3160a18")
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
