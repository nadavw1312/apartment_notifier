"""
Abstract base class for Telegram messages
Defines the interface for all message providers
"""
from abc import ABC, abstractmethod

class TelegramMessages(ABC):
    """Abstract base class for telegram messages"""
    
    # Generic messages
    @abstractmethod
    def welcome_message(self) -> str:
        """Welcome message when user starts the bot"""
        pass
    
    @abstractmethod
    def welcome_back(self, name: str) -> str:
        """Welcome back message for returning users"""
        pass
    
    @abstractmethod
    def error_message(self) -> str:
        """Generic error message"""
        pass
    
    @abstractmethod
    def loading_message(self) -> str:
        """Loading message"""
        pass
    
    # Button texts
    @abstractmethod
    def signup_button(self) -> str:
        """Signup button text"""
        pass
    
    @abstractmethod
    def preferences_button(self) -> str:
        """Preferences button text"""
        pass
    
    # Registration messages
    @abstractmethod
    def registration_start(self) -> str:
        """Start registration process message"""
        pass
    
    @abstractmethod
    def ask_email(self) -> str:
        """Ask for email message"""
        pass
    
    @abstractmethod
    def ask_name(self) -> str:
        """Ask for name message"""
        pass
    
    @abstractmethod
    def invalid_email(self) -> str:
        """Invalid email message"""
        pass
    
    @abstractmethod
    def registration_error(self) -> str:
        """Registration error message"""
        pass
    
    @abstractmethod
    def registration_success(self, name: str) -> str:
        """Registration success message"""
        pass
    
    # Preferences messages
    @abstractmethod
    def preferences_start(self) -> str:
        """Start preferences setup message"""
        pass
    
    @abstractmethod
    def ask_min_price(self) -> str:
        """Ask for minimum price message"""
        pass
    
    @abstractmethod
    def ask_max_price(self) -> str:
        """Ask for maximum price message"""
        pass
    
    @abstractmethod
    def ask_min_rooms(self) -> str:
        """Ask for minimum rooms message"""
        pass
    
    @abstractmethod
    def ask_max_rooms(self) -> str:
        """Ask for maximum rooms message"""
        pass
    
    @abstractmethod
    def ask_min_area(self) -> str:
        """Ask for minimum area message"""
        pass
    
    @abstractmethod
    def ask_max_area(self) -> str:
        """Ask for maximum area message"""
        pass
    
    @abstractmethod
    def invalid_number(self) -> str:
        """Invalid number message"""
        pass
    
    @abstractmethod
    def negative_number_error(self) -> str:
        """Negative number error message"""
        pass
    
    @abstractmethod
    def preferences_saved(self) -> str:
        """Preferences saved message"""
        pass
    
    @abstractmethod
    def preferences_error(self) -> str:
        """Preferences error message"""
        pass
    
    @abstractmethod
    def signup_required(self) -> str:
        """Signup required message"""
        pass
    
    # Apartment messages
    @abstractmethod
    def apartment_details_title(self) -> str:
        """Apartment details title"""
        pass
    
    @abstractmethod
    def apartment_location(self) -> str:
        """Apartment location label"""
        pass
    
    @abstractmethod
    def apartment_price(self) -> str:
        """Apartment price label"""
        pass
    
    @abstractmethod
    def apartment_posted_by(self) -> str:
        """Apartment posted by label"""
        pass
    
    @abstractmethod
    def apartment_posted_on(self) -> str:
        """Apartment posted on label"""
        pass
    
    @abstractmethod
    def apartment_contact(self) -> str:
        """Apartment contact label"""
        pass
    
    @abstractmethod
    def apartment_summary(self) -> str:
        """Apartment summary label"""
        pass
    
    @abstractmethod
    def apartment_original_post(self) -> str:
        """Apartment original post label"""
        pass
    
    @abstractmethod
    def apartment_view_original(self) -> str:
        """Apartment view original post label"""
        pass
    
    @abstractmethod
    def apartment_not_found(self) -> str:
        """Apartment not found message"""
        pass
    
    @abstractmethod
    def apartment_fetch_error(self) -> str:
        """Apartment fetch error message"""
        pass
    
    @abstractmethod
    def apartment_id_required(self) -> str:
        """Apartment ID required message"""
        pass
    
    @abstractmethod
    def apartment_invalid_id(self) -> str:
        """Apartment invalid ID message"""
        pass 