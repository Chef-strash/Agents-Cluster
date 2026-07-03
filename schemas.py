from typing import TypedDict

# Define Orchestrator Agent State
class AgentState(TypedDict):
    Instructions: str
    MessagePool: list[str]
    Round_No: int  # Represents 'Round No'
    Public_Message: str  # Represents 'Public Message'