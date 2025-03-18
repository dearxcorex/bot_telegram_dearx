from telegram import Update
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
import pandas as pd
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes,filters,MessageHandler,ConversationHandler
import os 
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
load_dotenv()   
#https://colab.research.google.com/drive/14ncV0nviLcP9IDzmFSRGSXb7Bgpz212v?usp=sharing
#load csv 
path = "frequency_analysis/merged_clean.csv"

df = pd.read_csv(path)

class FrequencySearch(BaseModel):
    freq: float
    user: str
    freq_range:list[float,float]

    
class State(TypedDict):
    messages: Annotated[list, add_messages]


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
    # print(q)
    #filter range freqeuncy and user
    mask = (df["freq"] >= f[0]) & (df["freq"] <= f[1]) & (df["user"] == q)

    return df[mask]

tools = [search_frequency,search_frequency_user]
model = ChatOpenAI(model="gpt-4o-mini",temperature=0)
llm_with_tools = model.bind_tools(tools)


prompt = """
You are a expert in frequency allocation and analysis. 
You are given a frequency and you need to find the nearest frequency or user column in the dataframe. If the frequency is not found, you need to return the nearest 5 frequency and  column user from the dataframe.

if user spell wrong, you need to correct the user name and return the nearest user from the dataframe.
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
react_graph = builder.compile()

#Display graph  save as png
react_graph.get_graph().draw_mermaid_png(output_file_path="frequency_analysis/frequency_analysis.png")





# def print_stream(stream):
#     for s in stream:
#         message = s["messages"][-1]
#         if isinstance(message, tuple):
#             print(message)
#         else:
#             message.pretty_print()


messages = [HumanMessage(content="what is  user frequency  กรมการสื่อสารทหาร and range 137-174 ?")]
messages = react_graph.invoke({"messages":messages})


for m in messages["messages"]:
    m.pretty_print()

# query = FrequencySearch(freq=0.0, user="กรมการสื่อสารทหาร",freq_range=[137,174])  # freq is required since it's part of the model
# result = search_frequency_user(query)

# print(result)


