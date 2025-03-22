from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,filters,MessageHandler,ConversationHandler
import datetime
import os
import logging
from dotenv import load_dotenv



#AI 
from search_frequency import start_search_frequency,end,WAITING_FOR_FREQUENCY,find_frequency_bot

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
        entry_points=[CommandHandler('freq',start_search_frequency)],
        states={
            WAITING_FOR_FREQUENCY:[MessageHandler(filters.TEXT & ~ filters.COMMAND,find_frequency_bot)]
        },
        fallbacks=[CommandHandler('end',end)]
    )
    app.add_handler(conv_hanler)
    
    #start the bot 
    logger.info("Bot starting bot")
    app.run_polling()





if __name__ == "__main__":
    main()  