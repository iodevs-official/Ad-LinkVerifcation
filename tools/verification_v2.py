import asyncio
import random
import string
from datetime import datetime
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp
import traceback

# MongoDB configurations
FILE_TO_LINK_URI = "Mongo DB URI"
ACCESS_MANAGER_URI = "Mongo DB URI"

# Initialize MongoDB clients
file_to_link_client = MongoClient(FILE_TO_LINK_URI)
access_manager_client = MongoClient(ACCESS_MANAGER_URI)

# Databases and collections
user_links_db = file_to_link_client["User_Links"]
premium_credit_db = access_manager_client["FileToLink"]
user_links_collection = user_links_db["verification_links"]
premium_credit_collection = premium_credit_db["premium_credit"]

start_text = """
Hi,

Welcome to access manager bot.

Use our bots with Adlinks to get access to all bots.
Unlike others, you only need to complete one link to access all our bots for that day.

Made By @botio_devs
"""

async def generate_random_string(length: int) -> str:
    """Generate a random alphanumeric string of given length"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def shorten_url(link: str) -> str:
    """Shorten URL using the modiji API"""
    from config import modiji_url, modiji_api
    
    api_url = f'https://{modiji_url}/api'
    params = {'api': modiji_api, 'url': link}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, raise_for_status=True, ssl=False) as response:
                data = await response.json()
                if data.get("status") == "success":
                    return data['shortenedUrl']
                return f'https://{modiji_url}/api?api={modiji_api}&url={link}'
    except Exception as e:
        print(f"URL shortening error: {e}")
        return link 


async def report_error(client, error_msg: str):
    """Report errors to admin or log channel"""
    try:
        # Replace with your error reporting channel ID
        await client.send_message(-100123456789, error_msg)
    except Exception as e:
        print(f"Error reporting failed: {e}")

async def makelinkv2(client, message, mssg, botname: str):
    """Generate verification link and send to user"""
    try:
        user_id = message.from_user.id
        doc_name = await generate_random_string(6)
        verification_code = await generate_random_string(12)
        
        # Current time in ISO format without seconds
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
        
        # Prepare verification document
        verification_data = {
            "name": doc_name,
            "verification_code": verification_code,
            "user_id": user_id,
            "botname": botname,
            "credits": 5,
            "created_at": current_time,
            "used": False
        }
        
        # Insert into MongoDB
        await asyncio.to_thread(user_links_collection.insert_one, verification_data)
        
        # Create verification URL
        verify_url = f"https://telegram.me/Bots_Access_Manager_l_Bot?start=v2verify_{doc_name}_{verification_code}"
        short_url = await shorten_url(verify_url)
        
        # Prepare reply with button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Get Now", url=short_url)]
        ])
        
        await mssg.edit_text(
            "Use Below Link To Earn 5 credits",
            reply_markup=keyboard
        )
        
    except Exception as e:
        error_msg = f"#makelinkv2_error\n\nError generating link:\n```{traceback.format_exc()}```"
        await report_error(client, error_msg)
        await mssg.edit_text("Failed to generate link. Please try again later.")

async def check_verificationv2(client, message, doc_name: str, verification_str: str):
    """Verify user and update credits"""
    try:
        # Find the verification document
        doc = await asyncio.to_thread(user_links_collection.find_one, {"name": doc_name})
        
        if not doc:
            await message.reply_text("Invalid verification link.")
            return
            
        if doc.get("used", False):
            await message.reply_text("This link has already been used.")
            return
            
        if doc.get("verification_code") != verification_str:
            await message.reply_text("Verification failed. Invalid code.")
            return
            
        user_id = doc["user_id"]
        credits_to_add = doc["credits"]
        
        # Mark the link as used
        await asyncio.to_thread(
            user_links_collection.update_one,
            {"name": doc_name},
            {"$set": {"used": True}}
        )
        
        # Update user credits in premium_credit collection
        premium_doc = await asyncio.to_thread(
            premium_credit_collection.find_one,
            {"name": "premium_credit"}
        )
        
        if not premium_doc:
            # Create new premium_credit document if it doesn't exist
            new_doc = {
                "name": "premium_credit",
                "users": {str(user_id): credits_to_add}
            }
            await asyncio.to_thread(premium_credit_collection.insert_one, new_doc)
            new_credits = credits_to_add
        else:
            # Update existing user or add new user
            current_credits = premium_doc.get("users", {}).get(str(user_id), 0)
            new_credits = current_credits + credits_to_add
            
            await asyncio.to_thread(
                premium_credit_collection.update_one,
                {"name": "premium_credit"},
                {"$set": {f"users.{user_id}": new_credits}},
                upsert=True
            )
        
        await message.reply_text(
            f"✅ You have successfully verified!\n"
            f"Current balance: {new_credits} credits"
        )
        
    except Exception as e:
        error_msg = f"#check_verificationv2_error\n\nVerification failed:\n```{traceback.format_exc()}```"
        await report_error(client, error_msg)
        await message.reply_text("Verification failed. Please try again later.")

