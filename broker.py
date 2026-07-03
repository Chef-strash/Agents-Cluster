import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from distributed_compute.schemas import AgentState
from typing import Dict, List, Any

app = FastAPI()

class BrokerState:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.responses: Dict[str, Any] = {}
        self.response_event = asyncio.Event()

broker_state = BrokerState()

@app.websocket("/connect/{agent_id}")
async def connect_agent(websocket: WebSocket, agent_id: str):
    await websocket.accept()
    broker_state.connections[agent_id] = websocket
    print(f"{agent_id} connected")

    try:
        while True:
            data = await websocket.receive_json()
            broker_state.responses[data["agent_id"]] = data
            if len(broker_state.responses) >= len(broker_state.connections):
                broker_state.response_event.set()       
            
    # catches the exception raised when a subagent loses or closes its WebSocket connection
    except WebSocketDisconnect:
        print(f"{agent_id} disconnected")
        if agent_id in broker_state.connections:
            del broker_state.connections[agent_id]
        if agent_id in broker_state.responses:
            del broker_state.responses[agent_id]
            
        if len(broker_state.responses) >= len(broker_state.connections) and len(broker_state.connections) > 0:
            broker_state.response_event.set()

@app.post("/distribute")
async def distribute(state: AgentState):
    broker_state.responses.clear()
    broker_state.response_event.clear()

    if not broker_state.connections:
        return {"status": "error", "message": "No active subagents connected"}

    for agent_id, websocket in broker_state.connections.items():
        try:
            await websocket.send_json({
                "agent_id": agent_id,
                "instruction": state.get("Public_Message", "")
            })
        except Exception as e:
            print(f"Failed to send task to {agent_id}: {e}")
    
    await broker_state.response_event.wait()
    
    return {"status": "success", "responses": list(broker_state.responses.values())}

    