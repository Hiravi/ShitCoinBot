import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
INVITE_URL = os.getenv('INVITE_URL')
REFERRAL_BASE_URL = os.getenv('REFERRAL_BASE_URL')
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DATABASE = os.getenv('MONGO_DATABASE')

print(BOT_TOKEN, CHANNEL_ID, INVITE_URL, REFERRAL_BASE_URL, MONGO_URI, MONGO_DATABASE)



