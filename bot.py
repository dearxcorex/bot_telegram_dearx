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
import pandas as pd 
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI



# Set up logging 
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#api
OPENAI_API = os.getenv("OPENAI_API_KEY")

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
# Define states
WAITING_FOR_FREQUENCY = 1


#set up  openai and langchain 
chat = ChatOpenAI(api_key=OPENAI_API,model='gpt-4o',temperature=0.0)
df = pd.read_csv("frequency_analysis/merged.csv",index_col=0)
agent = create_pandas_dataframe_agent(chat,df,agent_type=AgentType.OPENAI_FUNCTIONS,verbose=True,allow_dangerous_code=True)


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




async def start_search_frequency(update:Update,context:ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please enter the frequency you want to search for :")
    return WAITING_FOR_FREQUENCY

async def find_frequency_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:



    message_text = update.message.text
    response = agent.invoke(f"Find rows where 'คลื่นความถี่ (MHz)' is {message_text}")
    final = response['output']
    
    await context.bot.send_message(chat_id=update._effective_chat.id, text=final,parse_mode="Markdown")
    return ConversationHandler.END

async def end(update:Update,context:ContextTypes.DEFAULT_TYPE) ->int:
    await update.message.reply_text("Search canceled.")
    return ConversationHandler.END

def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") 
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
            
    #Initialize the bot app  
    app = ApplicationBuilder().token(bot_token).build()
    app.add_handler(CommandHandler("task", google_calendar))
    conv_hanler = ConversationHandler(
        entry_points=[CommandHandler('freq',start_search_frequency)],
        states={
            WAITING_FOR_FREQUENCY:[MessageHandler(filters.TEXT & ~ filters.COMMAND,find_frequency_bot)]
        },
        fallbacks=[CommandHandler('end',end)]
    )
    app.add_handler(conv_hanler)
    # app.add_handler(CommandHandler("freq",find_frequency_bot))
    # app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, find_frequency_bot))
    #start the bot 
    logger.info("Bot starting bot")
    app.run_polling()





if __name__ == "__main__":
    main()  