from telegram import Update
from typing import Annotated
from langgraph.prebuilt import ToolNode,tools_condition
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
import pandas as pd
from telegram.ext import ContextTypes
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
load_dotenv()   
#https://colab.research.google.com/drive/14ncV0nviLcP9IDzmFSRGSXb7Bgpz212v?usp=sharing
#load csv 
# States of conversation
WAITING_FOR_FREQUENCY = 1
path = "frequency_analysis/merged_clean.csv"

df = pd.read_csv(path)

class FrequencySearch(BaseModel):
    freq: float
    user: str
    freq_range:list[float,float] = Field(default=[137,174])

    
class State(TypedDict):
    messages: Annotated[list, add_messages]


async def start_search_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the frequency search conversation."""
    await update.message.reply_text(
        "Please enter a user name to search for frequencies.\n"
        "Example: กรมการสื่อสารทหาร"
    )
    return WAITING_FOR_FREQUENCY



def search_frequency(query:FrequencySearch) -> pd.DataFrame:
    """Search for a frequency in the dataframe if not found return nearest frequency.
    Args:
        freq: Frequency to search for
    """
    q = query.freq
    mask = df[df["freq"] == q]
    if not mask.empty:
        return mask
    else: 
        return df.iloc[(df["freq"] - q).abs().argsort()[:5]]

def search_frequency_user(query:FrequencySearch) -> pd.DataFrame:
    """Search for a frequency user in the dataframe.
    Args:
        user: User to search for
        freq: Frequency to search range 
    """
    q = query.user
    f = query.freq_range
    mask = (df["freq"] >= f[0]) & (df["freq"] <= f[1]) & (df["user"] == q)

    return df[mask]

tools = [search_frequency,search_frequency_user]
model = ChatOpenAI(model="gpt-4o-mini",temperature=0)
llm_with_tools = model.bind_tools(tools)


prompt = """
You are a filter frequency dataframe app.
You are given a frequency and you need to find the nearest frequency or user column in the dataframe. If the frequency is not found, you need to return the nearest 5 frequency and  column user from the dataframe.
if user spell user frequency wrong, you need to correct the user frequency input.
"""
sys_msg = SystemMessage(content=prompt)

def chatbot(state:MessagesState):
    return {"messages":[llm_with_tools.invoke([sys_msg] + state["messages"])]}

builder = StateGraph(MessagesState)

#add node
builder.add_node("chatbot",chatbot)
builder.add_node("tools",ToolNode(tools))



# Add edges 
builder.add_edge(START, "chatbot")
builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    
)

builder.add_edge("tools","chatbot")


builder.add_edge("chatbot",END)

react_graph = builder.compile()



#use with telegram bot
async def find_frequency_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    messages = [HumanMessage(content=user_input)]
    messages = react_graph.invoke({"messages":messages})
    await update.message.reply_text(messages["messages"][-1].content)



async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Thank you for using the frequency search bot!")




