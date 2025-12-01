
import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
import pyrogram.utils
from flask import Flask
import threading


pyrogram.utils.MIN_CHANNEL_ID = -1009999999999

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def hello_world():
    return "Hello, World!"

# Run the Flask app in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Initialize and run the bot
def run_bot():
    logger.info("Starting the bot...")
    telegram_bot = Client(
        "my_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins=dict(root="plugins")
    )
    logger.info("Bot initialized.")
    telegram_bot.run()

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    run_bot()
