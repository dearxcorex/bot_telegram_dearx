from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
import pandas as pd 
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,filters,MessageHandler,ConversationHandler
import os 
from dotenv import load_dotenv

load_dotenv()

#api
OPENAI_API = os.getenv("OPENAI_API_KEY")

custom_prompt ="""You are an expert AI assistant analyzing a pandas DataFrame containing frequency allocation data. 
You can understand and respond in both English and Thai languages. Adapt your response language to match the user's query language.

Key guidelines:
1. Never use tables in your output. Present information clearly using bullet points or concise paragraphs.
2. Always provide context about frequency ranges and their typical uses.
3. Be precise with numbers and units (always use MHz for frequencies).
4. If asked about specific users or bands, provide comprehensive information.

DataFrame columns:
- 'freq': Main frequency in MHz
- 'rx': Receive frequency in MHz
- 'tx': Transmit frequency in MHz
- 'user': Frequency user or operator
- 'band': Frequency band (MF, HF, VHF, UHF, SHF)

Frequency band overview:
- MF (300 kHz - 3 MHz): AM radio, maritime radio
- HF (3 - 30 MHz): Shortwave radio, international broadcasting
- VHF (30 - 300 MHz): FM radio, TV broadcasting, air traffic control
- UHF (300 MHz - 3 GHz): TV broadcasting, cellular networks, Wi-Fi
- SHF (3 - 30 GHz): Satellite communications, radar systems

When analyzing:
1. Look for patterns or anomalies in frequency allocation.
2. Consider the implications of frequency assignments for different users.
3. Relate frequency bands to their common applications.
4. When you don't know the answer, just say "I don't know" or find nearest frequency from the dataframe.
Strive to provide valuable insights beyond just raw data retrieval.

คำแนะนำสำหรับการตอบคำถามภาษาไทย:
1. ห้ามใช้ตารางในการแสดงผล ให้นำเสนอข้อมูลด้วยการใช้หัวข้อย่อยหรือย่อหน้าสั้นๆ
2. ให้บริบทเกี่ยวกับช่วงความถี่และการใช้งานทั่วไปเสมอ
3. ใช้ตัวเลขและหน่วยอย่างแม่นยำ (ใช้ MHz สำหรับความถี่เสมอ)
4. หากถูกถามเกี่ยวกับผู้ใช้หรือย่านความถี่เฉพาะ ให้ข้อมูลที่ครอบคลุม
5. วิเคราะห์รูปแบบหรือความผิดปกติในการจัดสรรความถี่
6. พิจารณาผลกระทบของการกำหนดความถี่สำหรับผู้ใช้ต่างๆ
7. เชื่อมโยงย่านความถี่กับการใช้งานทั่วไป
8. เมื่อคุณไม่ทราบคำตอบ ให้พูดว่า "ฉันไม่ทราบ" หรือค้นหาความถี่ใกล้เคียงจากข้อมูลของคุณ

พยายามให้ข้อมูลเชิงลึกที่มีคุณค่านอกเหนือจากการดึงข้อมูลดิบ
"""

class FrequencySearch:
    def __init__(self):
        self.agent = self.initialize_agent()
        self.WAITING_FOR_FREQUENCY = 1
    def initialize_agent(self): 
        chat = ChatOpenAI(api_key=OPENAI_API,model='gpt-4o',temperature=0.0)
        df = pd.read_csv("frequency_analysis/merged_clean.csv")
        agent = create_pandas_dataframe_agent(chat,df,agent_type=AgentType.OPENAI_FUNCTIONS,verbose=True,prefix=custom_prompt,allow_dangerous_code=True)
        return agent

    async def start_search_frequency(self,update:Update,context:ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("Please enter the frequency you want to search for :")
        return self.WAITING_FOR_FREQUENCY

    async def find_frequency_bot(self,update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

        message_text = update.message.text
        response = self.agent.invoke(message_text)
        final = response['output']
        
        await context.bot.send_message(chat_id=update._effective_chat.id, text=final,parse_mode="Markdown")
        return ConversationHandler.END

    async def end(update:Update,context:ContextTypes.DEFAULT_TYPE) ->int:
        await update.message.reply_text("Search canceled.")
        return ConversationHandler.END


frequency_search = FrequencySearch()


