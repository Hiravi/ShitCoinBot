import time
from languages import LANGUAGES
import logging
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


def get_message_text(db, user_id, message_key, **kwargs):
    """
   Gets the message text in the user's preferred language, inserting provided kwargs into the string.

   Args:
       db: An instance of the UsersDb class.
       user_id: The ID of the user.
       message_key: The key of the message to retrieve from LANGUAGES.
       **kwargs: Keyword arguments to insert into the message string.

   Returns:
       The formatted message text in the user's language, or the default English message if not found.
   """

    user_data = db.get_user_data(user_id)
    user_language = user_data.get("user_language", "en")
    message_texts = LANGUAGES.get(user_language, {})

    message_text = message_texts.get(message_key, LANGUAGES["en"][message_key])

    formatted_message = message_text.format(**kwargs)

    return formatted_message


def get_button_name(db, user_id, button_key):
    """
    Gets the button name in the user's preferred language.

    Args:
        db: An instance of the UsersDb class.
        user_id: The ID of the user.
        button_key: The key of the button to retrieve from LANGUAGES.

    Returns:
        The button name in the user's language, or the default English button name if not found.
    """

    user_data = db.get_user_data(user_id)
    user_language = user_data.get("user_language", "en")
    button_texts = LANGUAGES.get(user_language, {})

    button_name = button_texts.get(button_key, LANGUAGES["en"].get(button_key, button_key))

    return button_name


def get_current_timestamp():
    return time.time()


def get_last_pillage_time(db, user_id):
    user_data = db.get_user_data(user_id)
    return user_data.get("last_time_pillage_claimed", 0)


def update_last_pillage_time(db, user_id, timestamp):
    """
    Updates the user's last pillage claim time in the database.

    Args:
        db: The database object used to interact with the data.
        user_id: The ID of the user to update.
        timestamp: The timestamp to set as the last pillage claim time.
    """
    db.update_user_data(user_id, {"last_time_pillage_claimed": timestamp})


def get_gold_per_pillage(user_data) -> int:
    if user_data is None:
        return 0
    return user_data.get("gold_per_pillage", 0)


def update_balance(db, user_id, amount):
    """
    Updates the user's balance in the database.

    Args:
      db: The database object to interact with.
      user_id: The ID of the user to update.
      amount: The amount to add or subtract from the user's balance.
    """
    # Retrieve current balance efficiently
    current_balance = db.get_user_data(user_id).get("balance", 0)
    new_balance = current_balance + amount
    db.update_user_data(user_id, {"balance": new_balance})
    return new_balance


def get_amount_of_referrals(db, user_id):
    user_data = db.get_user_data(user_id)
    return user_data.get("amount_of_referrals", 0)


# Function to check if user is subscribed to the channel (replace with actual verification logic)
def is_user_subscribed(user_id):
    # Replace with your channel verification logic (e.g., Telegram API, external service)
    return True  # Placeholder for now


def get_user_balance(db, user_id) -> int:
    user_data = db.get_user_data(user_id)

    if user_data is None:
        return 0
    return user_data.get("balance", 0)


def get_user_referral_code(db, user_id) -> str:
    user_data = db.get_user_data(user_id)

    if user_data is None:
        return ""
    return user_data.get("referral_code", "")


def get_user_amount_of_referrals(db, user_id) -> int:
    user_data = db.get_user_data(user_id)

    if user_data is None:
        return 0
    return user_data.get("amount_of_referrals", 0)


def get_user_language(db, user_id):
    user_data = db.get_user_data(user_id)
    return user_data.get("user_language", "en")


def claim_gold(db, user_id):
    user_data = db.get_user_data(user_id)
    gold_per_pillage = get_gold_per_pillage(user_data)

    try:
        # Check if last_time_quest_completed exists before subtracting
        if user_data.get('last_time_daily_quest_completed'):
            last_time_quest_completed = user_data.get('last_time_daily_quest_completed')
            current_time = datetime.now()
            time_difference = current_time - last_time_quest_completed

            if time_difference >= timedelta(hours=24):
                updated_balance = update_balance(db, user_id, gold_per_pillage * 2)
            else:
                updated_balance = update_balance(db, user_id, gold_per_pillage)
        else:
            # Handle the case where last_time_quest_completed is None
            updated_balance = update_balance(db, user_id, gold_per_pillage)

        if updated_balance is not None:
            logger.info(f"User {user_id} successfully claimed gold. New balance: {updated_balance}")
            return True
        else:
            logger.error(f"Failed to update balance for user {user_id}")
            return False
    except Exception as e:
        logger.exception(f"An error occurred while claiming gold for user {user_id}: {e}")
        return False


