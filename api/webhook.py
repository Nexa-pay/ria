from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import logging
import random
import requests
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get bot token
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Funny and romantic Hinglish messages
MESSAGES = [
    "Hey {name} ❤️, tu toh bilkul {adjective} lag raha/rahi hai aaj!",
    "{name} 😍, teri smile ne mera dil chura liya!",
    "Oye {name} ✨, teri beauty ka koi answer nahi!",
    "{name} ji 💕, aapke liye ek special tag!",
    "Sun {name} 🌟, tu mere group ka sabse pyara member hai!",
    "{name} baby 😘, miss you in the group!",
    "Bhai {name} 🚀, tu aaya to group mein jaan aa gayi!",
    "{name} 😂, tera intezaar tha ki nahi?",
    "Oye {name} 🎭, tu toh famous ho gaya hai group mein!",
    "{name} 🌹, tujhe dekh ke dil garden garden ho gaya!",
]

ADJECTIVES = [
    "ekdum jhakaas", "superb", "awesome", "mast", "cool", 
    "dhamakedar", "rocking", "fantastic", "amazing",
    "pyaara", "sweet", "lovely", "cute", "handsome"
]

EMOJIS = ["❤️", "💕", "💖", "😍", "🥰", "😘", "✨", "🌟", "⭐"]

def send_message(chat_id, text):
    """Send message to Telegram"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        logger.debug(f"Sending message to {chat_id}: {text[:50]}...")
        response = requests.post(url, json=payload, timeout=10)
        logger.debug(f"Send message response: {response.status_code} - {response.text[:100]}")
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def handle_command(update):
    """Handle bot commands"""
    try:
        logger.debug(f"Received update: {json.dumps(update)[:200]}...")
        
        message = update.get('message', {})
        text = message.get('text', '')
        chat_id = message.get('chat', {}).get('id')
        user = message.get('from', {})
        name = user.get('first_name', 'Member')
        
        if not chat_id:
            logger.warning("No chat_id in update")
            return
        
        logger.info(f"Processing command: '{text}' from user {name} in chat {chat_id}")
        
        # Handle commands
        if text == '/start':
            response = "✅ *Auto-Tagger Activated!*\n\nUse /tag to tag someone!\nUse /help for commands."
            send_message(chat_id, response)
            
        elif text == '/help':
            help_text = """
*🤖 Auto-Tagger Commands*

• /start - Activate bot
• /tag - Tag random member
• /tag [name] - Tag someone
• /help - Show this menu

*Features:*
✨ Hinglish messages
💕 Romantic & funny
🎭 Different every time
            """
            send_message(chat_id, help_text)
            
        elif text.startswith('/tag'):
            # Parse tag command
            parts = text.split(' ', 1)
            if len(parts) > 1:
                tag_name = parts[1]
            else:
                tag_name = name
            
            # Generate message
            adjective = random.choice(ADJECTIVES)
            message_template = random.choice(MESSAGES)
            emoji = random.choice(EMOJIS)
            
            final_message = message_template.format(name=tag_name, adjective=adjective)
            final_message = f"{final_message} {emoji}"
            
            send_message(chat_id, final_message)
            
        else:
            logger.debug(f"Unknown command: {text}")
            
    except Exception as e:
        logger.error(f"Error in handle_command: {e}\n{traceback.format_exc()}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests - for testing"""
        try:
            logger.info(f"GET request from {self.client_address}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "ok",
                "message": "🤖 Auto-Tagger Bot is running!",
                "bot_token_set": bool(BOT_TOKEN),
                "python_version": sys.version
            }
            
            self.wfile.write(json.dumps(response).encode())
            logger.info("GET request handled successfully")
            
        except Exception as e:
            logger.error(f"GET error: {e}\n{traceback.format_exc()}")
            self.send_error(500, str(e))
    
    def do_POST(self):
        """Handle POST requests - Telegram webhook"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parse update
            update = json.loads(post_data.decode('utf-8'))
            logger.info(f"Received POST update: {update.get('update_id')}")
            
            # Handle the update
            handle_command(update)
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {"ok": True}
            self.wfile.write(json.dumps(response).encode())
            
            logger.info("POST request handled successfully")
            
        except Exception as e:
            logger.error(f"POST error: {e}\n{traceback.format_exc()}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")