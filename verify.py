import sys
import os

# Add parent directory to path so python can find distributed_compute modules
sys.path.append(r"c:\Users\AYUSH\Messblock-Dojo\NLP\Agents")

from distributed_compute.Orchestrator import orchestrator_app

def run_verification():
    print("Initializing Orchestrator Run...")
    
    initial_state = {
        "Instructions": "Solve this equation: x + 5 = 12. Explain it in a brief step.",
        "MessagePool": [],
        "Round_No": 0,
        "Public_Message": ""
    }
    
    # Run the orchestrator graph
    final_state = orchestrator_app.invoke(initial_state)
    
    print("\n--- FINAL ORCHESTRATOR STATE ---")
    print(f"Final Round Count: {final_state.get('Round_No')}")
    print(f"Number of Messages in Pool: {len(final_state.get('MessagePool', []))}")
    print("Message Pool Responses:")
    for idx, msg in enumerate(final_state.get("MessagePool", []), 1):
        print(f"  {idx}. {msg}")

if __name__ == "__main__":
    run_verification()

