import uuid
from pymongo import MongoClient
import logging


class UsersDb:
    def __init__(self, mongo_uri, mongo_database):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[mongo_database]
        self.users_collection = self.db["users"]

    def user_exists(self, user_id):
        return self.users_collection.find_one({"_id": user_id}) is not None

    def create_user(self, user_id, user_language='en'):
        user_data = {
            "_id": user_id,
            "balance": 0,
            "referral_code": self.generate_referral_code(),
            "amount_of_referrals": 0,
            "gold_per_pillage": 100,
            "last_time_pillage_claimed": None,
            "last_time_daily_quest_completed": None,
            "user_language": user_language,
            "subscribe_channel_quest_time": None,
            "start_another_bot_quest_time": None,
            "last_time_twitter_link_clicked": None,
        }
        self.users_collection.insert_one(user_data)

    @staticmethod
    def generate_referral_code():
        # Replace with your referral logic (consider MongoDB for uniqueness)
        unique_id = str(uuid.uuid4())  # Example using UUID
        referral_code = unique_id
        return referral_code

    def get_user_data(self, user_id):
        user_data = self.users_collection.find_one({"_id": user_id})
        return user_data if user_data else {}

    def update_user_data(self, user_id, update_data):
        self.users_collection.update_one({"_id": user_id}, {"$set": update_data})

    def increase_referrals_number(self, user_id):
        # Find the user document
        user = self.users_collection.find_one({"_id": user_id})
        if user:
            # Increment the amount_of_referrals field by 1
            self.users_collection.update_one({"_id": user_id}, {"$inc": {"amount_of_referrals": 1}})
        else:
            logging.error("User not found.")

    def get_common_data(self):
        system_config = self.users_collection.find_one({"_id": 0})
        return system_config

    def update_common_data(self, update_data):
        self.users_collection.update_one({"_id": 0}, {"$set": update_data}, upsert=True)
