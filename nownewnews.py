import requests
import time
import threading
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from bs4 import BeautifulSoup
import re
import logging

# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with the token you received from BotFather
TELEGRAM_BOT_TOKEN = '7875384319:AAFA7sC1VR35WJ8Lo_MEMZ_iAGdgk-IZfsc'

# Replace 'YOUR_NEWSAPI_KEY' with your NewsAPI key
NEWSAPI_KEY = '73ab671c8d4d45f3aac58a057fd0a81a'

# Initialize the bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Data storage
keywords = set()  # Set of keywords for monitoring
favorite_news = []  # List of favorite news items
monitoring_interval = 600  # Default interval for monitoring in seconds
chat_id = None  # To store the chat ID for news updates

# Logger setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Add keywords
def add_keyword(update: Update, context: CallbackContext) -> None:
    global chat_id
    chat_id = update.message.chat_id  # Store chat ID for future use
    keywords_to_add = context.args
    if keywords_to_add:
        added_keywords = []
        for keyword in keywords_to_add:
            if keyword.lower() not in keywords:
                keywords.add(keyword.lower())
                added_keywords.append(keyword)
        if added_keywords:
            update.message.reply_text(f'Keywords added successfully: {", ".join(added_keywords)}')
        else:
            update.message.reply_text('No new keywords were added. They might already be in the list.')
    else:
        update.message.reply_text('Please provide at least one keyword to add.')

# Remove keywords
def remove_keyword(update: Update, context: CallbackContext) -> None:
    keywords_to_remove = context.args
    if keywords_to_remove:
        removed_keywords = []
        for keyword in keywords_to_remove:
            if keyword.lower() in keywords:
                keywords.remove(keyword.lower())
                removed_keywords.append(keyword)
        if removed_keywords:
            update.message.reply_text(f'Keywords removed successfully: {", ".join(removed_keywords)}')
        else:
            update.message.reply_text('No matching keywords found to remove.')
    else:
        update.message.reply_text('Please provide at least one keyword to remove.')

# List keywords
def list_keywords(update: Update, context: CallbackContext) -> None:
    if keywords:
        update.message.reply_text('Currently monitored keywords:\n' + '\n'.join(keywords))
    else:
        update.message.reply_text('No keywords are being monitored currently.')

# Mark news as favorite
def add_to_favorites(update: Update, context: CallbackContext) -> None:
    news_link = ' '.join(context.args)
    if news_link:
        favorite_news.append(news_link)
        update.message.reply_text('News added to favorites successfully!')
    else:
        update.message.reply_text('Please provide a valid news link to add to favorites.')

# List favorite news
def list_favorites(update: Update, context: CallbackContext) -> None:
    if favorite_news:
        update.message.reply_text('Favorite News:\n' + '\n'.join(favorite_news))
    else:
        update.message.reply_text('No news added to favorites yet.')

# Set monitoring interval
def set_interval(update: Update, context: CallbackContext) -> None:
    global monitoring_interval
    try:
        interval = int(context.args[0])
        monitoring_interval = interval
        update.message.reply_text(f'Monitoring interval set to {interval} seconds.')
    except (IndexError, ValueError):
        update.message.reply_text('Please provide a valid interval in seconds.')

# Monitor news using Google News and NewsAPI
def monitor_news():
    global chat_id
    while True:
        try:
            # Use NewsAPI to search for news articles containing the keywords
            for keyword in keywords:
                newsapi_url = f'https://newsapi.org/v2/everything?q={keyword}&apiKey={NEWSAPI_KEY}'
                response = requests.get(newsapi_url)
                if response.status_code == 200:
                    articles = response.json().get('articles', [])
                    for article in articles:
                        title = article.get('title')
                        url = article.get('url')
                        image = article.get('urlToImage')
                        if url and chat_id:
                            message = f'Found keyword "{keyword}" in:\n{title}\n{url}'
                            if image:
                                bot.send_photo(chat_id=chat_id, photo=image, caption=message)
                            else:
                                bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logging.error(f'Error occurred while monitoring news: {e}')
        time.sleep(monitoring_interval)  # Use dynamic interval

# Telegram command handlers
dispatcher.add_handler(CommandHandler('add_keyword', add_keyword))
dispatcher.add_handler(CommandHandler('remove_keyword', remove_keyword))
dispatcher.add_handler(CommandHandler('list_keywords', list_keywords))
dispatcher.add_handler(CommandHandler('add_to_favorites', add_to_favorites))
dispatcher.add_handler(CommandHandler('list_favorites', list_favorites))
dispatcher.add_handler(CommandHandler('set_interval', set_interval))

# Start the bot
if __name__ == '__main__':
    threading.Thread(target=monitor_news, daemon=True).start()  # Run monitor_news in a separate thread
    updater.start_polling()
