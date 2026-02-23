from http.server import BaseHTTPRequestHandler
import json
import os
import requests

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Simple GET handler"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "ok",
            "message": "Bot is alive!",
            "bot_token_set": bool(BOT_TOKEN)
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Simple POST handler"""
        try:
            # Read the request
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Parse update
            update = json.loads(post_data.decode('utf-8'))
            
            # Get chat ID
            chat_id = update.get('message', {}).get('chat', {}).get('id')
            
            if chat_id:
                # Send a simple response
                requests.post(
                    f"{TELEGRAM_API}/sendMessage",
                    json={
                        'chat_id': chat_id,
                        'text': '✅ Bot is working! Your command was received.'
                    }
                )
            
            # Always return 200 to Telegram
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            # Log error but still return 200
            print(f"Error: {e}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())