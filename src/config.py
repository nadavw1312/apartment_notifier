import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/apartment_notifier")
DB_TYPE = os.getenv("DB_TYPE", "sql")  # Options: "sql" or "nosql"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")

FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "your_facebook_access_token")
FACEBOOK_GROUP_ID = os.getenv("FACEBOOK_GROUP_ID", "your_facebook_group_id")

DOMAIN = os.getenv("DOMAIN", "https://ab13-77-126-46-8.ngrok-free.app")

DEEPSEEK_API_KEY = "sk-55cea438c7e44b229526f19eba3631e9"

GMAIL_USERNAME = "dirot2411@gmail.com"
GMAIL_PASSWORD = "dirotbot2025"
