import asyncio
import websockets
import json
from distributed_compute.subagent.subagent import subagent_app

# broker connect API
base_url= "wss" + "https://prolongedly-prius-eldon.ngrok-free.dev"[5:]
BROKER_URL = base_url + "/connect"
AGENT_ID = "agent_A"


async def run_agent():
    uri = f"{BROKER_URL}/{AGENT_ID}"
    
    # Establish connection via websocket
    async with websockets.connect(uri) as ws:
        print("Connected to broker")

        while True:
            raw_msg = await ws.recv()
            task = json.loads(raw_msg)

            print("Received task:", task)

            # Retry loop to handle rate limits and transient errors gracefully
            retries = 3
            ai_response = None
            for attempt in range(retries):
                try:
                    result = await subagent_app.ainvoke(
                        {"messages": task["instruction"]},
                        config={
                            "configurable": {
                                "thread_id": AGENT_ID
                            }
                        })
                    
                    ai_response = result["messages"][-1].content
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed with error: {e}")
                    if attempt < retries - 1:
                        print("Sleeping 3 seconds to respect rate limits and back off")
                        await asyncio.sleep(3)
                    else:
                        ai_response = f"Error: Failed to execute task after {retries} attempts due to: {e}"
    
            print("Result:", ai_response)

            await ws.send(json.dumps({
                "agent_id": AGENT_ID,
                "result": ai_response
            }))

if __name__ == "__main__":
    asyncio.run(run_agent())