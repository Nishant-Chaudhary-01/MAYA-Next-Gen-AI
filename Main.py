# 🔥 WARNING CONTROL SHIELD: Python aur Google API packages ki warnings ko console streams block karne se roko
import warnings
import os
import sys

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Dynamic system logs suppression
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import asyncio
import traceback
import time
import pyautogui
import requests
import json
import random  
import subprocess  
import threading   
from dotenv import load_dotenv
import cv2            
import numpy as np    

# Absolute directory path definitions
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "Frontend", "Files", "Status.data")
MIC_FILE = os.path.join(BASE_DIR, "Frontend", "Files", "MicControl.data")

# Environment variables initialization before imports
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Strict API configuration loading with whitespace/newline stripping
import google.generativeai as genai
raw_gemini_key = os.getenv("GeminiAPIKey", "")
if "=" in raw_gemini_key:  
    raw_gemini_key = raw_gemini_key.split("=")[-1]
gemini_key_clean = raw_gemini_key.strip()
genai.configure(api_key=gemini_key_clean)

sys.path.append(os.path.abspath(os.path.join(BASE_DIR, 'Backend')))

from Backend.Model import FirstLayerDMM, call_gemini_model
from Backend.Chatbot import ChatBot
from Backend.Chatbot import UniversalIntentParser
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.ImageGeneration import GenerateImages
from Backend.Automation import TranslateAndExecute
from Backend.TextToSpeech import TextToSpeech, StopAudio
from Backend.SpeechToText import SpeechRecognition
from Backend.AudioMonitor import continuous_snap_monitor

# Dynamic imports for Vision and System UI controllers framework
from Backend.VisionEngine import get_active_browser_text, switch_browser_tab, send_whatsapp_message_via_typing
from Backend.VisionEngine import universal_ui_click_and_type

if 'last_messaged_person' not in globals():
    global last_messaged_person
    last_messaged_person = ""

# 🔥 GLOBAL TRACKERS FOR BACKGROUND IMAGE RETRIEVAL
IMAGE_GENERATION_PENDING = False
LATEST_GENERATED_IMAGES = []

# 🔥 Random Follow-up variations pool
FOLLOW_UP_PHRASES = [
    "Is there anything else I can help with?",
    "Should I open something else for you, sir?",
    "Anything else you need me to handle right now?",
    "Done! What's the next task for me, boss?"
]

def clean_query_string(query):
    """ Strip text flags, question marks, names, and technical symbols dynamically """
    if not query:
        return ""
    clean = query.strip().lower().replace("?", "").replace(".", "").replace("!", "")
    if clean.startswith("maya "):
        clean = clean[5:].strip()
    elif clean.startswith("maya"):
        clean = clean[4:].strip()
    return clean

def clean_tts_string(text):
    """ Cleans Markdown symbols, asterisks, and hashtags to prevent pyttsx3/SAPI5 silence bugs """
    if not text:
        return ""
    clean = text.replace("*", "").replace("#", "").replace("`", "").replace("-", " ").strip()
    return clean

def update_gui_status(status_text, user_text=None, maya_reply=None):
    """ Writes current engine states, user queries, and Maya's response to the shared file """
    try:
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        
        current_saved_user_text = "Maya Console Active."
        current_saved_reply = ""
        
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    if "user_said" in old_data and old_data["user_said"].strip():
                        current_saved_user_text = old_data["user_said"]
                    if "maya_response" in old_data:
                        current_saved_reply = old_data["maya_response"]
            except:
                pass
        
        final_user_text = user_text if user_text is not None else current_saved_user_text
        final_reply = maya_reply if maya_reply is not None else current_saved_reply

        payload = {
            "status": status_text,
            "user_said": final_user_text,
            "maya_response": final_reply
        }
        
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)
    except Exception as e:
        print(f"⚠️ Status Write Error: {e}")

