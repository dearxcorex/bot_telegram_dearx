from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,filters,MessageHandler,ConversationHandler
import datetime
import os
import logging
from dotenv import load_dotenv



#AI 
from search_frequency import frequency_search

# Set up logging 
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") 
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
            
    #Initialize the bot app  
    app = ApplicationBuilder().token(bot_token).build()
    conv_hanler = ConversationHandler(
        entry_points=[CommandHandler('freq',frequency_search.start_search_frequency)],
        states={
            frequency_search.WAITING_FOR_FREQUENCY:[MessageHandler(filters.TEXT & ~ filters.COMMAND,frequency_search.find_frequency_bot)]
        },
        fallbacks=[CommandHandler('end',frequency_search.end)]
    )
    app.add_handler(conv_hanler)
    
    #start the bot 
    logger.info("Bot starting bot")
    app.run_polling()





if __name__ == "__main__":
    main()  