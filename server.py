import asyncio
import websockets
import requests

# Hugging Face API configuration
API_TOKEN = "**********************"
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-v0.1"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# Debate parameters
NUM_ROUNDS = 5

# Function to send a request to the Mistral 7B model
def query_mistral(prompt):
    payload = {"inputs": prompt, "parameters": {"max_length": 200, "temperature": 0.7}}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# Function to create prompts for both participants
def create_prompt(topic, previous_statements, speaker):
    debate_history = "\n".join(previous_statements[-4:])  # Include recent context
    
    system_context = (
        "You are participating in a formal debate. Make clear, logical arguments supported by reasoning or evidence. "
        "Address the specific points made by your opponent and provide counterarguments when appropriate. "
        "Keep responses focused and structured."
    )
    
    if speaker == "Participant A":
        prompt = f"""
{system_context}

Debate Topic: {topic}

Previous Discussion:
{debate_history}

You are Participant A. Carefully consider Participant B's last point, then provide a well-reasoned response that:
1. Briefly acknowledges their argument
2. Presents your counter-argument with supporting logic or evidence
3. Concludes with a strong point

Response:"""
    else:
        prompt = f"""
{system_context}

Debate Topic: {topic}

Previous Discussion:
{debate_history}

You are Participant B. Carefully consider Participant A's last point, then provide a well-reasoned response that:
1. Briefly acknowledges their argument
2. Presents your counter-argument with supporting logic or evidence
3. Concludes with a strong point

Response:"""
    return prompt

# WebSocket server to facilitate the debate
async def debate_server(websocket, path):
    await websocket.send("Welcome to the LLM Debate Server! Please provide a debate topic:")
    topic = await websocket.recv()
    
    # Initialize with a more structured opening
    opening_statement = f"The topic for today's debate is: {topic}\n\nParticipant A will present the opening argument."
    previous_statements = [opening_statement]
    await websocket.send(opening_statement)

    # Track the debate rounds and participants' responses
    participants = ["Participant A", "Participant B"]

    for round_number in range(1, NUM_ROUNDS + 1):
        # Determine the current speaker
        current_speaker = participants[round_number % 2]
        
        # Generate the prompt for the current speaker
        prompt = create_prompt(topic, previous_statements, current_speaker)
        response = query_mistral(prompt)
        
        # Update debate history
        if response:
            previous_statements.append(response)
            # Send the response back through WebSocket
            await websocket.send(f"{current_speaker}: {response}")
        else:
            await websocket.send(f"Error: Could not generate response for {current_speaker}.")

    await websocket.send("The debate has concluded. Thank you for watching!")

# Start the WebSocket server
start_server = websockets.serve(debate_server, "localhost", 8765)

print("WebSocket server started on ws://localhost:8765")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

