from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access environment variables
MONGODB_URI = f"""{os.getenv("MONGO_URI")}/?retryWrites=true&w=majority"""
USERS_DATABASE = f"""{os.getenv("USERS_DATABASE")}"""
CONTENT_DATABASE = f"""{os.getenv("CONTENT_DATABASE")}"""
USERS_COLLECTION = f"""{os.getenv("USERS_COLLECTION")}"""
CONTENT_COLLECTION = f"""{os.getenv("CONTENT_COLLECTION")}"""

# Create a new client and connect to the server
primary_mongo_client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
users_db = primary_mongo_client[USERS_DATABASE]
content_db = primary_mongo_client[CONTENT_DATABASE]

# Define access to our collections
users_collection = users_db[USERS_COLLECTION]
content_collection = content_db[CONTENT_COLLECTION]
