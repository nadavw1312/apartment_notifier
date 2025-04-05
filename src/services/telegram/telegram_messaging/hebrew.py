"""
Hebrew implementation of telegram messages
"""
from src.services.telegram.telegram_messaging.base import TelegramMessages

class HebrewMessages(TelegramMessages):
    """Hebrew implementation of telegram messages"""
    
    # Generic messages
    def welcome_message(self) -> str:
        return "ברוכים הבאים למערכת התראות דירות!"
    
    def welcome_back(self, name: str) -> str:
        return f"ברוכים הבאים שוב, {name}!"
    
    def error_message(self) -> str:
        return "מצטערים, אירעה שגיאה. אנא נסו שוב מאוחר יותר."
    
    def loading_message(self) -> str:
        return "טוען..."
    
    # Button texts
    def signup_button(self) -> str:
        return "הרשמה"
    
    def preferences_button(self) -> str:
        return "הגדרת העדפות"
    
    # Registration messages
    def registration_start(self) -> str:
        return "בואו נרשום אותך."
    
    def ask_email(self) -> str:
        return "אנא הזינו את כתובת האימייל שלכם:"
    
    def ask_name(self) -> str:
        return "מצוין! עכשיו אנא הזינו את שמכם:"
    
    def invalid_email(self) -> str:
        return "אנא הזינו כתובת אימייל תקינה:"
    
    def registration_error(self) -> str:
        return "מצטערים, אירעה שגיאה בהשלמת ההרשמה.\nאנא נסו שוב מאוחר יותר."
    
    def registration_success(self, name: str) -> str:
        return f"מצוין! נרשמת בהצלחה, {name}. השתמשו בפקודה /preferences כדי להגדיר את ההעדפות שלכם."
    
    # Preferences messages
    def preferences_start(self) -> str:
        return "בואו נגדיר את העדפות הדירה שלכם."
    
    def ask_min_price(self) -> str:
        return "מהו המחיר המינימלי שאתם מחפשים? (בש\"ח)\nהקלידו 0 אם אין מינימום."
    
    def ask_max_price(self) -> str:
        return "מהו המחיר המקסימלי שאתם מחפשים? (בש\"ח)\nהקלידו 0 אם אין מקסימום."
    
    def ask_min_rooms(self) -> str:
        return "כמה חדרים אתם צריכים לכל הפחות?\nהקלידו 0 אם אין מינימום."
    
    def ask_max_rooms(self) -> str:
        return "מהו מספר החדרים המקסימלי שאתם מחפשים?\nהקלידו 0 אם אין מקסימום."
    
    def ask_min_area(self) -> str:
        return "מהו גודל הדירה המינימלי שאתם מחפשים? (במטרים רבועים)\nהקלידו 0 אם אין מינימום."
    
    def ask_max_area(self) -> str:
        return "מהו גודל הדירה המקסימלי שאתם מחפשים? (במטרים רבועים)\nהקלידו 0 אם אין מקסימום."
    
    def invalid_number(self) -> str:
        return "אנא הזינו מספר תקין:"
    
    def negative_number_error(self) -> str:
        return "אנא הזינו מספר חיובי:"
    
    def preferences_saved(self) -> str:
        return "מצוין! העדפות הדירה שלכם נשמרו.\nכעת תקבלו התראות על דירות המתאימות לקריטריונים שלכם."
    
    def preferences_error(self) -> str:
        return "מצטערים, אירעה שגיאה בשמירת ההעדפות שלכם.\nאנא נסו שוב מאוחר יותר באמצעות הפקודה /preferences."
    
    def signup_required(self) -> str:
        return "עליכם להירשם תחילה לפני הגדרת העדפות.\nאנא לחצו על כפתור ההרשמה."
    
    # Apartment messages
    def apartment_details_title(self) -> str:
        return "🏠 *פרטי הדירה* 🏠"
    
    def apartment_location(self) -> str:
        return "📍 *מיקום:*"
    
    def apartment_price(self) -> str:
        return "💰 *מחיר:*"
    
    def apartment_posted_by(self) -> str:
        return "👤 *פורסם על ידי:*"
    
    def apartment_posted_on(self) -> str:
        return "🕒 *פורסם בתאריך:*"
    
    def apartment_contact(self) -> str:
        return "📱 *יצירת קשר:*"
    
    def apartment_summary(self) -> str:
        return "📝 *סיכום:*"
    
    def apartment_original_post(self) -> str:
        return "📄 *פוסט מקורי:*"
    
    def apartment_view_original(self) -> str:
        return "🔗 [צפייה בפוסט המקורי]"
    
    def apartment_not_found(self) -> str:
        return "מצטער, לא הצלחתי למצוא את הדירה הזו."
    
    def apartment_fetch_error(self) -> str:
        return "מצטער, אירעה שגיאה בקבלת פרטי הדירה."
    
    def apartment_id_required(self) -> str:
        return "אנא ספקו מזהה דירה. שימוש: /apartment <id>"
    
    def apartment_invalid_id(self) -> str:
        return "מזהה דירה לא תקין. אנא ספקו מספר תקין." 