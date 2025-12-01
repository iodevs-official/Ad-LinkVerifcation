from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from pytz import timezone
from datetime import datetime

MONGO_URI = "Mongo DB URI"
mongo_client = MongoClient(MONGO_URI)
IST = timezone("Asia/Kolkata")
SUDO = 6883997969

# Helper function to get today's collection
def get_today_collection():
    db = mongo_client["users"]
    today = datetime.now(IST).strftime("%Y-%m-%d")
    return db[today]


# Helper function to check if a user is verified
async def is_user_verified(user_id):
    try:
        collection = get_today_collection()
        verified_user = collection.find_one({"type": "verified", "users": {"$in": [user_id]}})
        return bool(verified_user)
    except Exception as e:
        print(f"Error checking verification: {e}")
        return False


@Client.on_message(filters.command("status") & filters.user(SUDO))
async def status_command(client, message):
    try:
        collection = get_today_collection()
        
        # Fetch verified documents
        verified_docs = list(collection.find({"type": "verified"}))
        
        # Calculate total users and build the user list
        total_users = sum(len(doc.get("users", [])) for doc in verified_docs)
        user_list = [user_id for doc in verified_docs for user_id in doc.get("users", [])]
        
        # Prepare response
        users_text = "\n".join([str(user_id) for user_id in user_list])
        response = f"Total verified users: {total_users}\n\nUsers:\n{users_text}" if user_list else "No verified users found."

        await message.reply_text(response)
    except Exception as e:
        print(f"Error in status command: {e}")
        await message.reply_text("An error occurred while fetching the status. Please try again later.")



# Command: /remove
@Client.on_message(filters.command("remove") & filters.user(SUDO))
async def remove_command(client, message):
    try:
        command_data = message.text.split(" ", 1)
        if len(command_data) < 2:
            return await message.reply_text("Please provide a user ID to remove. Example: /remove 123456789")
        
        user_id = int(command_data[1])
        collection = get_today_collection()
        verified_doc = collection.find_one({"type": "verified", "users": {"$in": [user_id]}})
        
        if verified_doc:
            # Ask for confirmation
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"Remove {user_id}", callback_data=f"remove_{user_id}")]
            ])
            await message.reply_text(f"Do you want to remove user ID: {user_id} from the list?", reply_markup=keyboard)
        else:
            await message.reply_text(f"User ID {user_id} is not in the verified list.")
    except Exception as e:
        print(f"Error in remove command: {e}")
        await message.reply_text("An error occurred. Please try again later.")


# Callback handler for remove confirmation
@Client.on_callback_query(filters.regex(r"remove_\d+"))
async def remove_user_callback(client, callback_query):
    try:
        user_id = int(callback_query.data.split("_")[1])
        collection = get_today_collection()
        result = collection.update_one({"type": "verified"}, {"$pull": {"users": user_id}})
        
        if result.modified_count > 0:
            await callback_query.message.edit_text(f"User ID {user_id} has been successfully removed.")
        else:
            await callback_query.message.edit_text(f"User ID {user_id} could not be found in the verified list.")
    except Exception as e:
        print(f"Error in remove callback: {e}")
        await callback_query.message.edit_text("An error occurred. Please try again later.") 