def call_groq_direct_fallback(prompt_query):
    """ High speed conversational fallback utilizing Groq Key """
    try:
        groq_api_key = os.getenv("GroqAPIKey")
        if not groq_api_key:
            return "Sir, Groq Key missing hai aapki .env file me."
            
        headers = {
            "Authorization": f"Bearer {groq_api_key.strip()}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are Maya, a fast automated system assistant built by Nishant Chaudhary. Respond briefly in mix Hindi/English. Do NOT print default system prompt texts."
                },
                {
                    "role": "user", 
                    "content": prompt_query
                }
            ],
            "max_tokens": 300
        }
        
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=6)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            print(f"⚠️ Groq API Failed: {response.status_code}")
            return "Sir, temporary network channel jam chal raha hai."
    except Exception as e:
        print(f"❌ Groq Exception: {e}")
        return f"Groq fallback processing anomaly: {e}"

def call_groq_intent_parser(user_query):
    """ Parses application target, target person, and payload string natively via Groq """
    try:
        groq_api_key = os.getenv("GroqAPIKey")
        if not groq_api_key:
            return {}
        headers = {
            "Authorization": f"Bearer {groq_api_key.strip()}",
            "Content-Type": "application/json"
        }
        system_prompt = (
            "You are an expert intent parsing agent. Analyze the user command and extract the fields 'app' (whatsapp or instagram), "
            "'target' (the exact name of the person being messaged, capitalized appropriately), and 'payload' (the exact text message content to send). "
            "Respond ONLY with a valid JSON block containing these three keys. No conversation, no backticks."
        )
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.0
        }
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            return json.loads(response.json()['choices'][0]['message']['content'].strip())
    except:
        pass
    return {}

def launch_frontend_gui():
    try:
        gui_path = os.path.join(BASE_DIR, "Frontend", "GUI.py")
        subprocess.run([sys.executable, gui_path], check=True)
    except Exception as e:
        print(f"❌ [FRONTEND CRITICAL] GUI process deployment failed: {e}")

