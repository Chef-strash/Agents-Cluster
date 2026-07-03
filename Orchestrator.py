from distributed_compute.schemas import AgentState
from langgraph.graph import StateGraph, END, START
import asyncio
import httpx
import websockets
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Constant extra instruction for public message
EXTRA_INSTRUCTION = "Note: Ensure your output is highly professional, concise, and structured."


# Define Central Node
def central_node(state: AgentState) -> dict:
    """
    Central node:
    - Prepares the public message (includes constant extra instruction)
    - Logs the subagent's response into the MessagePool
    - Increments the Round_No
    """
    current_round = state.get("Round_No", 0)
    instructions = state.get("Instructions", "")
    message_pool = state.get("MessagePool", [])
    
    # Public message has a constant (will not change) extra instruction
    public_msg = f"{instructions}\n\n[Extra Instruction]: {EXTRA_INSTRUCTION}"
    
    print(f"--- Round {current_round + 1} ---")
    
    return {
        "Round_No": current_round + 1,
        "MessagePool": message_pool,
        "Public_Message": public_msg
    }

# Define Broker Node to distribute task and aggregate responses
def broker_node(state: AgentState) -> dict:
    print("\n--- Broker Node: Distributing Task to Broker ---")
    
    async def _run():
        broker_http_url = "http://127.0.0.1:8000/distribute"
        
        try:
            # 1. Trigger task distribution and await responses (blocking until all agents reply)
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(broker_http_url, json=dict(state))
                if response.status_code != 200:
                    print(f"Failed to distribute task: {response.text}")
                    return state
                
                result = response.json()
                if result.get("status") == "error":
                    print(f"Broker error: {result.get('message')}")
                    return state
                
                agent_responses = result.get("responses", [])
                new_messages = []
                for resp in agent_responses:
                    agent_id = resp.get("agent_id")
                    content = resp.get("result")
                    
                    formatted_response = f"[{agent_id}]: {content}"
                    new_messages.append(formatted_response)
                    print(f"Collected response from {agent_id}: {content}")
                
                updated_pool = list(state.get("MessagePool", [])) + new_messages
                
                return {
                    "Round_No": state.get("Round_No", 0),
                    "MessagePool": updated_pool,
                    "Public_Message": state.get("Public_Message", "")
                }
        except Exception as e:
            print(f"Error in Broker Node communication: {e}")
            return state

    try:
        # Run async function safely from sync context
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(_run(), loop).result()
        except RuntimeError:
            return asyncio.run(_run())
    except Exception as e:
        print(f"Error executing Broker Node: {e}")
        return state


# Define Conditional Route
def should_continue(state: AgentState) -> str:
    """
    Conditional routing: if round no. is less than 10, go back to Central, else end.
    """
    if state.get("Round_No", 0) < 10:
        return "Central"
    else:
        return "end"


# Build the Orchestrator Graph
orchestrator_workflow = StateGraph(AgentState)

# Add Central Node
orchestrator_workflow.add_node("Central", central_node)

#Add broker
orchestrator_workflow.add_node("Broker", broker_node)

# START -> Central
orchestrator_workflow.add_edge(START, "Central")
orchestrator_workflow.add_edge("Central","Broker")

# Add Conditional Edge from Central
orchestrator_workflow.add_conditional_edges(
    "Broker",
    should_continue,
    {
        "Central": "Central",
        "end": END
    }
)

# Compile Orchestrator Graph
orchestrator_app = orchestrator_workflow.compile()

if __name__ == "__main__":
    # Define an initial query to conduct the rounds on
    initial_state = {
        "Instructions": "Analyze the impact of distributed consensus protocols in large-scale multi-agent systems. answer in 5 lines",
        "MessagePool": [],
        "Round_No": 0,
        "Public_Message": ""
    }
    
    print("Starting Orchestrator Graph execution...")
    final_output = orchestrator_app.invoke(initial_state)
    
    print("\n================ FINAL COMPUTE POOL RESULTS ================")
    for msg in final_output.get("MessagePool", []):
        print(msg)

