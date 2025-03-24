from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,filters,MessageHandler,ConversationHandler
import datetime
import os
import logging
from dotenv import load_dotenv



#AI 
from search_frequency import start_search_frequency,end,WAITING_FOR_FREQUENCY,find_frequency_bot
from upload_picture import get_credentials,find_or_create_folder
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
# Set up logging 
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#Define conversation states
FOLDER_NAME,UPLOAD_PHOTO = range(2)

async def start_upload(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Please enter the folder name for the pictures"
    )
    return FOLDER_NAME

async def get_folder_name(update:Update,context:ContextTypes.DEFAULT_TYPE):
    folder_name = update.message.text
    context.user_data['folder_name'] = folder_name

    await update.message.reply_text(f"Folder name set to: {folder_name}\nNow please send me the photo to upload.")
    return UPLOAD_PHOTO

async def handle_picture(update:Update,context:ContextTypes.DEFAULT_TYPE):
    try:
        folder_name = context.user_data.get('folder_name')

        # Get the largest photo size 
        photo = update.message.photo[-1]

        # Download the photo
        file = await context.bot.get_file(photo.file_id)
        temp_path = f"temp_{photo.file_id}.jpg"
        await file.download_to_drive(temp_path)

        # Upload to Google Drive
        creds = get_credentials()
        service = build('drive','v3',credentials=creds)

        # Find or create FM_BOT folder 
        parent_folder_id = find_or_create_folder(service,"FM_BOT")
        target_folder_id = find_or_create_folder(service, folder_name, parent_folder_id)

        file_metadata = {
        'name': f"photo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
        'parents': [target_folder_id]
        } 

        media = MediaFileUpload(
            temp_path,
            mimetype='image/jpeg',
            resumable=True
        )

        file = service.files().create(
           body = file_metadata,
           media_body=media,
           fields = 'id,name,webViewLink'
        ).execute()

        os.remove(temp_path)
        
        await update.message.reply_text(
            f"✅ Photo uploaded successfully!\n"
            f"Folder: {folder_name}\n"
            f"Link: {file.get('webViewLink')}\n\n"
            f"Send another photo to upload to the same folder, or use /start to choose a new folder."
        )
        return UPLOAD_PHOTO
    
    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}")
        await update.message.reply_text(
            "Sorry, there was an error uploading your photo. Please try again or use /start to restart."
        )
        return ConversationHandler.END
    
async def cancel(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Upload cancelled. Use /start to start a new upload."
    )
    return ConversationHandler.END
        

def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") 
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
            
    #Initialize the bot app  
    app = ApplicationBuilder().token(bot_token).build()

    #add upload picture conversation handler
    upload_handler = ConversationHandler(
        entry_points=[CommandHandler('upload',start_upload)],
        states={
            FOLDER_NAME:[MessageHandler(filters.TEXT & ~ filters.COMMAND,get_folder_name)],
            UPLOAD_PHOTO:[MessageHandler(filters.PHOTO,handle_picture),CommandHandler('cancel',cancel)]
        },
        fallbacks=[CommandHandler('cancel',cancel)]
    )
    app.add_handler(upload_handler)
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