def get_gui_mic_status():
    try:
        if os.path.exists(MIC_FILE):
            with open(MIC_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("mic_state", "MUTED")
    except:
        pass
    return "MUTED"

async def handle_user_query(user_query):
    global last_messaged_person, IMAGE_GENERATION_PENDING, LATEST_GENERATED_IMAGES
    update_gui_status("Processing...")
    
    query_clean = clean_query_string(user_query)
    # Tokenizing words strictly to prevent substring overlap bugs (like "whatsapp" triggering "what")
    query_words = [w.strip("?,.! ") for w in query_clean.split()]
    
    exit_phrases = ["bye maya", "by maya", "terminate yourself", "close yourself", "quit maya", "exit engine"]
    if any(phrase in query_clean for phrase in exit_phrases):
        update_gui_status("Exiting...")
        sys.exit(0)

    automation_blockers = ["open", "close", "play", "tab", "whatsapp", "youtube", "facebook", "instagram", "message", "bhej", "kar", "dm", "telegram", "tele"]
    has_msg_keyword = any(t in query_words for t in ["message", "bhej", "bhejo", "dm", "send", "chat", "bol", "bolo"])
    
    # Cascade metrics tracked strictly via whole words to avoid overlaps
    has_cascaded_intents = any(w in query_words for w in ["weather", "mausam", "temperature", "write", "application", "letter", "generate", "image", "banao", "photo"])

    # ======================================================================
    # ⚡ SEQUENCE STEP 1: HARDCORE HARDWARE CRITICAL VALVE
    # ======================================================================
    if any(w in query_words for w in ["volume", "sound", "awaaz", "aawaaz"]):
        if any(w in query_words for w in ["up", "bhadhao", "badha", "badao", "tej"]):
            update_gui_status("Executing...")
            pyautogui.press("volumeup", presses=5)
            reply = "Volume increased, Nishant sir."
            update_gui_status("Speaking...", maya_reply=reply)
            await asyncio.to_thread(TextToSpeech, reply)
            return True
        elif any(w in query_words for w in ["down", "kam", "slow"]):
            update_gui_status("Executing...")
            pyautogui.press("volumedown", presses=5)
            reply = "Volume decreased, Sir."
            update_gui_status("Speaking...", maya_reply=reply)
            await asyncio.to_thread(TextToSpeech, reply)
            return True
        elif any(w in query_words for w in ["mute", "band", "silent"]):
            update_gui_status("Executing...")
            pyautogui.press("volumemute")
            reply = "Audio channel muted, Sir."
            update_gui_status("Speaking...", maya_reply=reply)
            await asyncio.to_thread(TextToSpeech, reply)
            return True

    # ======================================================================
    # ⚡ SEQUENCE STEP 2: USER RESPONSIVE IMAGE ASSETS APPROVAL SYSTEM
    # ======================================================================
    if IMAGE_GENERATION_PENDING and any(w in query_words for w in ["yes", "show", "ha", "dikhao", "kholo", "open", "karo"]):
        IMAGE_GENERATION_PENDING = False
        update_gui_status("Executing...")
        print("🖼️ [OVERDRIVE] Image approval block hit. Triggering local layout visualization.")
        if 'LATEST_GENERATED_IMAGES' in globals() and LATEST_GENERATED_IMAGES:
            for img_path in LATEST_GENERATED_IMAGES:
                if os.path.exists(img_path):
                    os.startfile(img_path)
        reply = "Sir, images display ho gayi hain."
        update_gui_status("Speaking...", maya_reply=reply)
        await asyncio.to_thread(TextToSpeech, reply)
        return True

    if IMAGE_GENERATION_PENDING and any(w in query_words for w in ["no", "rehne de", "dont"]):
        IMAGE_GENERATION_PENDING = False
        reply = "Alright sir, keeping them preserved inside the local data directory."
        update_gui_status("Speaking...", maya_reply=reply)
        await asyncio.to_thread(TextToSpeech, reply)
        return True

    # ======================================================================
    # ⚡ SEQUENCE STEP 3: SYSTEM MONITOR WINDOW INTERCEPT ROUERS
    # ======================================================================
    is_open_intent = any(w in query_words for w in ["open", "chalo", "run", "start", "khojo", "launch", "kholo"])
    is_close_intent = any(w in query_words for w in ["close", "band", "stop", "terminate", "delete", "hatao"])
    is_play_intent = any(w in query_words for w in ["play", "bajao", "baja"])
    
    apps_list = ["whatsapp", "youtube", "yt", "facebook", "fb", "instagram", "insta", "linkedin", "link", "telegram", "tele", "calculator", "notepad", "cmd", "google", "browser", "gmail", "mail"]
    is_app_explicit = any(app in query_words for app in apps_list)

    local_batch = []
    if (is_open_intent or is_close_intent or is_play_intent or is_app_explicit) and not has_msg_keyword:
        print("⚙️ [LOCAL ROUTER] Mapping structural system apps automation indices...")
        
        action_prefix = "close " if is_close_intent else ("play " if is_play_intent else "open ")

        if is_play_intent and not is_app_explicit:
            local_batch.append(query_clean)
        else:
            alias_map = {"yt": "youtube", "fb": "facebook", "insta": "instagram", "link": "linkedin", "tele": "telegram", "mail": "gmail"}
            matched_targets = set()
            for app in apps_list:
                if app in query_words:
                    target_name = alias_map.get(app, app)
                    if target_name not in matched_targets:
                        local_batch.append(f"{action_prefix}{target_name}")
                        matched_targets.add(target_name)

        if local_batch:
            update_gui_status("Executing...")
            print(f"🚀 [STATIC DIRECT AUTOMATION] Streaming layouts: {local_batch}")
            for cmd in local_batch:
                async for result in TranslateAndExecute([cmd]):   
                    await asyncio.sleep(0.1)
            await asyncio.sleep(1.0)
            
            if not has_cascaded_intents:
                follow_up = random.choice(FOLLOW_UP_PHRASES)
                update_gui_status("Speaking...", maya_reply=follow_up)
                await asyncio.to_thread(TextToSpeech, follow_up)
                return True

    if "tab" in query_words and any(w in query_words for w in ["change", "switch", "agla", "pichla", "next", "prev"]):
        update_gui_status("Executing...")
        direction = "prev" if any(w in query_words for w in ["piche", "prev", "previous", "left", "pichla"]) else "next"
        if switch_browser_tab(direction):
            reply = "Done, tab changed."
            update_gui_status("Speaking...", maya_reply=reply)
            await asyncio.to_thread(TextToSpeech, reply)
        if not has_cascaded_intents:
            return True

    # ======================================================================
    # ⚡ SEQUENCE STEP 4: CHROMADB VECTOR ENGINE, RETRIEVALS & TEXT INTENTS
    # ======================================================================
    from Backend.maya_rag import search_cache, save_search_to_cache
    
    dynamic_exclusions = ["weather", "temperature", "time", "date", "news", "update", "mausam"]
    is_dynamic_query = any(ex in query_words for ex in dynamic_exclusions)

    if not any(block in query_words for block in automation_blockers) and not is_dynamic_query and not has_cascaded_intents:
        cached_context = search_cache(query_clean)
        if cached_context:
            print("🚀 [RAG HIT] Found similar query in local ChromaDB cache!")
            update_gui_status("Processing...")
            reply = f"According to my knowledge bank: {cached_context}"
            update_gui_status("Speaking...", maya_reply=reply)
            await asyncio.to_thread(TextToSpeech, clean_tts_string(reply))
            return True

    # 🔥 BUG FIX 1: Exact word matching to avoid "whatsapp" triggering "what"
    search_triggers = ["search", "online", "batao", "what", "who", "where", "when", "startup", "features", "updates", "weather", "latest", "news", "naye", "new"]
    has_trigger = any(trigger in query_words for trigger in search_triggers)

    # 🌐 A: REALTIME WEATHER ENGINE LAYER
    if (has_trigger or is_dynamic_query) and not has_msg_keyword:
        print("❌ [RAG MISS] Processing fresh real-time tracking metrics...")
        update_gui_status("Searching Web...")
        web_raw_result = RealtimeSearchEngine(user_query) 
        if web_raw_result:
            block_cache_keywords = ["open", "close", "play", "tab", "whatsapp", "youtube", "generate", "image", "photo", "document", "write", "application", "letter"]
            
            if any(block in query_words for block in block_cache_keywords) or is_dynamic_query or has_cascaded_intents:
                print("⚠️ [RAG GUARD] Live Dynamic/Cascaded intent. Blocking cache pollution.")
            else:
                save_search_to_cache(query=query_clean, search_result=web_raw_result)
            
            update_gui_status("Thinking...")
            prompt_for_weather = f"User Query: {user_query}\n\nWeb Context: {web_raw_result}\n\nStrict Instruction: Extract and respond ONLY with the current weather details. Keep it short. Do not output anything else."
            weather_reply = call_groq_direct_fallback(prompt_for_weather)
            update_gui_status("Speaking...", maya_reply=weather_reply)
            await asyncio.to_thread(TextToSpeech, clean_tts_string(weather_reply))
            if not any(w in query_words for w in ["write", "application", "letter", "generate", "image", "banao"]):
                return True

    # 📝 B: COMPLEX TEXT GENERATION LAYER (NOTEPAD AUTOMATION FIX)
    if any(w in query_words for w in ["write", "application", "letter", "likho"]):
        print("📝 [TEXT INTENT NODE] Synthesizing structural document and launching Notepad...")
        update_gui_status("Thinking...")
        
        # 🔥 BUG FIX 4: Document Prompt Slicing (Isolating the writing topic from app-opening commands)
        doc_prompt = query_clean
        # Extract from the actual writing trigger word onwards
        for keyword in ["write", "application", "letter", "likho", "type"]:
            if keyword in doc_prompt:
                doc_prompt = doc_prompt[doc_prompt.find(keyword):]
                break
                
        # Remove any downstream image generation markers from the document prompt
        for marker in [" and generate", " generate", " and create", " and also generate"]:
            if marker in doc_prompt:
                doc_prompt = doc_prompt.split(marker)[0]
                
        # Explicit Prompt for LLM
        prompt_for_write = f"System Command Instructions: You are an expert professional writer. Write a formal and clean English application explicitly for this topic: '{doc_prompt.strip()}'. Output ONLY the raw application text in English. Do NOT write about opening apps (WhatsApp, Facebook, etc.) and do NOT include any conversational fillers."
        
        application_reply = call_groq_direct_fallback(prompt_for_write)
        
        # Notepad Execution Injection
        update_gui_status("Writing to Notepad...")
        try:
            subprocess.Popen(["notepad.exe"])
            await asyncio.sleep(2.0) # Wait for UI to open
            pyautogui.write(application_reply, interval=0.015)
        except Exception as e:
            print(f"⚠️ Notepad automation failed: {e}")
            
        print(f"\n📄 [GENERATED DOCUMENT CORE OUTPUT]:\n{application_reply}\n")
        reply = "Sir, application generate karke Notepad par successfully type kar di hai."
        update_gui_status("Speaking...", maya_reply=reply)
        await asyncio.to_thread(TextToSpeech, reply)

    # Persona Identities Framework
    if not has_msg_keyword and not local_batch and not is_dynamic_query and not any(w in query_words for w in ["write", "application", "generate"]):
        if "who are you" in query_clean or "tell me about yourself" in query_clean or "identity" in query_clean or query_clean == "maya":
            reply = "I am Maya, an advanced AI operational core framework custom built to manage automated application nodes and digital system parameters."
            update_gui_status("Speaking...", maya_reply=reply)
            await asyncio.to_thread(TextToSpeech, reply)
            return True

        if "founder" in query_clean or "creator" in query_clean or "banya" in query_clean or "built you" in query_clean:
            reply = "I was conceptualized and engineered by Nishant Chaudhary, designed to act as an adaptive automation and smart assistance workspace handler."
            update_gui_status("Speaking...", maya_reply=reply)
            await asyncio.to_thread(TextToSpeech, reply)
            return True

    if "time" in query_words and not has_cascaded_intents:
        current_time = time.strftime("%I:%M %p")
        reply = f"Sir, abhi time ho raha hai {current_time}."
        update_gui_status("Speaking...", maya_reply=reply)
        await asyncio.to_thread(TextToSpeech, reply)
        return True

    # ======================================================================
    # ⚡ SEQUENCE STEP 5: THE GOD-MODE AGI MESSAGING ROUTER
    # ======================================================================
    if has_msg_keyword:
        update_gui_status("Processing AGI Intent...")
        print("🎯 [GOD-MODE RADAR] Parsing communication tokens agentically...")
        
        person = "None"
        payload = "None"
        app_target = "whatsapp" if "whatsapp" in query_clean else "instagram"
        
        try:
            parsed_intent = await asyncio.to_thread(UniversalIntentParser, user_query)
            app_target = parsed_intent.get("app", "whatsapp").lower()
            person = str(parsed_intent.get("target", "None")).strip()
            payload = str(parsed_intent.get("payload", "None"))
        except Exception as api_err:
            print(f"⚠️ [GEMINI CRASH] Quota Choked. Hot-swapping to Groq Llama Agent nodes...")
            groq_intent = await asyncio.to_thread(call_groq_intent_parser, user_query)
            if groq_intent:
                app_target = groq_intent.get("app", app_target).lower()
                person = str(groq_intent.get("target", "None")).strip()
                payload = str(groq_intent.get("payload", "None"))

        if person == "None" or payload == "None" or person.strip() == "" or payload.strip() in ["None", ""]:
            print("⚠️ [LOCAL AGENT BYPASS] Processing text mapping slicing boundaries...")
            text_raw = user_query.lower().strip("?,.! ")
            
            for sep in [" ko message bhej ki ", " ko message bhejo ki ", " ko bol ki ", " ko bolo ki ", " ko dm karo ki ", " ko hello bhej ", " ko message bhej "]:
                if sep in text_raw:
                    parts = text_raw.split(sep)
                    payload = parts[1].strip()
                    left_side = parts[0]
                    for prefix in ["whatsapp per ", "whatsapp par ", "instagram per ", "instagram par ", "insta per ", "insta par ", "open whatsapp ", "open instagram "]:
                        left_side = left_side.replace(prefix, "")
                    person = left_side.replace("maya ", "").strip().capitalize()
                    break
            
            if (person == "None" or person.strip() == "") and " ko " in text_raw:
                parts = text_raw.split(" ko ")
                left_side = parts[0]
                for prefix in ["whatsapp per ", "whatsapp par ", "instagram per ", "instagram par ", "insta per ", "insta par "]:
                    left_side = left_side.replace(prefix, "")
                person = left_side.replace("maya ", "").strip().capitalize()
                
                right_side = parts[1]
                for suffix in [" message bhej", " message bhejo", " bhej", " bhejo", " dm karo", " bol", " bolo"]:
                    if right_side.endswith(suffix):
                        right_side = right_side[:len(right_side)-len(suffix)].strip()
                payload = right_side.strip()

        if person != "None" and person.strip() != "":
            person = person.strip("?,.! ")

        if person != "None" and payload != "None" and payload.strip() not in ["None", ""]:
            update_gui_status(f"Automating...")
            active_text = get_active_browser_text().lower()
            
            if "whatsapp" in app_target or "whatsapp" in query_clean:
                print(f"🎙️ [OpenCV Overdrive] Target: '{person}' | Message: '{payload}'")
                if "whatsapp" not in active_text:
                    async for result in TranslateAndExecute(["open whatsapp"]):
                        await asyncio.sleep(0.5)
                    await asyncio.sleep(4.5)  
                
                success = send_whatsapp_message_via_typing(person, payload)
                if not success:
                    success = universal_ui_click_and_type(target_element_name="search_bar", text_to_type=person)
                if success:
                    reply = f"Message dispatched to {person} on WhatsApp."
                    update_gui_status("Speaking...", maya_reply=reply)
                    await asyncio.to_thread(TextToSpeech, reply)
                if not has_cascaded_intents:
                    return True
                
            elif "instagram" in app_target or "insta" in query_clean:
                print(f"🎙️ [OpenCV Overdrive] Targeting Instagram DM Layout: '{person}'")
                if "instagram" not in active_text and "insta" not in active_text:
                    async for result in TranslateAndExecute(["open instagram"]):
                        await asyncio.sleep(0.5)
                    await asyncio.sleep(4.0)
                else:
                    pyautogui.click(600, 400) 
                    await asyncio.sleep(0.3)
                
                global last_messaged_person
                is_already_open = False
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                msg_box_img = os.path.join(base_dir, "Data", "message_input.png")
                
                if os.path.exists(msg_box_img) and last_messaged_person == person.lower():
                    try:
                        res_check = cv2.matchTemplate(cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR), cv2.imread(msg_box_img), cv2.TM_CCOEFF_NORMED)
                        _, max_val_check, _, _ = cv2.minMaxLoc(res_check)
                        if max_val_check >= 0.70:
                            is_already_open = True
                    except:
                        pass

                if is_already_open:
                    search_success = universal_ui_click_and_type("message_input", payload)
                    if search_success:
                        reply = f"Sent to {person} again on Instagram DM."
                        update_gui_status("Speaking...", maya_reply=reply)
                        await asyncio.to_thread(TextToSpeech, reply)
                        if not has_cascaded_intents:
                            return True
                else:
                    pyautogui.press('escape'); await asyncio.sleep(0.3)
                    search_success = universal_ui_click_and_type("search_bar", person)
                    if search_success:
                        await asyncio.sleep(1.0)
                        universal_ui_click_and_type("message_input", payload)
                        last_messaged_person = person.lower()
                        if not has_cascaded_intents:
                            return True

    # ======================================================================
    # ⚡ SEQUENCE STEP 6: SILICONFLOW SYNTHESIS PIPELINE (IMAGE PROMPT EXTRACTION FIX)
    # ======================================================================
    is_creation_task = any(w in query_words for w in ["image", "photo", "picture"]) or "generate" in query_words
    if is_creation_task:
        print("🎨 [IMAGE SYNTHESIS DOWNSTREAM] Invoking isolated background generation engine pipeline nodes.")
        update_gui_status("Generating Image...")
        
        # 🔥 BUG FIX 3: Dynamic Slicing instead of replacement
        img_prompt = query_clean
        markers = ["image of", "picture of", "photo of", "generate", "banao"]
        for marker in markers:
            if marker in img_prompt:
                img_prompt = img_prompt.split(marker)[-1].strip()
                break
                
        if img_prompt.startswith("a "): img_prompt = img_prompt[2:].strip()
        if img_prompt.startswith("an "): img_prompt = img_prompt[3:].strip()
        if img_prompt.startswith("and "): img_prompt = img_prompt[4:].strip()

        def background_image_generator(prompt_text):
            global IMAGE_GENERATION_PENDING, LATEST_GENERATED_IMAGES
            try:
                GenerateImages(prompt_text)
                time.sleep(1.0)
                import glob
                base_data_folder = os.path.join(BASE_DIR, "Data")
                LATEST_GENERATED_IMAGES = sorted(glob.glob(os.path.join(base_data_folder, "*.jpg")), key=os.path.getmtime)[-3:]
                IMAGE_GENERATION_PENDING = True
                print(f"✅ [SYNTHESIS TRACK] Assets ready for target prompt: '{prompt_text}'")
            except Exception as trace:
                print(f"❌ Background Image Synthesis Failure: {trace}")
                IMAGE_GENERATION_PENDING = False

        reply = f"Sir, background me {img_prompt} ki unique images generate ho rhi hai. Ready hone par show kar dungi."
        update_gui_status("Speaking...", maya_reply=reply)
        await asyncio.to_thread(TextToSpeech, reply)
        threading.Thread(target=background_image_generator, args=(img_prompt,), daemon=True).start()
        return True

    # ======================================================================
    # ⚡ SEQUENCE STEP 7: GENERAL CONVERSATIONAL ORCHESTRATOR
    # ======================================================================
    try:
        if not local_batch:
            print("🧠 [PRIMARY CORE FALLBACK] Forwarding remaining query structure to Gemini logic array...")
            intents = await asyncio.to_thread(FirstLayerDMM, user_query)
            print(f"🤖 Extracted Fallback Intents: {intents}")

            is_whistle_intent = any(w in query_clean for w in ["whistle", "vishal", "seeti", "chutki", "bajau", "bajaunga"])
            is_close_command = any(c in query_clean for c in ["band", "close", "delete", "remove", "rehne de"])
            
            if is_whistle_intent and not is_close_command and intents:
                queued_actions = []
                for intent in intents:
                    intent_str = str(intent).strip()
                    if intent_str.startswith("open ") or intent_str.startswith("play "):
                        action_type = "play_song:" if intent_str.startswith("play ") else ""
                        clean_target = intent_str.replace("open ", "").replace("play ", "").strip()
                        queued_actions.append(f"{action_type}{clean_target}")
                    else:
                        app_dictionary = {
                            "whatsapp": "whatsapp", "youtube": "youtube", "yt": "youtube",
                            "facebook": "open facebook", "fb": "open facebook", "instagram": "open instagram",
                            "insta": "open instagram", "linkedin": "open linkedin", "link": "open linkedin", "telegram": "open telegram",
                            "gmail": "open gmail"
                        }
                        for key in app_dictionary:
                            if key in intent_str.lower() and app_dictionary[key] not in queued_actions:
                                queued_actions.append(app_dictionary[key])

                if queued_actions:
                    final_queue_string = ",".join(queued_actions)
                    intents = [f"set_snap_action {final_queue_string}"]

            for intent in intents:
                if intent.startswith("set_snap_action"):
                    target_queue = intent.replace("set_snap_action", "").strip()
                    snap_file_path = os.path.join(BASE_DIR, "Data", "SnapAction.txt")
                    os.makedirs(os.path.dirname(snap_file_path), exist_ok=True)
                    with open(snap_file_path, "w", encoding="utf-8") as sf:
                        sf.write(target_queue)
                    return True

            automation_commands = []
            is_conversational = False
            conversational_type = "general"
            
            for intent in intents:
                intent_lower = str(intent).strip().lower()
                if intent_lower.startswith("close") or intent_lower.startswith("delete") or intent_lower.startswith("open") or intent_lower.startswith("start"):
                    automation_commands.append(intent)
                elif intent_lower.startswith("general") or intent_lower.startswith("chat"):
                    is_conversational = True
                    conversational_type = "general"
                elif intent_lower.startswith("realtime") or intent_lower.startswith("google search") or intent_lower.startswith("youtube search"):
                    is_conversational = True
                    conversational_type = "realtime"
                    
            if automation_commands:
                update_gui_status("Executing Tasks...")
                try:
                    async for result in TranslateAndExecute(automation_commands):  
                        await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"❌ Automation Task Failure: {e}")
                
            if is_conversational:
                update_gui_status("Thinking...")
                if conversational_type == "realtime":
                    reply = RealtimeSearchEngine(user_query)   
                else:
                    reply = ChatBot(user_query)               
                    
                update_gui_status("Speaking...", maya_reply=reply)
                await asyncio.to_thread(TextToSpeech, clean_tts_string(reply))
                return True

    except Exception as chat_err:
        print(f"⚠️ [CRITICAL OVERDRIVE DROP] Fallback routing engaged: {chat_err}")
        try:
            prompt_for_groq = f"Respond directly to this query in short mix Hindi/English: {user_query}"
            reply = await asyncio.to_thread(call_groq_direct_fallback, prompt_for_groq)
            update_gui_status("Speaking...", maya_reply=reply)
            await asyncio.to_thread(TextToSpeech, clean_tts_string(reply))
        except:
            pass

    print("🧹 Resetting focus nodes naturally...")
    pyautogui.press('escape')
    return True

