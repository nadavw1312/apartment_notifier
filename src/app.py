from fastapi import FastAPI, Request, HTTPException
from aiogram.fsm.storage.memory import MemoryStorage
from src.db.sql_database import SQL_DB_MANAGER
from src.services.user.user_api import router as user_router
from src.services.apartment.apartment_api import router as apartment_router
from src.services.notification.notification_api import router as notification_router
from src.services.telegram.telegram_bot import TelegramBot
from src.config import TELEGRAM_BOT_TOKEN, DOMAIN
from contextlib import asynccontextmanager

# Ensure the token is not None
if TELEGRAM_BOT_TOKEN is None:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")

# Initialize your custom TelegramBot class
telegram_bot = TelegramBot(token=TELEGRAM_BOT_TOKEN)

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup logic
    await SQL_DB_MANAGER.init()
    await telegram_bot.start()
    await telegram_bot.set_webhook(DOMAIN)
    yield
    # Shutdown logic
    await SQL_DB_MANAGER.close()
    await telegram_bot.stop()

# Create the FastAPI app with lifespan events
app = FastAPI(
    title="Apartment Notifier POC - Hybrid DB Approach",
    description="Service for managing apartment notifications",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        # Parse the incoming update
        update_data = await request.json()
        # Process the update using the TelegramBot instance
        await telegram_bot.process_update(update_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(apartment_router, prefix="/apartments", tags=["Apartments"])
app.include_router(notification_router, prefix="/notifications", tags=["Notifications"])
