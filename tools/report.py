from pyrogram import enums, Client

async def report_error(client: Client, error_message: str):
    try:
        await client.send_message(
            chat_id=-1002259383577,
            text=f"**#Error :**\n{error_message}",
            reply_to_message_id=5,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except Exception as e:
        print(f"Failed to report error: {e}")
      