async def main_Maya_loop():
    global IMAGE_GENERATION_PENDING, LATEST_GENERATED_IMAGES
    print("🧠 Maya Core Orchestrator Initializing...")
    update_gui_status("Initializing...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    snap_file_path = os.path.join(base_dir, "Data", "SnapAction.txt")
    if os.path.exists(snap_file_path):
        try: os.remove(snap_file_path)
        except: pass

    asyncio.create_task(continuous_snap_monitor())
    threading.Thread(target=launch_frontend_gui, daemon=True).start()
    
    print("⏳ Waiting for Pygame Window Canvas to capture OS window focus pools...")
    await asyncio.sleep(5.0) 
    
    simple_greet = "Hello Nishant Sir, Maya here. I am online, how can I help you?"
    update_gui_status("Speaking...", maya_reply=simple_greet)
    print("\n🎙️ Maya is Active & Initializing Speech Modules...")
    
    # 🔥 FIX 1: Clean string + Audio Buffer (Mic start hone se pehle speaker ko finish hone do)
    await asyncio.to_thread(TextToSpeech, clean_tts_string(simple_greet))
    await asyncio.sleep(0.8) 
    
    last_processed_query = ""
    
    while True:
        try:
            current_mic_mode = get_gui_mic_status()
            if current_mic_mode == "MUTED":
                update_gui_status("Muted...")
                await asyncio.sleep(0.4)
                continue

            if IMAGE_GENERATION_PENDING and LATEST_GENERATED_IMAGES:
                alert_phrase = "Sir, images generate ho gayi hain. Kya main in images ko aapko open karke dikhau?"
                update_gui_status("Speaking...", maya_reply=alert_phrase)
                
                # 🔥 FIX 2: Confirmation maangte waqt bhi buffer add kiya taaki aawaz kate na
                await asyncio.to_thread(TextToSpeech, clean_tts_string(alert_phrase))
                await asyncio.sleep(0.8)
                
                update_gui_status("Listening for confirmation...")
                user_confirmation = await asyncio.to_thread(SpeechRecognition)
                
                if get_gui_mic_status() == "MUTED":
                    continue
                
                if user_confirmation and len(user_confirmation.strip()) >= 2:
                    StopAudio() # Safety stop
                    await handle_user_query(user_confirmation)
                continue
                
            update_gui_status("Listening...") 
            user_query = await asyncio.to_thread(SpeechRecognition)
            
            if get_gui_mic_status() == "MUTED":
                continue
                
            if not user_query or len(user_query.strip()) < 2:
                await asyncio.sleep(0.2)
                continue
                
            cleaned_query = user_query.strip().lower()
            skip_phrases = ["how can i help you", "maya here", "systems are fully operational", "something specific you'd like me to write"]
            if any(phrase in cleaned_query for phrase in skip_phrases) or cleaned_query == last_processed_query:
                await asyncio.sleep(0.2)
                continue
                
            print(f"👤 User Said: {user_query}")
            last_processed_query = cleaned_query
            
            update_gui_status("Processing...", user_text=user_query)
            
            StopAudio()
            await handle_user_query(user_query)
            await asyncio.sleep(0.3)
            
        except SystemExit:
            print("\n👋 Maya successfully terminated.")
            break
        except Exception as loop_error:
            print(f"⚠️ Safe Stream Thread Reset Triggered: {loop_error}")
            await asyncio.sleep(0.5)
            continue

if __name__ == "__main__":
    try:
        update_gui_status("Listening...")
        try:
            with open(MIC_FILE, "w", encoding="utf-8") as f:
                json.dump({"mic_state": "ACTIVE"}, f)
        except: pass
        
        asyncio.run(main_Maya_loop())
    except KeyboardInterrupt:
        print("\nExiting Maya...")