from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get bot token
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
logger.info(f"BOT_TOKEN set: {bool(BOT_TOKEN)}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests - for testing"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "ok",
                "message": "Bot is running!",
                "bot_token_set": bool(BOT_TOKEN),
                "python_version": sys.version
            }
            
            self.wfile.write(json.dumps(response).encode())
            logger.info("GET request handled successfully")
            
        except Exception as e:
            logger.error(f"GET error: {e}")
            self.send_error(500, str(e))
    
    def do_POST(self):
        """Handle POST requests - Telegram webhook"""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read the request body
            post_data = self.rfile.read(content_length)
            
            # Log received data
            logger.info(f"Received POST with length: {content_length}")
            
            # Parse JSON
            try:
                update = json.loads(post_data.decode('utf-8'))
                logger.info(f"Update ID: {update.get('update_id', 'unknown')}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
                return
            
            # Here you would process the Telegram update
            # For now, just acknowledge
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {"ok": True, "message": "Update received"}
            self.wfile.write(json.dumps(response).encode())
            
            logger.info("POST request handled successfully")
            
        except Exception as e:
            logger.error(f"POST error: {e}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")