from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,filters,MessageHandler,ConversationHandler
import datetime
import os
import logging
from dotenv import load_dotenv



#google calendar
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#AI 
from search_frequency import frequency_search

# Set up logging 
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#api
OPENAI_API = os.getenv("OPENAI_API_KEY")

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

async def google_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    creds = None 

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json",SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json","w") as token:
            token.write(creds.to_json())
    try:
        service = build("calendar","v3",credentials=creds)


        # Call The Calender API 
        now = datetime.datetime.now().isoformat() + "Z"
        print("getting strating") 

        event_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin = now,
                maxResults = 5,
                singleEvents = True,
                orderBy = "startTime",
            )
            .execute()
        )
        events = event_result.get("items",[])

        if not events:
            await update.message.reply_text('No upcoming event found.')             

        else:
            event_list = "Upcoming events:\n"
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                event_list += f"{start} - {event['summary']} \n"
            await update.message.reply_text(event_list) 
    except HttpError as error:
        logger.error(f"An error occurred: {error}")
        await update.message.reply_text("An error occurred while accessing google calendar.")


def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") 
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
            
    #Initialize the bot app  
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("task", google_calendar))
    conv_hanler = ConversationHandler(
        entry_points=[CommandHandler('freq',frequency_search.start_search_frequency)],
        states={
            frequency_search.WAITING_FOR_FREQUENCY:[MessageHandler(filters.TEXT & ~ filters.COMMAND,frequency_search.find_frequency_bot)]
        },
        fallbacks=[CommandHandler('end',frequency_search.end)]
    )
    app.add_handler(conv_hanler)
    # app.add_handler(CommandHandler("freq",find_frequency_bot))
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, find_frequency_bot))
    #start the bot 
    logger.info("Bot starting bot")
    app.run_polling()





if __name__ == "__main__":
    main()  