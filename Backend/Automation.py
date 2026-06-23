import os
import sys
import time
import keyboard
import subprocess
import pyautogui
import pygetwindow as gw
from AppOpener import open as appopen, close as appclose
import pywhatkit
import requests
from dotenv import dotenv_values
from groq import Groq

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
client = Groq(api_key=GroqAPIKey)

def OpenNotepad(File):
    try:
        subprocess.Popen(["notepad.exe", File])
        return True
    except:
        return False

def ContentWriterAI(prompt):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are an expert professional content writer. Write clean, complete templates without any conversational intro/outro text."}, {"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Groq API Engine Error: {e}")
        return "Error creating content templates."

async def Content(Topic):
    topic_clean = Topic.replace("Content ", "").strip()
    content = ContentWriterAI(topic_clean)
    file_path = fr"Data\{topic_clean.lower().replace(' ', '')}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    OpenNotepad(file_path)
    return f"Content saved to {file_path}"

async def YoutubeSearch(Topic):
    # HARD OVERRIDE: Direct Windows OS command to search YouTube
    url = f"https://www.youtube.com/results?search_query={Topic}"
    subprocess.Popen(f'start chrome "{url}"', shell=True)
    return "YouTube search executed via Native Shell."

async def PlayYouTube(query):
    print("🧹 Autopilot: Terminating previous playing tab instance...")
    try:
        pyautogui.hotkey('ctrl', 'w')
        time.sleep(0.3)
    except:
        pass
    print(f"🎬 Opening YouTube to play: {query}...")
    pywhatkit.playonyt(query)
    return "Streaming requested video on YouTube node."

# ======================================================================
# UNBREAKABLE OS-LEVEL SHELL COMMAND FOR OPENING APPS/WEBSITES
# ======================================================================
async def OpenApp(app):
    app_lower = app.lower().strip()
    
    known_websites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://www.github.com",
        "instagram": "https://www.instagram.com",
        "insta": "https://www.instagram.com",
        "whatsapp": "https://web.whatsapp.com",
        "facebook": "https://www.facebook.com",
        "fb": "https://www.facebook.com",
        "twitter": "https://www.twitter.com",
        "linkedin": "https://www.linkedin.com"
    }
    
    if app_lower in known_websites:
        target_url = known_websites[app_lower]
        print(f"🌐 Autopilot Shell: Force launching cloud portal -> {target_url}")
        try:
            # Direct Windows OS Terminal command pipeline execution (100% pop-up guarantee)
            subprocess.Popen(f'start chrome "{target_url}"', shell=True)
            return f"Opened {app_lower} via Windows Native Shell Core."
        except Exception as shell_err:
            print(f"⚠️ Primary Chrome Shell Failed, firing fallback Edge pipeline: {shell_err}")
            subprocess.Popen(f'start msedge "{target_url}"', shell=True)
            return f"Opened {app_lower} via Backup Shell Node."
        
    try:
        appopen(app, match_closest=True, output=False, throw_error=True)
        return f"Opened application {app}"
    except:
        search_url = f"https://www.google.com/search?q={app}"
        subprocess.Popen(f'start chrome "{search_url}"', shell=True)
        return f"Browsing query mapping for {app}"

async def CloseApp(app):
    app_lower = app.lower().strip()
    web_tabs = {
        "facebook": "facebook", "fb": "facebook",
        "instagram": "instagram", "insta": "instagram",
        "whatsapp": "whatsapp", "youtube": "youtube",
        "yt": "youtube", "google": "google",
        "twitter": "x", "linkedin": "linkedin",
        "x": "x", "x.com": "x"
    }
    
    generic_keywords = ["song", "video", "browser", "old song", "music", "all song", "this tab", "exit", "close", "it", "this"]
    
    matched_site = None
    for key, val in web_tabs.items():
        if key in app_lower or val in app_lower:
            matched_site = val
            break
            
    if matched_site:
        print(f"🎯 Sniper Target Acquired: Native OS detection running for '{matched_site}' tab layer...")
        try:
            chrome_windows = [w for w in gw.getAllTitles() if "chrome" in w.lower() or "edge" in w.lower() or "brave" in w.lower()]
            if chrome_windows:
                browser_win = gw.getWindowsWithTitle(chrome_windows[0])[0]
                browser_win.activate()
                time.sleep(0.2)
            
            pyautogui.hotkey('ctrl', '1')
            time.sleep(0.2)
            
            for tab_index in range(12):
                active_title = gw.getActiveWindow().title.lower()
                print(f"👀 Scanning Window Title: '{active_title}'")
                
                if matched_site == "x":
                    is_match = (" / x" in active_title) or ("x.com" in active_title) or (active_title.startswith("x "))
                else:
                    is_match = matched_site in active_title
                
                if is_match:
                    print(f"🚀 Match Confirmed! Wiping targeted tab: '{matched_site}'")
                    pyautogui.hotkey('ctrl', 'w')
                    time.sleep(0.2)
                    return f"Successfully targeted and terminated {matched_site} tab natively."
                
                pyautogui.hotkey('ctrl', 'tab')
                time.sleep(0.15)
                
            return f"Scan finished. Target tab '{matched_site}' was not found."
        except Exception as e:
            print(f"❌ Native OS Tab Tracking Failed: {e}")
            pyautogui.hotkey('ctrl', 'w')
            return "Executed emergency fallback tab closure."
            
    elif any(keyword in app_lower for keyword in generic_keywords) or app_lower == "":
        print("🛑 System Trace: Dropping current active tab via hotkey layer...")
        try:
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(0.1)
            return "Closed current active tab context."
        except Exception as e:
            print(f"⚠️ Safe Tab Closure Exception: {e}")
            
    try:
        appclose(app, match_closest=True, output=False, throw_error=True)
        return f"Closed application {app}"
    except:
        try:
            pyautogui.hotkey('ctrl', 'w')
            return f"Issued browser tab fallback closer for {app}"
        except:
            return f"Could not find active process template for {app}"

async def SystemTask(command):
    cmd = command.lower().strip()
    if "mute" in cmd:
        keyboard.press_and_release("volume mute")
    elif "volume up" in cmd:
        for _ in range(5): keyboard.press_and_release("volume up")
    elif "volume down" in cmd:
        for _ in range(5): keyboard.press_and_release("volume down")
    return "System command processed."

async def TranslateAndExecute(commands: list[str]):
    if not commands:
        return
    for command in commands:
        cmd_clean = command.lower().strip()
        try:
            if cmd_clean.startswith("open "):
                target = cmd_clean.replace("open ", "").strip()
                yield await OpenApp(target)
            elif cmd_clean.startswith("close ") or cmd_clean.startswith("delete ") or cmd_clean == "exit":
                target = cmd_clean.replace("close ", "").replace("delete ", "").strip()
                yield await CloseApp(target)
            elif cmd_clean.startswith("play "):
                target = cmd_clean.replace("play ", "").strip()
                yield await PlayYouTube(target)
            elif cmd_clean.startswith("content "):
                target = cmd_clean.replace("content ", "").strip()
                yield await Content(target)
            elif cmd_clean.startswith("youtube search "):
                target = cmd_clean.replace("youtube search ", "").strip()
                yield await YoutubeSearch(target)
            elif cmd_clean.startswith("system ") or any(k in cmd_clean for k in ["mute", "volume"]):
                yield await SystemTask(cmd_clean)
        except Exception as e:
            print(f"⚠️ Warning inside TranslateAndExecute: {e}")
            continue