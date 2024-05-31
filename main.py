import telebot
from utils import *
from db import UsersDb
import config
from datetime import datetime, timedelta
import logging.config
from logging_config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)

BOT_TOKEN = config.BOT_TOKEN

users_db = UsersDb(mongo_uri=config.MONGO_URI, mongo_database=config.MONGO_DATABASE, username=config.MONGO_USERNAME,
                   password=config.MONGO_PASSWORD, authSource=config.MONGO_AUTH_SOURCE)

bot = telebot.TeleBot(BOT_TOKEN)


def generate_main_keyboard(user_id):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)

    # Get translated button names based on the user's language
    pillage_btn = telebot.types.KeyboardButton(get_button_name(users_db, user_id, "pillage_button"))
    referrals_btn = telebot.types.KeyboardButton(get_button_name(users_db, user_id, "referrals_button"))
    balance_btn = telebot.types.KeyboardButton(get_button_name(users_db, user_id, "balance_button"))
    quests_btn = telebot.types.KeyboardButton(get_button_name(users_db, user_id, "quests_button"))
    language_btn = telebot.types.KeyboardButton(get_button_name(users_db, user_id, "language_button"))

    keyboard.add(pillage_btn, referrals_btn)
    keyboard.add(balance_btn, quests_btn)
    keyboard.add(language_btn)

    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id

    if not users_db.user_exists(user_id):
        user_language = message.from_user.language_code

        if user_language == 'ru':
            users_db.create_user(user_id, user_language)
        else:
            users_db.create_user(user_id)

        try:
            deeplink_args = message.text.split(" ")[1:]

            if len(deeplink_args) > 0:
                [referral_code] = deeplink_args
                master_id = find_user_by_referral_code(users_db, referral_code)

                increase_referral_number(users_db, master_id)

                get_referral_reward(users_db, master_id)

        except IndexError:
            # Unexpected error, handle gracefully
            bot.reply_to(message, "An error occurred processing your request.")

        new_user_message = get_message_text(db=users_db, message_key='new_user_message', user_id=user_id)

        initiation_button = telebot.types.InlineKeyboardButton(get_button_name(users_db, user_id, "initiation_button"),
                                                               callback_data="initiation")

        keyboard = telebot.types.InlineKeyboardMarkup().add(initiation_button)

        image_path = 'webp_images/welcome.webp'

        try:
            # Open the image file
            with open(image_path, 'rb') as image_file:
                # Send both text and image in a single message
                bot.send_photo(message.chat.id, photo=image_file, caption=new_user_message, reply_markup=keyboard,
                               parse_mode='HTML')
        except FileNotFoundError:
            # Handle the case where the image file is not found
            bot.reply_to(message, "Error: Image not found.")

    else:
        if not message.text:
            keyboard = generate_main_keyboard(user_id=user_id)
            bot.reply_to(message, text="", reply_markup=keyboard)

        else:
            keyboard = generate_main_keyboard(user_id=user_id)

            welcome_message = get_message_text(db=users_db, message_key='welcome_message', user_id=user_id)

            image_path = 'webp_images/main.webp'

            try:
                # Open the image file
                with open(image_path, 'rb') as image_file:
                    # Send both text and image in a single message
                    bot.send_photo(message.chat.id, photo=image_file, caption=welcome_message, reply_markup=keyboard,
                                   parse_mode='HTML')
            except FileNotFoundError:
                # Handle the case where the image file is not found
                bot.reply_to(message, "Error: Image not found.")


