import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Main Administrator ID (Owner)
OWNER_ID = int(os.getenv("OWNER_ID", 0))

# Database File Path
DB_PATH = "bot_database.db"

# Notification Settings
REMINDER_TIME_0 = "00:05"  # Time for birthday day notification
