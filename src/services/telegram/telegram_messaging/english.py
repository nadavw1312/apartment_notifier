"""
English implementation of telegram messages
"""
from src.services.telegram.telegram_messaging.base import TelegramMessages

class EnglishMessages(TelegramMessages):
    """English implementation of telegram messages"""
    
    # Generic messages
    def welcome_message(self) -> str:
        return "Welcome to Apartment Notifier!"
    
    def welcome_back(self, name: str) -> str:
        return f"Welcome back, {name}!"
    
    def error_message(self) -> str:
        return "Sorry, an error occurred. Please try again later."
    
    def loading_message(self) -> str:
        return "Loading..."
    
    # Button texts
    def signup_button(self) -> str:
        return "Sign Up"
    
    def preferences_button(self) -> str:
        return "Set Preferences"
    
    # Registration messages
    def registration_start(self) -> str:
        return "Let's get you signed up."
    
    def ask_email(self) -> str:
        return "Please enter your email address:"
    
    def ask_name(self) -> str:
        return "Great! Now please enter your name:"
    
    def invalid_email(self) -> str:
        return "Please enter a valid email address:"
    
    def registration_error(self) -> str:
        return "Sorry, there was an error completing your signup.\nPlease try again later."
    
    def registration_success(self, name: str) -> str:
        return f"Great! You're now registered, {name}. Use the /preferences command to set up your preferences."
    
    # Preferences messages
    def preferences_start(self) -> str:
        return "Let's set up your apartment preferences."
    
    def ask_min_price(self) -> str:
        return "What's the minimum price you're looking for? (in NIS)\nType 0 for no minimum."
    
    def ask_max_price(self) -> str:
        return "What's the maximum price you're looking for? (in NIS)\nType 0 for no maximum."
    
    def ask_min_rooms(self) -> str:
        return "How many rooms do you need at minimum?\nType 0 for no minimum."
    
    def ask_max_rooms(self) -> str:
        return "What's the maximum number of rooms you're looking for?\nType 0 for no maximum."
    
    def ask_min_area(self) -> str:
        return "What's the minimum apartment size you're looking for? (in square meters)\nType 0 for no minimum."
    
    def ask_max_area(self) -> str:
        return "What's the maximum apartment size you're looking for? (in square meters)\nType 0 for no maximum."
    
    def invalid_number(self) -> str:
        return "Please enter a valid number:"
    
    def negative_number_error(self) -> str:
        return "Please enter a positive number:"
    
    def preferences_saved(self) -> str:
        return "Perfect! Your apartment preferences have been saved.\nYou'll now receive notifications about apartments that match your criteria."
    
    def preferences_error(self) -> str:
        return "Sorry, there was an error saving your preferences.\nPlease try again later using the /preferences command."
    
    def signup_required(self) -> str:
        return "You need to sign up first before setting preferences.\nPlease click the Sign Up button."
    
    # Apartment messages
    def apartment_details_title(self) -> str:
        return "🏠 *Apartment Details* 🏠"
    
    def apartment_location(self) -> str:
        return "📍 *Location:*"
    
    def apartment_price(self) -> str:
        return "💰 *Price:*"
    
    def apartment_posted_by(self) -> str:
        return "👤 *Posted by:*"
    
    def apartment_posted_on(self) -> str:
        return "🕒 *Posted on:*"
    
    def apartment_contact(self) -> str:
        return "📱 *Contact:*"
    
    def apartment_summary(self) -> str:
        return "📝 *Summary:*"
    
    def apartment_original_post(self) -> str:
        return "📄 *Original Post:*"
    
    def apartment_view_original(self) -> str:
        return "🔗 [View Original Post]"
    
    def apartment_not_found(self) -> str:
        return "Sorry, I couldn't find that apartment."
    
    def apartment_fetch_error(self) -> str:
        return "Sorry, there was an error getting apartment details."
    
    def apartment_id_required(self) -> str:
        return "Please provide an apartment ID. Usage: /apartment <id>"
    
    def apartment_invalid_id(self) -> str:
        return "Invalid apartment ID. Please provide a valid number." 