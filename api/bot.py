from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import random
import os
import json
from http.server import BaseHTTPRequestHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set in environment variables!")

# Store active groups
active_groups = set()

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

# Initialize bot and application
application = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    active_groups.add(chat_id)
    
    await update.message.reply_text(
        "✅ *Auto-Tagger Activated!*\n\n"
        "I'll tag members when you use /tag command!\n"
        "Use /help to see all commands.",
        parse_mode='Markdown'
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop command handler"""
    chat_id = update.effective_chat.id
    active_groups.discard(chat_id)
    
    await update.message.reply_text(
        "🛑 *Auto-Tagger Deactivated!*",
        parse_mode='Markdown'
    )

async def tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag a random member"""
    chat_id = update.effective_chat.id
    
    try:
        # Get chat admins
        admins = await context.bot.get_chat_administrators(chat_id)
        
        # Filter out bots
        valid_users = [admin.user for admin in admins if not admin.user.is_bot]
        
        if valid_users:
            user = random.choice(valid_users)
            name = user.first_name or "Member"
            
            # Create message
            adjective = random.choice(ADJECTIVES)
            message = random.choice(MESSAGES).format(name=name, adjective=adjective)
            emoji = random.choice(EMOJIS)
            
            # Create mention
            if user.username:
                tag_text = f"@{user.username} {message} {emoji}"
            else:
                tag_text = f"{name} {message} {emoji}"
            
            await update.message.reply_text(tag_text)
        else:
            await update.message.reply_text("No members found to tag!")
            
    except Exception as e:
        logger.error(f"Error in tag: {e}")
        await update.message.reply_text("❌ Error tagging member!")

async def tag_someone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag a specific person"""
    if context.args:
        name = ' '.join(context.args)
        adjective = random.choice(ADJECTIVES)
        message = random.choice(MESSAGES).format(name=name, adjective=adjective)
        emoji = random.choice(EMOJIS)
        
        await update.message.reply_text(f"{message} {emoji}")
    else:
        await tag(update, context)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check status"""
    chat_id = update.effective_chat.id
    status = "🟢 Active" if chat_id in active_groups else "🔴 Inactive"
    
    await update.message.reply_text(
        f"*Bot Status:* {status}\n\n"
        f"Commands:\n"
        f"/start - Activate bot\n"
        f"/stop - Deactivate bot\n"
        f"/tag - Tag random member\n"
        f"/tag [name] - Tag someone\n"
        f"/help - Show help",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    help_text = """
*🤖 Auto-Tagger Bot Commands*

• /start - Activate bot in group
• /stop - Deactivate bot
• /tag - Tag random member
• /tag [name] - Tag specific person
• /status - Check bot status
• /help - Show this menu

*Features:*
✨ Hinglish messages
💕 Romantic & funny
🎭 Different every time

*Setup:*
1. Add bot to group
2. Make bot admin
3. Send /start
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Vercel serverless function handler
def handler(request):
    """Main handler for Vercel"""
    global application
    
    try:
        # Handle GET request (for testing)
        if request.method == "GET":
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Bot is running!",
                    "status": "active",
                    "bot_token_set": bool(BOT_TOKEN)
                })
            }
        
        # Handle POST request (Telegram webhook)
        if request.method == "POST":
            # Get request body
            try:
                body = request.body
                if isinstance(body, bytes):
                    body = body.decode('utf-8')
                
                update_data = json.loads(body)
                logger.info(f"Received update: {update_data.get('update_id')}")
                
                # Initialize application if needed
                global application
                if not application and BOT_TOKEN:
                    application = Application.builder().token(BOT_TOKEN).build()
                    
                    # Add handlers
                    application.add_handler(CommandHandler("start", start))
                    application.add_handler(CommandHandler("stop", stop))
                    application.add_handler(CommandHandler("tag", tag_someone))
                    application.add_handler(CommandHandler("status", status))
                    application.add_handler(CommandHandler("help", help_command))
                
                if application and BOT_TOKEN:
                    # Process update
                    import asyncio
                    
                    # Create event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Create update object
                    update = Update.de_json(update_data, application.bot)
                    
                    # Process update
                    loop.run_until_complete(application.process_update(update))
                    loop.close()
                    
                    return {
                        "statusCode": 200,
                        "body": json.dumps({"ok": True})
                    }
                else:
                    return {
                        "statusCode": 500,
                        "body": json.dumps({
                            "error": "Bot not initialized",
                            "bot_token_set": bool(BOT_TOKEN)
                        })
                    }
                    
            except Exception as e:
                logger.error(f"Error processing update: {e}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": str(e)})
                }
        
        # Handle other methods
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"})
        }
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }