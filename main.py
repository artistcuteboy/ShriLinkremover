import os
import logging
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import sqlite3
from datetime import datetime
from flask import Flask
import threading
import html

# Flask app for Render/Heroku
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Join Hider Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
SUPPORT_CHANNEL = os.environ.get("SUPPORT_CHANNEL", "@idxhelp")
ANIMATION_URL = os.environ.get("ANIMATION_URL", "https://files.catbox.moe/zvv7fa.gif")

# Database setup
def init_db():
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chats
                (chat_id INTEGER PRIMARY KEY, chat_title TEXT, added_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS broadcast
                (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, timestamp TEXT, 
                broadcast_type TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                joined_date TEXT)''')
    conn.commit()
    conn.close()

# Download GIF locally for better performance
def download_animation():
    try:
        # GIF download karein
        print(f"📥 Downloading GIF from environment variable...")
        print(f"📥 URL: {ANIMATION_URL}")
        
        if not ANIMATION_URL or ANIMATION_URL == "":
            print("❌ No animation URL provided in environment variables")
            return False
            
        try:
            if not os.path.exists('welcome.gif'):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(ANIMATION_URL, timeout=30, stream=True, headers=headers)
                if response.status_code == 200:
                    with open('welcome.gif', 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    print(f"✅ GIF downloaded successfully!")
                    return True
                else:
                    print(f"❌ Failed to download: Status {response.status_code}")
            else:
                print("✅ GIF already exists!")
                return True
                
        except Exception as e:
            print(f"❌ Error downloading GIF: {e}")
            
        # Agar download fail ho to static image bana lein
        if not os.path.exists('welcome.gif'):
            print("⚠️ Creating fallback image...")
            try:
                # Simple static image create karein
                from PIL import Image, ImageDraw, ImageFont
                
                img = Image.new('RGB', (400, 200), color='darkblue')
                d = ImageDraw.Draw(img)
                
                # Try to add text
                try:
                    font = ImageFont.truetype("arial.ttf", 30)
                except:
                    font = ImageFont.load_default()
                
                d.text((100, 80), "🤖 Join Hider Bot", fill='white', font=font)
                d.text((120, 120), "Welcome!", fill='yellow', font=font)
                
                img.save('welcome.gif')
                print("✅ Created fallback image!")
                return True
            except Exception as e:
                print(f"❌ Failed to create image: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Critical animation error: {e}")
        return False

# Combined welcome message with GIF and buttons
async def send_welcome_message(chat_id, context, chat_title=None, user_name=None, is_group=False, user_id=None):
    """Send combined welcome message with GIF and buttons"""
    try:
        # Welcome message text
        if is_group and chat_title:
            welcome_text = f"""
🎉 <b>Hello {html.escape(chat_title)}!</b>

🤖 <b>I'm Join Hider Bot</b> - Your friendly group assistant!

✅ <b>I will automatically hide all join/leave messages</b>
✅ <b>No more spammy notifications</b>
✅ <b>Clean chat experience</b>

<b>To get started:</b>
1️⃣ Make me admin in this group
2️⃣ Grant me delete message permission
3️⃣ I'll start working automatically!

<b>Support:</b> {SUPPORT_CHANNEL}
"""
            # Group welcome buttons
            keyboard = [
                [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                [InlineKeyboardButton("⚙️ Bot Settings", callback_data="group_settings"),
                 InlineKeyboardButton("🆘 Help", callback_data="help")]
            ]
            
        elif user_name:
            # Check if user is owner
            is_owner = (user_id == OWNER_ID)
            
            welcome_text = f"""
🎉 <b>Welcome to Join Hider Bot!</b>

Hello <b>{html.escape(user_name)}</b>! I will hide join/leave messages in your groups.

<b>Features:</b>
✅ Hide new member join messages
✅ Hide member leave messages

<b>Support Channel:</b> {SUPPORT_CHANNEL}
"""
            if is_owner:
                welcome_text += "\n<b>👑 Owner Panel:</b> You have access to admin features!"
            
            # Private chat buttons (different for owner and regular users)
            if is_owner:
                keyboard = [
                    [InlineKeyboardButton("📊 Stats", callback_data="stats"),
                     InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_menu")],
                    [InlineKeyboardButton("👥 Managed Groups", callback_data="chats"),
                     InlineKeyboardButton("🆘 Help", callback_data="help")],
                    [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                    [InlineKeyboardButton("👥 Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true")]
                ]
            else:
                keyboard = [
                    [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                    [InlineKeyboardButton("🆘 Help", callback_data="help"),
                     InlineKeyboardButton("👥 Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true")]
                ]
        else:
            welcome_text = f"""
🎉 <b>Welcome to Join Hider Bot!</b>

🤖 I will hide join/leave messages in your groups.

<b>Features:</b>
✅ Auto hide join/leave messages

<b>Support:</b> {SUPPORT_CHANNEL}
"""
            keyboard = [
                [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                [InlineKeyboardButton("🆘 Help", callback_data="help")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to send GIF with caption and buttons
        if os.path.exists('welcome.gif'):
            try:
                await context.bot.send_animation(
                    chat_id=chat_id,
                    animation=open('welcome.gif', 'rb'),
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return True
            except Exception as e:
                logger.error(f"GIF send error: {e}")
                # Fallback: Send GIF and message separately
                await context.bot.send_animation(
                    chat_id=chat_id,
                    animation=open('welcome.gif', 'rb')
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return True
        else:
            # Try to send from URL
            try:
                await context.bot.send_animation(
                    chat_id=chat_id,
                    animation=ANIMATION_URL,
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return True
            except Exception as e:
                logger.error(f"URL GIF error: {e}")
                # Send only text with buttons
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return True
                
    except Exception as e:
        logger.error(f"Welcome message error: {e}")
        # Last resort: simple text with buttons
        try:
            simple_keyboard = [
                [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                [InlineKeyboardButton("🆘 Help", callback_data="help")]
            ]
            simple_markup = InlineKeyboardMarkup(simple_keyboard)
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🎉 Welcome to Join Hider Bot!\n\nSupport: {SUPPORT_CHANNEL}",
                reply_markup=simple_markup
            )
            return True
        except:
            return False

# Start command - Combined GIF and welcome message with buttons
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    chat_type = update.effective_chat.type
    
    # User ko database me save karein (only in private chat)
    if chat_type == 'private':
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO users
                    (user_id, username, first_name, joined_date)
                    VALUES (?, ?, ?, ?)''',
                    (user_id, user.username, user.first_name, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    # Combined welcome message with GIF and buttons
    await send_welcome_message(
        chat_id=update.effective_chat.id,
        context=context,
        user_name=user.first_name,
        user_id=user_id,
        is_group=(chat_type != 'private')
    )

# Bot added to group handler
async def handle_group_events(update: Update, context: CallbackContext):
    try:
        if update.message:
            chat = update.message.chat
            chat_id = chat.id
            chat_title = chat.title or "Group"
            
            # Check for new chat members
            if update.message.new_chat_members:
                bot_added = False
                
                # Check if bot is among new members
                for member in update.message.new_chat_members:
                    if member.id == context.bot.id:
                        bot_added = True
                        break
                
                if bot_added:
                    # Bot was added to the group
                    logger.info(f"🤖 Bot added to group: {chat_title} ({chat_id})")
                    
                    # Store group info in database
                    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO chats (chat_id, chat_title, added_date) VALUES (?, ?, ?)",
                             (chat_id, chat_title, datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                    
                    # Send combined welcome message to group with buttons
                    await send_welcome_message(
                        chat_id=chat_id,
                        context=context,
                        chat_title=chat_title,
                        is_group=True
                    )
                    
                    # Notify owner
                    if OWNER_ID:
                        try:
                            notify_keyboard = [
                                [InlineKeyboardButton("👥 View Groups", callback_data="chats"),
                                 InlineKeyboardButton("📊 Stats", callback_data="stats")]
                            ]
                            notify_markup = InlineKeyboardMarkup(notify_keyboard)
                            
                            await context.bot.send_message(
                                chat_id=OWNER_ID,
                                text=f"✅ <b>Bot added to new group!</b>\n\n"
                                     f"<b>Group:</b> {html.escape(chat_title)}\n"
                                     f"<b>ID:</b> <code>{chat_id}</code>\n"
                                     f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                reply_markup=notify_markup,
                                parse_mode='HTML'
                            )
                        except Exception as e:
                            logger.error(f"Owner notification error: {e}")
                
                else:
                    # Regular users joined - hide their join message
                    try:
                        await update.message.delete()
                        logger.info(f"👥 Join message hidden in {chat_title}")
                        
                        # Ensure group is in database
                        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
                        c = conn.cursor()
                        c.execute("INSERT OR IGNORE INTO chats (chat_id, chat_title, added_date) VALUES (?, ?, ?)",
                                 (chat_id, chat_title, datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                        
                    except Exception as e:
                        logger.error(f"Delete join message error: {e}")
            
            # Check for left chat member
            elif update.message.left_chat_member:
                # Don't delete if it's the bot leaving
                if update.message.left_chat_member.id != context.bot.id:
                    try:
                        await update.message.delete()
                        logger.info(f"👋 Leave message hidden in {chat_title}")
                    except Exception as e:
                        logger.error(f"Delete leave message error: {e}")
                else:
                    # Bot was removed from group
                    logger.info(f"🤖 Bot removed from group: {chat_title} ({chat_id})")
                    
                    # Notify owner
                    if OWNER_ID:
                        try:
                            await context.bot.send_message(
                                chat_id=OWNER_ID,
                                text=f"❌ <b>Bot removed from group!</b>\n\n"
                                     f"<b>Group:</b> {html.escape(chat_title)}\n"
                                     f"<b>ID:</b> <code>{chat_id}</code>\n"
                                     f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                parse_mode='HTML'
                            )
                        except Exception as e:
                            logger.error(f"Owner notification error: {e}")
    
    except Exception as e:
        logger.error(f"Error in handle_group_events: {e}")

# Group settings callback
async def group_settings_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    chat = query.message.chat
    if chat.type in ['group', 'supergroup']:
        settings_text = f"""
<b>⚙️ Group Settings - {html.escape(chat.title)}</b>

<b>Group ID:</b> <code>{chat.id}</code>

<b>Bot Features:</b>
✅ Join messages hidden
✅ Leave messages hidden
✅ Welcome messages enabled

<b>Admin Commands:</b>
/settings - Show this menu
/start - Bot info

<b>Support:</b> {SUPPORT_CHANNEL}
"""
        
        keyboard = [
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(settings_text, reply_markup=reply_markup, parse_mode='HTML')

# Callback query handler
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "stats":
        if user_id != OWNER_ID:
            await query.message.reply_text("❌ Only owner can view statistics!")
            return
        
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM chats")
        chat_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM broadcast WHERE broadcast_type='groups'")
        group_broadcast_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM broadcast WHERE broadcast_type='users'")
        user_broadcast_count = c.fetchone()[0]
        conn.close()
        
        stats_text = f"""
<b>📊 Bot Statistics</b>

<b>👥 Managed Groups:</b> {chat_count}
<b>👤 Total Users:</b> {user_count}
<b>📢 Group Broadcasts Sent:</b> {group_broadcast_count}
<b>📢 User Broadcasts Sent:</b> {user_broadcast_count}

<b>🆔 Owner ID:</b> {OWNER_ID}
<b>🔧 Status:</b> ✅ Running
<b>💡 Support:</b> {SUPPORT_CHANNEL}
"""
        keyboard = [
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(stats_text, reply_markup=reply_markup, parse_mode='HTML')
    
    elif data == "chats":
        if user_id != OWNER_ID:
            await query.message.reply_text("❌ Only owner can view managed chats!")
            return
        
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT chat_id, chat_title, added_date FROM chats ORDER BY added_date DESC")
        chats = c.fetchall()
        conn.close()
        
        if chats:
            chat_list = "\n".join([f"• {html.escape(title)} (<code>{cid}</code>) - {added_date.split('T')[0]}" 
                                  for cid, title, added_date in chats[:50]])
            if len(chats) > 50:
                chat_list += f"\n\n... and {len(chats)-50} more groups"
            text = f"<b>👥 Managed Chats</b>\n\n{chat_list}"
        else:
            text = "❌ No chats managed yet.\nAdd me to a group and make me admin!"
        
        keyboard = [
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    elif data == "group_settings":
        # Group settings callback
        chat = query.message.chat
        if chat.type in ['group', 'supergroup']:
            settings_text = f"""
<b>⚙️ Group Settings - {html.escape(chat.title)}</b>

<b>Bot Features:</b>
✅ Join messages hidden
✅ Leave messages hidden
✅ Welcome messages enabled

<b>Commands:</b>
/settings - Show settings
/start - Bot info

<b>Support:</b> {SUPPORT_CHANNEL}
"""
            keyboard = [
                [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(settings_text, reply_markup=reply_markup, parse_mode='HTML')
    
    elif data == "gbroadcast_menu":
        if user_id != OWNER_ID:
            await query.message.reply_text("❌ Only owner can broadcast messages!")
            return
        
        await query.message.edit_text(
            f"<b>📢 Broadcast to Groups</b>\n\n"
            f"Please use command:\n"
            f"<code>/gbroadcast your_message_here</code>\n\n"
            f"<b>Example:</b>\n"
            f"<code>/gbroadcast Hello groups! New update available.</code>\n\n"
            f"<b>Support Channel:</b> {SUPPORT_CHANNEL}",
            parse_mode='HTML'
        )
    
    elif data == "broadcast_menu":
        if user_id != OWNER_ID:
            await query.message.reply_text("❌ Only owner can broadcast messages!")
            return
        
        await query.message.edit_text(
            f"<b>📢 Broadcast to Users</b>\n\n"
            f"Please use command:\n"
            f"<code>/broadcast your_message_here</code>\n\n"
            f"<b>Example:</b>\n"
            f"<code>/broadcast Hello users! Check out new features.</code>\n\n"
            f"<b>Support Channel:</b> {SUPPORT_CHANNEL}",
            parse_mode='HTML'
        )
    
    elif data == "help":
        help_text = f"""
<b>🆘 Help Guide</b>

<b>How to use this bot:</b>
1. Add me to your group
2. Make me admin with delete permissions
3. I'll automatically hide join/leave messages

<b>Owner Commands:</b>
/start - Bot menu
/stats - View statistics

<b>Support:</b>
If you need help, join our support channel: {SUPPORT_CHANNEL}

<b>Features:</b>
• Auto hide join messages
• Auto hide leave messages
"""
        keyboard = [
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(help_text, reply_markup=reply_markup, parse_mode='HTML')
    
    elif data == "back":
        # Send welcome message again
        user = query.from_user
        await send_welcome_message(
            chat_id=query.message.chat.id,
            context=context,
            user_name=user.first_name,
            user_id=user.id,
            is_group=(query.message.chat.type != 'private')
        )
        # Delete the previous message
        try:
            await query.message.delete()
        except:
            pass

# Broadcast commands (same as before)
async def gbroadcast_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text(
            f"❌ Only owner can use this command.\n\n"
            f"💡 Support: {SUPPORT_CHANNEL}"
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            f"<b>📢 Usage:</b> /gbroadcast your_message_here\n\n"
            f"<b>Example:</b> /gbroadcast Hello everyone! New update available.\n\n"
            f"💡 Support: {SUPPORT_CHANNEL}",
            parse_mode='HTML'
        )
        return
    
    message = " ".join(context.args)
    
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT chat_id, chat_title FROM chats")
    chats = c.fetchall()
    conn.close()
    
    if not chats:
        await update.message.reply_text("❌ No groups found to broadcast!")
        return
    
    success = 0
    failed = 0
    
    processing_msg = await update.message.reply_text(
        f"🔄 Broadcasting to {len(chats)} groups...\n"
        f"Please wait..."
    )
    
    for chat_id, chat_title in chats:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{html.escape(message)}",
                parse_mode='HTML'
            )
            success += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Broadcast failed for {chat_title} ({chat_id}): {e}")
            failed += 1
    
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO broadcast (message, timestamp, broadcast_type) VALUES (?, ?, ?)",
              (message, datetime.now().isoformat(), "groups"))
    conn.commit()
    conn.close()
    
    await processing_msg.edit_text(
        f"<b>✅ Broadcast Complete</b>\n\n"
        f"<b>Total Groups:</b> {len(chats)}\n"
        f"<b>Successful:</b> {success}\n"
        f"<b>Failed:</b> {failed}\n\n"
        f"💡 Support: {SUPPORT_CHANNEL}",
        parse_mode='HTML'
    )

async def broadcast_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text(
            f"❌ Only owner can use this command.\n\n"
            f"💡 Support: {SUPPORT_CHANNEL}"
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            f"<b>📢 Usage:</b> /broadcast your_message_here\n\n"
            f"<b>Example:</b> /broadcast Hello users! New features added.\n\n"
            f"💡 Support: {SUPPORT_CHANNEL}",
            parse_mode='HTML'
        )
        return
    
    message = " ".join(context.args)
    
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT user_id, username FROM users")
    users = c.fetchall()
    conn.close()
    
    if not users:
        await update.message.reply_text("❌ No users found to broadcast!")
        return
    
    success = 0
    failed = 0
    
    processing_msg = await update.message.reply_text(
        f"🔄 Broadcasting to {len(users)} users...\n"
        f"Please wait..."
    )
    
    for user_id, username in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"{html.escape(message)}",
                parse_mode='HTML'
            )
            success += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Broadcast failed for user {username} ({user_id}): {e}")
            failed += 1
    
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO broadcast (message, timestamp, broadcast_type) VALUES (?, ?, ?)",
              (message, datetime.now().isoformat(), "users"))
    conn.commit()
    conn.close()
    
    await processing_msg.edit_text(
        f"<b>✅ Broadcast Complete</b>\n\n"
        f"<b>Total Users:</b> {len(users)}\n"
        f"<b>Successful:</b> {success}\n"
        f"<b>Failed:</b> {failed}\n\n"
        f"💡 Support: {SUPPORT_CHANNEL}",
        parse_mode='HTML'
    )

# Other commands
async def stats_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if user_id == OWNER_ID:
        conn = sqlite3.connect('bot_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM chats")
        chat_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        conn.close()
        
        await update.message.reply_text(
            f"<b>📊 Statistics</b>\n\n"
            f"• <b>Managed Groups:</b> {chat_count}\n"
            f"• <b>Total Users:</b> {user_count}\n"
            f"• <b>Support:</b> {SUPPORT_CHANNEL}",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"❌ Only owner can view statistics.\n\n"
            f"💡 Support: {SUPPORT_CHANNEL}"
        )

async def settings(update: Update, context: CallbackContext):
    chat = update.effective_chat
    
    if chat.type in ['group', 'supergroup']:
        # Group settings with buttons
        settings_text = f"""
<b>⚙️ Group Settings - {html.escape(chat.title)}</b>

<b>Group ID:</b> <code>{chat.id}</code>

<b>Bot Features:</b>
✅ Join messages hidden
✅ Leave messages hidden
✅ Welcome messages enabled

<b>Support:</b> {SUPPORT_CHANNEL}
"""
        keyboard = [
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL[1:]}")],
            [InlineKeyboardButton("🆘 Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(
            f"ℹ️ This command works only in groups!\n\n"
            f"Add me to a group and make me admin to use this feature.\n\n"
            f"<b>Support:</b> {SUPPORT_CHANNEL}",
            parse_mode='HTML'
        )

async def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Error: {context.error}")

def main():
    # Bot token check
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable not set!")
        print("Please set BOT_TOKEN environment variable.")
        return
    
    if OWNER_ID == 0:
        print("⚠️ WARNING: OWNER_ID not set. Owner features will not work.")
    
    # Check animation URL
    if not ANIMATION_URL or ANIMATION_URL == "":
        print("⚠️ WARNING: ANIMATION_URL not set. Using default URL.")
    
    # Download GIF
    download_animation()
    
    # Initialize database
    init_db()
    
    # Start Flask server
    try:
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print("🌐 Flask server started on port 8080")
    except Exception as e:
        print(f"⚠️ Flask server error: {e}")
    
    # Create bot application
    print("🔄 Creating bot application...")
    
    # Pehle webhook delete karein
    try:
        import telegram
        bot = telegram.Bot(token=BOT_TOKEN)
        bot.delete_webhook()
        print("✅ Webhook deleted (if any)")
    except Exception as e:
        print(f"⚠️ Webhook deletion error: {e}")
    
    # Application create karein
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("gbroadcast", gbroadcast_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("settings", settings))
    
    # Group events handler
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER,
        handle_group_events
    ))
    
    # Callback query handler (including group_settings)
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("🤖 Bot starting...")
    print(f"📢 Support Channel: {SUPPORT_CHANNEL}")
    print(f"👤 Owner ID: {OWNER_ID}")
    print(f"🎥 Animation URL: {ANIMATION_URL}")
    print(f"🎥 GIF File: {'Available' if os.path.exists('welcome.gif') else 'Not available'}")
    print("✅ Ready to receive updates...")
    
    # Run bot
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == '__main__':
    main()
