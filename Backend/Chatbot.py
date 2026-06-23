# File Path: Backend/Chatbot.py
import json
import datetime
import os
from google import genai
from google.genai import types
from dotenv import dotenv_values

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")

Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Jarvis")

# Retrieve the Gemini API Key matching with your .env layout
GeminiAPIKey = env_vars.get("GeminiAPIKey")
if not GeminiAPIKey:
    # Safe backup hardcode fallback placeholder if needed
    GeminiAPIKey = "AQ.Ab8RN6I3tKNEwqfTHi9wuEGBjuJBGoE9wD2Wfn8EgQXIaDiVFA"

# Initialize the Gemini Client natively using the official 2026 google-genai SDK
client = genai.Client(api_key=GeminiAPIKey)

# Ensure the Data directory exists
os.makedirs("Data", exist_ok=True)

# System configuration setup for tracking rules
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question concisely.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes or explanations in the output, just answer the question directly and never mention your training data. ***
"""

CHAT_LOG_PATH = r"Data\ChatLog.json"

# Initialize or verify ChatLog format
try:
    with open(CHAT_LOG_PATH, "r", encoding="utf-8") as f:
        json.load(f)
except (FileNotFoundError, ValueError):
    with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump([], f, indent=4)

def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Please use this real-time information if needed,\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours :{minute} minutes :{second} seconds.\n"
    return data

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def ChatBot(Query):
    """ Sends the query to Gemini and maintains json logs. Bypasses unsupported streaming on multi-turn chat. """
    try:
        try:
            with open(CHAT_LOG_PATH, "r", encoding="utf-8") as f:
                messages = json.load(f)
        except Exception:
            messages = []

        # Syncing dynamic preamble configurations
        full_system_instruction = System + "\n" + RealtimeInformation()
        
        system_prompt = {"role": "system", "content": full_system_instruction}
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, system_prompt)
        else:
            messages[0] = system_prompt

        messages.append({"role": "user", "content": str(Query)})

        # Converting chat history array safely into Gemini's official Content objects structure
        gemini_history = []
        for msg in messages[:-1]:  # Exclude current query from history stream
            if msg["role"] == "system":
                continue
            # Map role identifiers: user -> user, assistant -> model
            role_map = "user" if msg["role"] == "user" else "model"
            gemini_history.append(
                types.Content(role=role_map, parts=[types.Part.from_text(text=msg["content"])])
            )

        # Configuring generation parameters using gemini-2.5-flash
        config = types.GenerateContentConfig(
            system_instruction=full_system_instruction,
            temperature=0.7,
            max_output_tokens=1024,
        )

        # Initialize multi-turn chat session safely
        chat = client.chats.create(model="gemini-2.5-flash", history=gemini_history)
        
        # 🔥 FIX: making the safe NON-STREAMING call. Removing stream=True keyword.
        response = chat.send_message(str(Query), config=config)

        # Extract absolute raw text response natively
        Answer = ""
        if response.text:
            Answer = response.text.strip()

        # Update disk storage components
        if Answer:
            messages.append({"role": "assistant", "content": Answer})
            with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=4)

        return AnswerModifier(Answer=Answer)

    except Exception as e:
        print(f"❌ Gemini Engine Runtime Failure Intercepted: {e}")
        # Agar main loop me Gemini crash karega toh direct Tavily Fallback fire hoga,
        # isliye hum bas ChatLog flush kar denge safest exit ke liye.
        try:
            with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)
        except:
            pass
        # Main loop expects standard failure string to initiate rerouting logic standard
        raise e 

def UniversalIntentParser(user_query):
    """ AGI Core: Extracts structured JSON intent using Gemini. Strictly enforces JSON format execution output. """
    try:
        prompt = f"""Analyze command: "{user_query}"
Extract ONLY raw JSON: {{"app": "...", "action": "...", "target": "...", "payload": "..."}}
Do not add markdown, quotes or explanations."""
        
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"  # Enforces Gemini to native output absolute valid JSON
        )
        
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt, config=config)
        return json.loads(response.text.strip())
        
    except Exception as e:
        print(f"⚠️ AGI JSON Parser Error: {e}")
        return {"app": "None", "action": "general_chat", "target": "None", "payload": "None"}

if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))