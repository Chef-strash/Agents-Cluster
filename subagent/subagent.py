from typing import Annotated, Sequence, TypedDict
import asyncio
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Initialize LLM

from langchain_ollama import ChatOllama
llm = ChatOllama(
    model="qwen2.5:1.5b",
    temperature=0.6
)

# Define Agent State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Define Respond node function
async def respond(state: AgentState) -> dict:
    """
    Respond node: Prepares a system prompt and retrieves the custom message 
    passed from the orchestrator's state (via the latest human message)
    to invoke the model.
    """
    system_prompt = SystemMessage(
        content= "respond with hi everytime"
    )
    
    # Retrieve the latest message, which is the custom message from Orchestrator's AgentState
    if state["messages"]:
        custom_message_content = state["messages"][-1].content
    else:
        custom_message_content = "No instructions provided."
        
    custom_message = HumanMessage(content=custom_message_content)
    
    # Invoke the model with system prompt and the custom message
    response = await llm.ainvoke([system_prompt, custom_message])
    
    return {"messages": [response]}


# Define workflow
workflow = StateGraph(AgentState)

# Add Respond node
workflow.add_node("Respond", respond)

# Add edges: START -> Respond -> END
workflow.add_edge(START, "Respond")
workflow.add_edge("Respond", END)

# Enable memory saver
memory = InMemorySaver()

# Compile the subagent
subagent_app = workflow.compile(checkpointer=memory)
