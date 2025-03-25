import firebase_admin
from firebase_admin import credentials

def init_firebase():
    cred = credentials.Certificate("config/ecoswap-5af7e-firebase-adminsdk-fbsvc-077e2513af.json")
    firebase_admin.initialize_app(cred)
