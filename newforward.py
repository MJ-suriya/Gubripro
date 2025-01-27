import os
import re
import logging
from telethon import TelegramClient, events

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fetch Telegram API credentials from environment variables
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Group IDs
SOURCE_GROUP_8DIGIT = 1001819819794  # This group checks both 8-digit and FP codes
SOURCE_GROUPS_FP_ONLY = [-1001234567890, -1009876543210]  # Other groups for FP codes only

# Destination Channel ID
DESTINATION_CHANNEL_ID = -1002293227856

# Start Telethon Client (Userbot Mode)
client = TelegramClient("userbot_session", api_id, api_hash)

@client.on(events.NewMessage(chats=[SOURCE_GROUP_8DIGIT] + SOURCE_GROUPS_FP_ONLY))
async def forward_message(event):
    """Extract and forward only relevant text messages."""
    text = event.message.text
    if not text:
        return  # Skip if there's no text

    formatted_text = text  # Preserve original text

    # Check which source the message came from
    source_id = event.chat_id

    # Extract FP Code (10 characters starting with FP or fp)
    fp_match = re.search(r'\b(fp\w{8})\b', text, re.IGNORECASE)
    fp_code = fp_match.group(1) if fp_match else None

    # Extract 8-digit code (only for SOURCE_GROUP_8DIGIT)
    digit_match = re.search(r'\b(\w{8})\b', text)
    digit_code = digit_match.group(1) if digit_match else None

    # Ignore codes starting with BP
    if digit_code and digit_code.upper().startswith("BP"):
        return  # Skip BP codes

    # Format the 8-digit code in mono font (only for SOURCE_GROUP_8DIGIT)
    if digit_code and source_id == SOURCE_GROUP_8DIGIT:
        formatted_text = text.replace(digit_code, f"`{digit_code}`")  # Using mono font for 8-digit code

    # Look for the "Answer:" part and format it in mono font
    answer_match = re.search(r"Answer:\s*(.*)", text)
    if answer_match:
        answer_text = answer_match.group(1)
        formatted_answer = f"Answer:\n```{answer_text}```"  # Wrap the answer text in triple backticks
        formatted_text = re.sub(r"Answer:\s*(.*)", formatted_answer, formatted_text)

    # Remove unnecessary hashtags (#box, #square)
    formatted_text = re.sub(r'#(box|square)', '', formatted_text).strip()

    # Ensure there is valid content to send
    if digit_code or fp_code:
        await client.send_message(DESTINATION_CHANNEL_ID, formatted_text)
        logger.info(f"✅ Forwarded: {formatted_text}")
    else:
        logger.warning("❌ No valid code found, message skipped.")

logger.info("✅ Userbot is running and monitoring messages...")
client.start()
client.run_until_disconnected()
