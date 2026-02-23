from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import random
import os
import asyncio
import json

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set in environment variables!")

# Store active groups (using a simple set for demo)
# In production, use a database
active_groups = set()

# Funny and romantic Hinglish messages
MESSAGES = [
    "Hey {name} ❤️, tu toh bilkul {adjective} lag raha/rahi hai aaj!",
    "{name} 😍, teri smile ne mera dil chura liya!",
    "Oye {name} ✨, teri beauty ka koi answer nahi!",
    "{name} ji 💕, aapke liye ek special tag!",
    "Sun {name} 🌟, tu mere group ka sabse pyara member hai!",
    "Bhai {name} 🚀, tu aaya to group mein jaan aa gayi!",
    "{name} 😂, tera intezaar tha ki nahi?",
    "{name} 🌹, tujhe dekh ke dil garden garden ho gaya!",
]

ADJECTIVES = [
    "ekdum jhakaas", "superb", "awesome", "mast", "cool", 
    "dhamakedar", "rocking", "fantastic", "amazing",
    "pyaara", "sweet", "lovely", "cute"
]

EMOJIS = ["❤️", "💕", "💖", "😍", "🥰", "😘", "✨", "🌟"]

# Initialize bot and application
bot_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    chat_id = update.effective_chat.id
    
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ This command only works in groups!")
        return
    
    active_groups.add(chat_id)
    
    await update.message.reply_text(
        "✅ *Auto-Tagger Activated!*\n\n"
        "Use /tag to tag a random member!\n"
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
        # Get chat administrators
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
    status_text = "🟢 Active" if chat_id in active_groups else "🔴 Inactive"
    
    await update.message.reply_text(
        f"*Bot Status:* {status_text}\n\n"
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

# Initialize the bot application
def init_bot():
    global bot_app
    if not bot_app and BOT_TOKEN:
        bot_app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("stop", stop))
        bot_app.add_handler(CommandHandler("tag", tag_someone))
        bot_app.add_handler(CommandHandler("status", status))
        bot_app.add_handler(CommandHandler("help", help_command))
        
        logger.info("Bot application initialized")
    return bot_app

# Vercel serverless handler
async def handler(request):
    """Main handler for Vercel"""
    try:
        # Handle GET request (for testing)
        if request.method == "GET":
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "status": "ok",
                    "message": "Bot is running!",
                    "bot_token_set": bool(BOT_TOKEN)
                })
            }
        
        # Handle POST request (Telegram webhook)
        if request.method == "POST":
            # Parse request body
            try:
                body = await request.json()
                logger.info(f"Received update: {body.get('update_id')}")
                
                # Initialize bot if needed
                bot_app = init_bot()
                if not bot_app or not BOT_TOKEN:
                    return {
                        "statusCode": 500,
                        "body": json.dumps({"error": "Bot not initialized"})
                    }
                
                # Create update object
                update = Update.de_json(body, bot_app.bot)
                
                # Process update
                await bot_app.process_update(update)
                
                return {
                    "statusCode": 200,
                    "body": json.dumps({"ok": True})
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
