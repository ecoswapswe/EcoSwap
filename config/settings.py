import os
from dotenv import load_dotenv

# Load from .env file if present
load_dotenv()

# -------------------------------------------------------------------
# Base directory of the project (two levels up from this file)
# e.g. C:\ecoswap\config\settings.py → BASE_DIR = C:\ecoswap
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# -------------------------------------------------------------------
# MongoDB Atlas
# -------------------------------------------------------------------
# Replace <user> and <pass> with your own, or override via the MONGO_URI env var.
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://aditya8mal:5H9LQHZqYl33mYlu@ecoswap.rodew.mongodb.net/"
    "ecoswap?retryWrites=true&w=majority"
)

# -------------------------------------------------------------------
# Firebase Admin SDK service‑account key
# -------------------------------------------------------------------
# Default points at config/ecoswap-5af7e-*.json under the project root.
FIREBASE_CREDENTIAL_PATH = os.getenv(
    "FIREBASE_CREDENTIAL_PATH",
    os.path.join(BASE_DIR, "config", "ecoswap-5af7e-firebase-adminsdk-fbsvc-077e2513af.json")
)

# -------------------------------------------------------------------
# Flask settings
# -------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "88c080b87d676d905047fa6c61e738f17f04ea45d3160a18")
DEBUG      = os.getenv("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")

