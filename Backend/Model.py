import json
import os
import sys
from google import genai
from google.genai import types
from rich import print  # Import the Rich library to enhance terminal outputs.
from dotenv import dotenv_values  # Import dotenv to load environment variables from a .env file.

# Load environment variables from the root .env file.
env_vars = dotenv_values(".env")

# Retrieve API key.
GeminiAPIKey = env_vars.get("GeminiAPIKey")
if not GeminiAPIKey:
    # Safe backup fallback placeholder matching your config layout
    GeminiAPIKey = "AQ.Ab8RN6I3tKNEwqfTHi9wuEGBjuJBGoE9wD2Wfn8EgQXIaDiVFA"

# Create a Gemini client using the official SDK package structure
client = genai.Client(api_key=GeminiAPIKey)

# Define a list of recognized function keywords for task categorization.
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder"
]

# Initialize an empty list to store user messages.
messages = []

# Define the strict system instruction template that guides the AI model on how to categorize queries.
strict_preamble = """You are a precise text classification machine. Your job is to convert user inputs into clean action intents inside a python list format.

Available Categories & Strict Routing Rules:
- 'play [query]' -> ONLY use this when user wants to stream or watch external media on YouTube/Browser (e.g., 'play carryminati video', 'play forever song'). If the user asks YOU to sing, talk, or speak directly (e.g., 'sing a song for me', 'sing a poem'), route it strictly to 'general' context.
- 'open [app_name/website_name]' -> For opening apps/sites (e.g., 'open google', 'open whatsapp', 'open visual studio code').
- 'close [app_name/website_name]' -> For closing apps/sites or stopping streams.
- 'system [task_name]' -> For tasks like 'system mute', 'system unmute', 'system volume up', 'system volume down'.
- 'generate image [prompt]' -> For generating images based on a prompt.
- 'content [topic]' -> For writing applications, letters, essays, emails, codes (e.g., 'write an application leave').
- 'realtime [query]' -> For live information, internet search, time, dates, or live updates.
- 'general [query]' -> For greetings, conversational replies, remembering names, chitchat, or when asked to talk/sing directly (e.g., 'greet my friend', 'remember my friend name Tanishka', 'sing a hindi poem for me').
- 'exit' -> To close tabs or end sessions.

CRITICAL RULES:
1. When asked to write templates, applications or notes, strictly match the 'content <topic>' format.
2. Personal conversation hooks, names, greetings must always be routed to 'general'.
3. OUTPUT FORMAT: Return ONLY a valid Python list of strings (e.g., ['content three day application leave']). No markdown, no prose, no code backticks. Do not include ```json or ```python formatting blocks.
4. CONDITIONAL SNAP LAWS:
If the user sets a future condition based on snapping or chutki (e.g., 'jab main chutki bajaunga tab youtube open karna', 'snap karne par whatsapp kholna'), you MUST NOT return 'open <app>'. Instead, return strictly ['set_snap_action <app_name>']."""

# Define the main function for decision-making on queries.
def FirstLayerDMM(prompt: str = "test"):
    global messages
    # Add the user's query to the messages list.
    messages.append({"role": "user", "content": f"{prompt}"})

    try:
        # Configuring system instructions and structural constraints using gemini-2.5-flash
        config = types.GenerateContentConfig(
            system_instruction=strict_preamble,
            temperature=0.0,  # Zero temperature for deterministic classification output
        )
        
        # Making a precise structural content generation call
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        
        # --- AUTOMATIC SANITIZATION LAYER ---
        import re
        raw_text = response.text.strip()
        
        # Safeguard cleaning against formatting brackets/quotes if any remain in text response
        cleaned_text = raw_text.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
        cleaned_text = cleaned_text.replace("```python", "").replace("```json", "").replace("```", "").strip()
        
        # Create the clean python list output array
        cleaned_intents = [intent.strip() for intent in re.split(r',|\n', cleaned_text) if intent.strip()]
        
        # Filter the response array based on recognized system function prefixes
        temp = []
        for task in cleaned_intents:
            for func in funcs:
                if task.startswith(func) or task.startswith("set_snap_action"):
                    if task not in temp:
                        temp.append(task)
                        
        return temp

    except Exception as e:
        print(f"❌ Gemini Intent Extraction Layer Failure: {e}")
        return ["general chat with me"]

# =========================================================================
# 🤖 NEW FUNCTION: FINAL RESPONSE GENERATOR WITH CONTEXT SUPPORT (RAG)
# =========================================================================
def call_gemini_model(prompt: str, context: str = None) -> str:
    """
    User ki query aur local database (RAG) ke context ko combine karke 
    Gemini-2.5-Flash se final polished answer generate karta hai.
    """
    try:
        # Agar local database se koi context mila hai, toh use prompt ke sath mix karo
        if context:
            full_prompt = f"""You are Maya, a smart AI Assistant. Use the provided Local Knowledge Context to answer the user's query accurately.
            
            [Local Knowledge Context]:
            {context}
            
            [User Query]: {prompt}
            
            Answer precisely based on the context."""
        else:
            full_prompt = prompt

        # Gemini API call for generating final output
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )
        return response.text.strip()

    except Exception as e:
        print(f"❌ Gemini Response Generation Failure: {e}")
        return "Sorry Nishant sir, I encountered an error while processing your request."

# Entry point for the script.
if __name__ == "__main__":
    while True:
        user_input = input(">>> ")
        print(FirstLayerDMM(user_input))