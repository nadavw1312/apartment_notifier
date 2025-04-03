import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.telegram.telegram_bot import TelegramBot, UserSignupStates

@pytest.fixture
def mock_bot():
    """Create a mock Telegram bot with a dummy valid token."""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot

@pytest.fixture
def mock_dispatcher():
    """Create a mock dispatcher."""
    dp = MagicMock()
    dp.message = MagicMock()
    dp.storage = AsyncMock()
    return dp

@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
async def telegram_bot(mock_bot, mock_dispatcher, mock_session):
    """Create a TelegramBot instance with mocked dependencies."""
    with patch('src.services.telegram.telegram_bot.Bot', return_value=mock_bot), \
         patch('src.services.telegram.telegram_bot.Dispatcher', return_value=mock_dispatcher):
        bot_instance = TelegramBot(token="123456:TEST_TOKEN")
        bot_instance.set_session(mock_session)
        await bot_instance.start()  # Ensure the bot is started
        yield bot_instance
        await bot_instance.stop()  # Ensure the bot is stopped

@pytest.mark.asyncio
async def test_start_command(telegram_bot, mock_bot):
    """Test the /start command handling."""
    # Create a mock message
    message = MagicMock(spec=types.Message)
    message.text = "/start"
    message.from_user = MagicMock()
    message.from_user.id = 123456
    message.answer = AsyncMock()
    
    # Create a mock state
    state = MagicMock(spec=FSMContext)
    state.set_state = AsyncMock()
    
    # Call the handler
    await telegram_bot._handle_start(message, state)
    
    # Verify that message.answer is called with a welcome message
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    text_sent = kwargs.get("text", "")
    assert "Welcome to Apartment Notifier" in text_sent, f"Expected welcome text, got: {text_sent}"
    
    # Verify that the state is set to waiting_for_email
    state.set_state.assert_called_once_with(UserSignupStates.waiting_for_email)

@pytest.mark.asyncio
async def test_email_validation(telegram_bot):
    """Test email validation in the signup flow."""
    # Create a mock message with an invalid email
    message = MagicMock(spec=types.Message)
    message.text = "invalid-email"
    message.answer = AsyncMock()
    
    # Create a mock state
    state = MagicMock(spec=FSMContext)
    state.update_data = AsyncMock()
    
    # Call the handler
    await telegram_bot._handle_email(message, state)
    
    # Verify that message.answer is called with an error message about valid email address
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    text_sent = kwargs.get("text", "")
    assert "valid email address" in text_sent, f"Expected email validation error, got: {text_sent}"
    
    # Ensure that update_data is not called when email is invalid
    state.update_data.assert_not_called()

@pytest.mark.asyncio
async def test_successful_signup(telegram_bot, mock_session):
    """Test successful user signup flow."""
    # Create a mock message with valid name input
    message = MagicMock(spec=types.Message)
    message.text = "John Doe"
    message.from_user = MagicMock()
    message.from_user.id = 123456
    message.answer = AsyncMock()
    
    # Create a mock state with stored email data
    state = MagicMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={"email": "john@example.com"})
    state.clear = AsyncMock()
    
    # Call the handler for name input (completing signup)
    await telegram_bot._handle_name(message, state)
    
    # Verify that the database session methods were called (e.g., add, commit, refresh)
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    
    # Verify that a confirmation message is sent to the user
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    text_sent = kwargs.get("text", "")
    assert "Perfect! You're now signed up" in text_sent, f"Expected signup confirmation, got: {text_sent}"
    
    # Ensure the state is cleared after signup
    state.clear.assert_called_once()

@pytest.mark.asyncio
async def test_send_message(telegram_bot, mock_bot):
    """Test sending a message successfully."""
    # Call send_message on the TelegramBot instance
    success = await telegram_bot.send_message("123456", "Test message")
    
    # Verify that send_message returns True on success
    assert success is True
    mock_bot.send_message.assert_called_once_with(chat_id="123456", text="Test message")

@pytest.mark.asyncio
async def test_send_message_failure(telegram_bot, mock_bot):
    """Test sending a message when it fails."""
    # Configure the mock bot to raise an exception
    mock_bot.send_message.side_effect = Exception("API Error")
    
    # Call send_message and expect it to handle the exception gracefully
    success = await telegram_bot.send_message("123456", "Test message")
    
    # Verify that send_message returns False on failure
    assert success is False
