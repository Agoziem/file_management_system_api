import firebase_admin
from firebase_admin import credentials
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, "firebase_credentials.json")
cred = credentials.Certificate(path)
firebase_admin.initialize_app(cred)
