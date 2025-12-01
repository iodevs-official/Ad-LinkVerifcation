from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from tools.report import report_error
from tools.verification_v2 import makelinkv2, check_verificationv2
import asyncio
import traceback
from pytz import timezone
from datetime import datetime
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import makelink, check_verification, is_user_verified


START_TEXT = """
Hi!  

Welcome to the Access Manager Bot.  

Use our bots with AdLinks to unlock all features.  
**One verification = Access to all bots for 24hrs!**  

Made by @botio_devs  
"""

@Client.on_message(filters.command("start"))
async def start_command(client, message):
    try:
        command_data = message.text.split(" ", 1)
        
        if len(command_data) > 1:
            start_data = command_data[1]
            
            if start_data == "terabox":
                user_id = message.from_user.id
                if await is_user_verified(user_id):
                    await message.reply_text("You are already verified.")
                    return
                
                mssg = await message.reply_text("Preparing your link...")
                return await makelink(client, message, mssg)

            elif start_data in ["FITLETOLINK", "OtherBotName"]:  # Add other bot names here
                mssg = await message.reply_text("Preparing your link...")
                return await makelinkv2(client, message, mssg, start_data)

            
            elif start_data.startswith("v2verify_"):
                # Handle v2 verification with format: v2verify_{doc_name}_{verification_code}
                verification_data = start_data.split("v2verify_", 1)[1]
                # Split into doc_name and verification_code parts
                parts = verification_data.split("_", 1)
                if len(parts) == 2:
                    doc_name, verification_str = parts
                    return await check_verificationv2(client, message, doc_name, verification_str)
                else:
                    # Handle invalid format
                    await message.reply("Invalid verification link format.")
                    return
                
            elif start_data.startswith("verify_"):
                verification_id = start_data.split("verify_", 1)[1]
                return await check_verification(client, message, verification_id)
                
                
        else:
            await message.reply_text(START_TEXT, reply_to_message_id=message.id)
            
    except Exception as e:
        error_msg = f"#start_command_error\n\nError in start command:\n```{traceback.format_exc()}```"
        await report_error(client, error_msg)
        await message.reply_text("An error occurred. Please try again later.")