def find_user_by_referral_code(db, referral_code):
    user_data = db.users_collection.find_one({"referral_code": referral_code})
    if user_data:
        return user_data["_id"]
    else:
        return None


def increase_referral_number(db, master_id):
    db.increase_referrals_number(master_id)


def twitter_link_clicked(db, user_id):
    time.sleep(10)
    current_time = datetime.now()
    db.update_user_data(user_id, {"last_time_twitter_link_clicked": current_time})


def mark_daily_quest_completed(db, user_id):
    user_data = db.get_user_data(user_id)
    last_time_link_clicked = user_data.get("last_time_twitter_link_clicked")

    if last_time_link_clicked is not None:
        current_time = datetime.now()
        db.update_user_data(user_id, {"last_time_daily_quest_completed": current_time})
        return True
    else:
        return False


def get_latest_tweet_url(db):
    common_data = db.get_common_data()
    twitter_link = common_data["last_twitter_post_link"]

    return twitter_link


def count_reward_time(db, user_id):
    # Get the last pillage claim time as a datetime object
    last_pillage_timestamp = get_last_pillage_time(db, user_id)
    if last_pillage_timestamp is None:
        return "00:00:00"  # If there's no previous pillage, return 0 time remaining

    last_pillage_time = datetime.fromtimestamp(last_pillage_timestamp)

    # Get the current time
    current_time = datetime.now()

    # Calculate the time difference
    time_difference = current_time - last_pillage_time

    # Check if at least 4 hours have passed since the last pillage
    if time_difference >= timedelta(hours=4):
        return "00:00:00"  # If 4 or more hours have passed, return 0 time remaining

    # Calculate remaining time until next pillage
    remaining_time = timedelta(hours=4) - time_difference

    # Convert remaining seconds to integer
    remaining_seconds = int(remaining_time.total_seconds())

    # Calculate hours, minutes, and seconds
    hours, remainder = divmod(remaining_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the remaining time
    reward_time = "{:02}:{:02}:{:02}".format(hours, minutes, seconds)

    return reward_time


def change_user_language(db, user_id, language_code):
    # Check if the language code is valid.
    if language_code not in LANGUAGES:
        raise ValueError("Invalid language code.")

    db.update_user_data(user_id, {"user_language": language_code})

    # Return the success message.
    return {"message": "Language changed."}


def get_referral_reward(db, user_id):
    user_data = db.get_user_data(user_id)

    if user_data.get('last_time_daily_quest_completed'):
        last_time_quest_completed = user_data.get('last_time_daily_quest_completed')
        current_time = datetime.now()
        time_difference = current_time - last_time_quest_completed

        if time_difference >= timedelta(hours=24):
            updated_balance = update_balance(db, user_id, 1000)
        else:
            updated_balance = update_balance(db, user_id, 500)
    else:
        # Handle the case where last_time_quest_completed is None
        logger.info(f"User {user_id} has no previous claim time. Granting base referral reward.")
        updated_balance = update_balance(db, user_id, 500)


def get_active_quests(db, user_id):
    user_data = db.get_user_data(user_id)
    common_data = db.get_common_data()
    current_time = datetime.now()
    active_quests = []

    daily_quest_completion_time = user_data.get('last_time_daily_quest_completed')

    if daily_quest_completion_time is None:
        active_quests.append('daily_quest_button')
    else:
        time_difference = current_time - daily_quest_completion_time
        if time_difference >= timedelta(hours=24):
            active_quests.append('daily_quest_button')

    if common_data and "quest_types" in common_data:
        for quest_type in common_data["quest_types"]:
            if quest_type["update_time"] is not None:
                if quest_type.get("type") == "subscribe_tg_channel":
                    subscribe_tg_channel_update_time = quest_type.get("update_time")
                    quest_completion_time = user_data.get('subscribe_channel_quest_time')

                    if quest_completion_time is None:
                        active_quests.append('subscribe_tg_channel_button')
                    else:
                        if quest_completion_time and subscribe_tg_channel_update_time:
                            if subscribe_tg_channel_update_time > quest_completion_time:
                                active_quests.append('subscribe_tg_channel_button')

                elif quest_type.get("type") == "start_another_bot":
                    start_another_bot_update_time = quest_type.get("update_time")
                    quest_completion_time = user_data.get('start_another_bot_quest_time')

                    if quest_completion_time is None:
                        active_quests.append('start_another_bot_button')
                    else:
                        if quest_completion_time and start_another_bot_update_time:
                            if start_another_bot_update_time > quest_completion_time:
                                active_quests.append('start_another_bot_button')

    return active_quests