@bot.callback_query_handler(func=lambda call: call.data == "initiation")
def handle_initiation(call):
    message = call.message
    user_id = message.chat.id
    chanel_id = config.CHANNEL_ID
    member_status = bot.get_chat_member(chanel_id, user_id).status
    is_initiated = member_status == 'member' or member_status == 'administrator'

    if is_initiated:

        keyboard = generate_main_keyboard(user_id=user_id)

        welcome_message = get_message_text(db=users_db, message_key='welcome_message', user_id=user_id)

        image_path = 'webp_images/main.webp'

        try:
            bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

            with open(image_path, 'rb') as image_file:
                # Send both text and image in a single message
                bot.send_photo(message.chat.id, photo=image_file, caption=welcome_message, reply_markup=keyboard,
                               parse_mode='HTML')
        except FileNotFoundError:
            # Handle the case where the image file is not found
            bot.reply_to(message, "Error: Image not found.")

    else:
        initiation_failed_message = get_message_text(db=users_db, message_key='initiation_failed_message', user_id=user_id)
        bot.send_message(user_id, initiation_failed_message)


@bot.message_handler(func=lambda message: get_button_name(users_db, message.chat.id, "pillage_button") == message.text)
def handle_pillage(message):
    user_id = message.chat.id
    claim_button = telebot.types.InlineKeyboardButton(get_button_name(users_db, user_id, "claim_button"),
                                                      callback_data="claim_gold")

    keyboard = telebot.types.InlineKeyboardMarkup().add(claim_button)

    pillage_message = get_message_text(db=users_db, user_id=user_id, message_key='pillage_info_message')

    # Specify the path to the image you want to send
    image_path = 'webp_images/pillage.webp'

    try:
        # Open the image file
        with open(image_path, 'rb') as image_file:
            # Send both text and image in a single message
            bot.send_photo(message.chat.id, photo=image_file, caption=pillage_message, reply_markup=keyboard,
                           parse_mode='HTML')
    except FileNotFoundError:
        # Handle the case where the image file is not found
        bot.reply_to(message, "Error: Image not found.")


@bot.callback_query_handler(func=lambda call: call.data == "claim_gold")
def claim_gold_callback(call):
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    user_id = call.message.chat.id
    last_claim_time = get_last_pillage_time(users_db, user_id)

    if last_claim_time is None or (datetime.now() - datetime.fromtimestamp(last_claim_time)) >= timedelta(hours=4):
        update_last_pillage_time(users_db, user_id, get_current_timestamp())
        claim_gold(db=users_db, user_id=user_id)

        reward_time = count_reward_time(users_db, user_id)

        successful_claim_message = get_message_text(db=users_db, user_id=user_id,
                                                    message_key='pillage_success_message', reward_time=reward_time)

        # Specify the path to the image you want to send
        image_path = 'webp_images/claim_successful.webp'

        try:
            # Open the image file
            with open(image_path, 'rb') as image_file:
                # Send both text and image in a single message
                bot.send_photo(call.message.chat.id, photo=image_file, caption=successful_claim_message)
        except FileNotFoundError:
            # Handle the case where the image file is not found
            bot.reply_to(call.message, "Error: Image not found.")
    else:
        reward_time = count_reward_time(users_db, user_id)

        unsuccessful_claim_message = get_message_text(db=users_db, user_id=user_id,
                                                      message_key='pillage_failure_message', reward_time=reward_time)

        # Specify the path to the image you want to send
        image_path = 'webp_images/claim_unsuccessful.webp'

        try:
            # Open the image file
            with open(image_path, 'rb') as image_file:
                # Send both text and image in a single message
                bot.send_photo(call.message.chat.id, photo=image_file, caption=unsuccessful_claim_message)
        except FileNotFoundError:
            # Handle the case where the image file is not found
            bot.reply_to(call.message, "Error: Image not found.")


@bot.message_handler(func=lambda message: get_button_name(users_db, message.chat.id, "balance_button") == message.text)
def handle_balance(message):
    user_id = message.chat.id
    user_balance = get_user_balance(users_db, user_id)

    balance_message = get_message_text(db=users_db, user_id=user_id, message_key='current_balance_message',
                                       user_balance=user_balance)

    # Specify the path to the image you want to send
    image_path = 'webp_images/balance.webp'

    try:
        # Open the image file
        with open(image_path, 'rb') as image_file:
            # Send both text and image in a single message
            bot.send_photo(message.chat.id, photo=image_file, caption=balance_message)
    except FileNotFoundError:
        # Handle the case where the image file is not found
        bot.reply_to(message, "Error: Image not found.")


