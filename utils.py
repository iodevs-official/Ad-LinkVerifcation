import string
import random
import asyncio
import aiohttp
import traceback
from pytz import timezone
from datetime import datetime
from pyrogram import Client, enums
from pymongo import MongoClient
from config import modiji_url, modiji_api
from tools.report import report_error
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

MONGO_URI = "Mongo DB URI"
mongo_client = MongoClient(MONGO_URI)
IST = timezone("Asia/Kolkata")

api_key = modiji_api

def get_today_ist():
    """Returns today's date string in IST timezone."""
    return datetime.now(IST).strftime("%Y-%m-%d")

async def is_user_verified(user_id):
    try:
        db = mongo_client["users"]
        today = get_today_ist()
        collection = db[today]
        # Check if the user is in a document with type: "verified"
        verified_user = collection.find_one({"type": "verified", "users": {"$in": [user_id]}})
        return verified_user is not None
    except Exception as e:
        error_msg = f" #verify_check \n -------- ``` traceback error: \n {traceback.format_exc()} ```"
        # client is not available here; consider passing client as an argument if needed
        # await report_error(client, error_msg)
        print(f"Error checking user verification: {e}")
        return False

async def shorten_url(link: str) -> str:
    api_url = f'https://{modiji_url}/api'
    params = {
        'api': modiji_api,
        'url': link,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, raise_for_status=True, ssl=False) as response:
                try:
                    data = await response.json()
                    if data.get("status") == "success":
                        return data['shortenedUrl']
                    else:
                        print(f"API Error: {data.get('message', 'Unknown error')}")
                        return f'https://{modiji_url}/api?api={api_key}&url={link}'
                except aiohttp.ContentTypeError:
                    print("Failed to parse JSON response.")
                    return f'https://{modiji_url}/api?api={api_key}&url={link}'
    except aiohttp.ClientError as e:
        try:
            error_msg = f" #api_error\n\n Shortener Api Down 🔴🔴 \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
            await report_error(client, error_msg)
        except:
            pass
        print(f"HTTP request failed: {e}")
        return f'https://{modiji_url}/api?api={api_key}&url={link}'
    except Exception as e:
        try:
            error_msg = f" #api_error \n\n unable to make adlink 🔴🔴 \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
            await report_error(client, error_msg)
        except:
            pass
        print(f"An unexpected error occurred: {e}")
        return f'https://{modiji_url}/api?api={api_key}&url={link}'

async def makelink(client, message, mssg):
    # Connect to MongoDB collection for today's date (IST)
    try:
        db = mongo_client['keys']
        collection_name = get_today_ist()
        collection = db[collection_name]
    except Exception as e:
        try:
            error_msg = f" #db_error \n\n Unable to connect to database 🔴🔴 \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
            await report_error(client, error_msg)
        except:
            pass
        print(f"Error connecting to MongoDB: {e}")
        return

    # Check if a document with the user's ID already exists for today
    try:
        existing_doc = collection.find_one({"id": message.from_user.id})
        if existing_doc:
            # Document exists, retrieve the final URL and send it to the user
            final_url = existing_doc["ad_link"]
        
            await mssg.edit_text(
                "Verify your access:\n\nOld Link ✅",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Verify", url=final_url)]]
                )
            )
            return
    except Exception as e:
        try:
            error_msg = f" #db_error \n\n Failed to check existing user details 🔴🔴 \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
            await report_error(client, error_msg)
        except:
            pass
        print(f"Error checking for existing document: {e}")
        return

    
    # Generate keys and URLs if no existing document found
    try:
        pub_key = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        pem_key = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        print(f"Generated keys - pub_key: {pub_key}, pem_key: {pem_key}")
    except Exception as e:
        try:
            error_msg = f" #key_make \n\n Error in making verification KEYS \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
            await report_error(client, error_msg)
        except:
            pass
        print(f"Error generating keys: {e}")
        return

    # Generate and shorten link
    try:
        verify_link = f"https://telegram.me/Bots_Access_Manager_l_Bot?start=verify_{pem_key}"
        final_url = await shorten_url(verify_link)
    except Exception as e:
        try:
            error_msg = f" #make_adlink \n\n Failed to make the ad links 🔴🔴 \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
            await report_error(client, error_msg)
        except:
            pass
        print(f"Error generating or shortening link: {e}")
        return

    # Insert document into MongoDB, including the shortened link and final URL
    try:
        doc = {
            "id": message.from_user.id,
            "pub_key": pub_key,
            "pem_key": pem_key,
            "status": "pending",
            "ad_link": final_url,
            "request_time": datetime.now(IST).strftime("%H:%M")
        }
        collection.insert_one(doc)
    except Exception as e:
        try:
            error_msg = f" #error_adding_doc \n\n Error to add user keys and status to db. \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
            await report_error(client, error_msg)
        except:
            pass
        print(f"Error inserting document into MongoDB: {e}")
        return

    # Send message with button
    try:
        await mssg.edit_text(
            "Verify your access: \n\nNew Link ✅",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Verify", url=final_url)]]
            )
        )
    except Exception as e:
        try:
            error_msg = f" Failed_send_link \n\n Failed to send link to user 🔴🔴 \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
            await report_error(client, error_msg)
        except:
            pass
        print(f"Error sending message: {e}")
        return

    # Send info to log group
    try:
        await client.send_message(
            chat_id=-1002259383577,
            text=f"""
#req_tera_{datetime.now(IST).strftime("%b%0d")}

**User {message.from_user.id} requested url access for terabox bot**

```info ℹ️:

🔗 ad_link: {final_url},

🔗 Verify: {verify_link},

⌚ request_time: {datetime.now(IST).strftime("%H:%M")}```
            """,
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_to_message_id=3
        )
    except Exception as e:
        print(f"Error sending message: {e}")

async def check_verification(client, message, verification_id):
    try:
        today_date = get_today_ist()
        keys_db = mongo_client["keys"]
        keys_collection = keys_db[today_date]

        # Retrieve the document using the verification ID
        user_doc = keys_collection.find_one({"id": message.from_user.id})

        # Check if the user's document exists and pem_key matches the verification_id
        if user_doc and user_doc["pem_key"] == verification_id:
            # Update the status to "verified"
            keys_collection.update_one(
                {"id": message.from_user.id},
                {"$set": {"status": "verified"}}
            )

            # Access the 'users' database and the collection for today (IST)
            users_db = mongo_client["users"]
            users_collection = users_db[today_date]

            # Update the document by adding the user ID to the 'users' array
            users_collection.update_one(
                {"type": "verified"},
                {"$addToSet": {"users": message.from_user.id}},  # $addToSet to avoid duplicates
                upsert=True  # If the document doesn't exist, create it
            )

            # Notify the user of successful verification
            await message.reply_text("Your verification is successful! You are now registered.")
        else:
            try:
                error_msg = f" #Invalid_verification \n\n User given verification details is not correct 🔴🔴 \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
                await report_error(client, error_msg)
            except:
                pass
            await message.reply_text("Verification failed. Please check your details and try again.")

    except Exception as e:
        try:
            error_msg = f" #Check_verification \n\n Failed to check users verification link 🔴🔴 \n-------- ``` traceback error: \n {traceback.format_exc()} ```"
            await report_error(client, error_msg)
        except:
            pass
        await message.reply_text("An error occurred during verification. Please try again later.")
