# import os
# from dotenv import load_dotenv

# import google.generativeai as genai

# # Load environment variables
# load_dotenv()

# # Configure the Gemini API
# API_KEY = "AIzaSyDACX1YWGJ0hsVnk6sK20aDjCVFEc7Th1c"
# genai.configure(api_key=API_KEY)

# def setup_model():
#     """Initialize and return the Gemini model"""
#     model = genai.GenerativeModel('gemini-2.0-flash')
#     return model

# def translate_text(text, source_lang, target_lang):
#     """
#     Translate text between Arabic and English using Gemini API
    
#     Args:
#         text (str): The text to translate
#         source_lang (str): Source language code ('ar' or 'en')
#         target_lang (str): Target language code ('ar' or 'en')
        
#     Returns:
#         str: Translated text
#     """
#     if not text:
#         return ""
    
#     # Validate language codes
#     if source_lang not in ['ar', 'en'] or target_lang not in ['ar', 'en']:
#         raise ValueError("Language codes must be 'ar' (Arabic) or 'en' (English)")
    
#     # Skip translation if source and target languages are the same
#     if source_lang == target_lang:
#         return text
    
#     # Create the translation prompt
#     source_lang_name = "Arabic" if source_lang == "ar" else "English"
#     target_lang_name = "Arabic" if target_lang == "ar" else "English"
    
#     prompt = f"Translate the following {source_lang_name} text to {target_lang_name}. Return ONLY the translation, no additional text: {text}"
    
#     try:
#         model = setup_model()
#         response = model.generate_content(prompt)
#         return response.text.strip()
#     except Exception as e:
#         print(f"Translation error: {e}")
#         return text  # Return original text if translation fails

# def translate_ar_to_en(text):
#     """Helper function to translate from Arabic to English"""
#     return translate_text(text, 'ar', 'en')

# def translate_en_to_ar(text):
#     """Helper function to translate from English to Arabic"""
#     return translate_text(text, 'en', 'ar')

# # Example usage
# if __name__ == "__main__":
#     # Test Arabic to English
#     arabic_text = "مرحبا بالعالم"
#     english_translation = translate_ar_to_en(arabic_text)
#     print(f"Arabic: {arabic_text}")
#     print(f"English: {english_translation}")
    
#     # Test English to Arabic
#     english_text = "Hello world"
#     arabic_translation = translate_en_to_ar(english_text)
#     print(f"English: {english_text}")
#     print(f"Arabic: {arabic_translation}")



#JUST FOR TESTINGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
# Safe translation stub (paste this into chat_service/translate.py for testing)
# chat_service/translate.py (TEST STUB - use only for local testing)
# chat_service/translate.py (quick local, uses deep-translator)
import os
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

load_dotenv()

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    if not text:
        print("⚠️ Received empty text for translation.")
        return ""

    # If same language, return as-is
    if source_lang == target_lang:
        return text

    # deep-translator uses language codes like 'en', 'ar'
    try:
        # Try direct translation
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        print(f"✅ Translated result: {translated}")
        return translated
    except Exception as e:
        print(f"Translation error: {e} — falling back to stub tag")
        # fallback to your stub-style tag so app keeps working
        return f"[{source_lang.upper()}→{target_lang.upper()}] {text}"

def translate_ar_to_en(text: str) -> str:
    return translate_text(text, "ar", "en")

def translate_en_to_ar(text: str) -> str:
    return translate_text(text, "en", "ar")