@bot.message_handler(
    func=lambda message: get_button_name(users_db, message.chat.id, "referrals_button") == message.text)
def handle_squad(message):
    user_id = message.chat.id
    user_data = users_db.get_user_data(user_id)
    referral_code = user_data.get("referral_code")
    amount_of_referrals = user_data.get("amount_of_referrals")

    squad_message = get_message_text(
        db=users_db,
        user_id=user_id,
        message_key='referrals_info_message',
        referral_code=referral_code,
        amount_of_referrals=amount_of_referrals,
        base_url=config.REFERRAL_BASE_URL,
    )

    invite_button = telebot.types.InlineKeyboardButton(
        get_button_name(users_db, user_id, "invite_button"),
        callback_data="invite",
        url=config.INVITE_URL,
    )

    keyboard = telebot.types.InlineKeyboardMarkup().add(invite_button)

    # Specify the path to the image you want to send
    image_path = 'webp_images/squad.webp'

    try:
        # Open the image file
        with open(image_path, 'rb') as image_file:
            # Send both text and image in a single message
            bot.send_photo(message.chat.id, photo=image_file, caption=squad_message, reply_markup=keyboard,
                           parse_mode="HTML")
    except FileNotFoundError:
        # Handle the case where the image file is not found
        bot.reply_to(message, "Error: Image not found.")


@bot.message_handler(func=lambda message: get_button_name(users_db, message.chat.id, "quests_button") == message.text)
def handle_quests(message):
    user_id = message.chat.id

    # # Create a keyboard with language options
    # keyboard = telebot.types.InlineKeyboardMarkup()
    # active_quests = get_active_quests(users_db, user_id)
    #
    # if active_quests:
    #
    #     for quest in active_quests:
    #         quest_code = quest
    #         keyboard.add(telebot.types.InlineKeyboardButton(text=get_button_name(users_db, user_id, quest_code),
    #                                                         callback_data=quest_code))
    #
    #     quest_list_message = get_message_text(db=users_db, user_id=user_id, message_key='quests_list_message')
    #
    # else:
    quest_list_message = get_message_text(db=users_db, user_id=user_id, message_key='quests_list_empty_message')

    image_path = 'webp_images/quests.webp'

    try:
        # Open the image file
        with open(image_path, 'rb') as image_file:
            # Send both text and image in a single message
            bot.send_photo(message.chat.id, photo=image_file, caption=quest_list_message)
            # bot.send_photo(message.chat.id, photo=image_file, caption=quest_list_message,
            #                reply_markup=keyboard)
    except FileNotFoundError:
        # Handle the case where the image file is not found
        bot.reply_to(message, "Error: Image not found.")


