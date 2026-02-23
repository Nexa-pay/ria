from flask import Flask, request, jsonify
import os
import logging
import random
import requests
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Bot configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set!")
    
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Funny Hinglish messages
MESSAGES = [
    "Hey {name} ❤️, tu toh bilkul {adjective} lag raha/rahi hai aaj!",
    "{name} 😍, teri smile ne mera dil chura liya!",
    "Oye {name} ✨, teri beauty ka koi answer nahi!",
    "{name} ji 💕, aapke liye ek special tag!",
    "Sun {name} 🌟, tu mere group ka sabse pyara member hai!",
    "Bhai {name} 🚀, tu aaya to group mein jaan aa gayi!",
]

ADJECTIVES = ["ekdum jhakaas", "superb", "awesome", "mast", "cool", "rocking"]
EMOJIS = ["❤️", "💕", "💖", "😍", "🥰", "✨"]

def send_message(chat_id, text):
    """Send message to Telegram"""
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload)
        logger.info(f"Message sent: {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

@app.route('/', methods=['GET'])
def home():
    """Home route for testing"""
    return jsonify({
        "status": "ok",
        "message": "Bot is running!",
        "bot_token_set": bool(BOT_TOKEN)
    })

@app.route('/', methods=['POST'])
def webhook():
    """Handle Telegram webhook"""
    try:
        # Get update from Telegram
        update = request.get_json()
        logger.info(f"Received update: {update.get('update_id') if update else 'None'}")
        
        if not update:
            return jsonify({"ok": False, "error": "No data"}), 200
        
        # Extract message info
        message = update.get('message', {})
        text = message.get('text', '')
        chat_id = message.get('chat', {}).get('id')
        user = message.get('from', {})
        name = user.get('first_name', 'Member')
        
        if not chat_id:
            return jsonify({"ok": True}), 200
        
        logger.info(f"Command: {text} from {name}")
        
        # Handle commands
        if text == '/start':
            response = "✅ *Bot Activated!*\n\nUse /tag to tag someone!\nUse /help for commands."
            send_message(chat_id, response)
            
        elif text == '/help':
            help_text = """
*🤖 Commands*
/start - Start bot
/tag - Tag yourself
/tag [name] - Tag someone
/help - Show this
            """
            send_message(chat_id, help_text)
            
        elif text.startswith('/tag'):
            # Parse tag name
            parts = text.split(' ', 1)
            tag_name = parts[1] if len(parts) > 1 else name
            
            # Generate message
            adjective = random.choice(ADJECTIVES)
            message_template = random.choice(MESSAGES)
            emoji = random.choice(EMOJIS)
            
            final_message = message_template.format(name=tag_name, adjective=adjective)
            final_message = f"{final_message} {emoji}"
            
            send_message(chat_id, final_message)
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"ok": True}), 200  # Always return 200 to Telegram

# This is for Vercel serverless
def handler(request):
    """Vercel serverless handler"""
    with app.request_context(request):
        return app.full_dispatch_request()