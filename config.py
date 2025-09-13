import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
OWNER_ID = os.getenv("OWNER_ID")