# @bot.callback_query_handler(func=lambda call: call.data in get_active_quests(users_db, call.message.chat.id))
# def quest_buttons_callback(call):
#     bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
#
#     user_id = call.message.chat.id
#
#     if call.data == 'daily_quest_button':
#         link_button_key = 'link_daily_quest_button'
#         link_callback_data = 'link_to_twitter'
#         check_callback_data = 'check_daily_quest'
#         quest_code = 'daily_quest_message'
#         url = get_latest_tweet_url(users_db)
#     elif call.data == 'start_another_bot_button':
#         link_button_key = 'link_bot_quest_button'
#         link_callback_data = 'link_to_bot'
#         check_callback_data = 'check_another_bot_quest'
#         quest_code = 'start_another_bot_quest_message'
#         url = get_latest_tweet_url(users_db)
#     else:
#         link_button_key = 'link_subscribe_quest_button'
#         link_callback_data = 'link_to_channel'
#         check_callback_data = 'check_subscribe_tg_channel_quest'
#         quest_code = 'subscribe_tg_channel_quest_message'
#         url = get_latest_tweet_url(users_db)
#
#     link_button = telebot.types.InlineKeyboardButton(get_button_name(users_db, user_id, link_button_key),
#                                                      callback_data=link_callback_data, url=url)
#     check_button = telebot.types.InlineKeyboardButton(get_button_name(users_db, user_id, "check_quest_button"),
#                                                       callback_data=check_callback_data)
#
#     keyboard = telebot.types.InlineKeyboardMarkup().add(link_button, check_button)
#
#     message = get_message_text(users_db, user_id, quest_code)
#
#     image_path = 'webp_images/language.webp'
#
#     try:
#         # Open the image file
#         with open(image_path, 'rb') as image_file:
#             # Send both text and image in a single message
#             bot.send_photo(call.message.chat.id, photo=image_file, caption=message,
#                            reply_markup=keyboard)
#     except FileNotFoundError:
#         # Handle the case where the image file is not found
#         bot.reply_to(call.message, "Error: Image not found.")
#
#     twitter_link_clicked(users_db, user_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('link_'))
def handle_link_buttons(call):
    user_id = call.message.chat.id
    link_type = call.data.replace('link_', '')
    if link_type == 'to_twitter':
        pass

    elif link_type == 'bot_quest_button':
        pass

    elif link_type == 'subscribe_quest_button':
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
def handle_check_buttons(call):
    user_id = call.message.chat.id
    check_type = call.data.replace('check_', '')

    if check_type == 'daily_quest':
        if mark_daily_quest_completed(users_db, user_id):
            message = get_message_text(users_db, user_id, 'daily_quest_completed_message')
            bot.send_message(user_id, message)
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        else:
            message = get_message_text(users_db, user_id, 'daily_quest_failed_message')
            bot.send_message(user_id, message)

    elif check_type == 'another_bot_quest':
        pass

    elif check_type == 'subscribe_tg_channel_quest':
        pass


@bot.message_handler(func=lambda message: get_button_name(users_db, message.chat.id, "language_button") == message.text)
def language_handler(message):
    user_id = message.chat.id

    # Create a keyboard with language options
    keyboard = telebot.types.InlineKeyboardMarkup()

    for language_code in LANGUAGES:
        language_name = LANGUAGES[language_code].get('language_name', language_code)  # Get language name if available
        keyboard.add(telebot.types.InlineKeyboardButton(text=language_name, callback_data=language_code))

    language_choose_message = get_message_text(db=users_db, user_id=user_id, message_key='language_choose_message')

    # Specify the path to the image you want to send
    image_path = 'webp_images/language.webp'

    try:
        # Open the image file
        with open(image_path, 'rb') as image_file:
            # Send both text and image in a single message
            bot.send_photo(message.chat.id, photo=image_file, caption=language_choose_message, reply_markup=keyboard)
    except FileNotFoundError:
        # Handle the case where the image file is not found
        bot.reply_to(message, "Error: Image not found.")


@bot.callback_query_handler(func=lambda call: call.data in LANGUAGES.keys())
def language_buttons_callback(call):
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    user_id = call.message.chat.id
    language_code = call.data

    try:
        # Update user's language in the database
        change_user_language(users_db, user_id, language_code)

        keyboard = generate_main_keyboard(user_id=user_id)

        # Send confirmation message
        bot.send_message(
            user_id,
            get_message_text(db=users_db, user_id=user_id, message_key='language_switched_message'),
            reply_markup=keyboard)

    except ValueError as ex:
        # Handle invalid language code
        bot.send_message(user_id, str(ex))


try:
    bot.infinity_polling()
except Exception as e:
    logger = logging.getLogger(__name__)  # Get the logger for this module
    logger.exception("An error occurred during polling: %s", e)

