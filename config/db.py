from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access environment variables
MONGODB_URI = f"""{os.getenv("MONGO_URI")}/?retryWrites=true&w=majority"""
DATABASE = f"""{os.getenv("MONGO_DATABASE")}"""
USERS_COLLECTION = f"""{os.getenv("MONGO_USERS_COLLECTION")}"""
TODO_COLLECTION = f"""{os.getenv("MONGO_TODO_COLLECTION")}"""

# Create a new client and connect to the server
client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
db = client[DATABASE]
todo_collection = db[TODO_COLLECTION]
users_collection = db[USERS_COLLECTION]
