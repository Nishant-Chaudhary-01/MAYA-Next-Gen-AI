import os
import sys
import asyncio
import numpy as np
import sounddevice as sd
import subprocess
import time
import pygame
from Backend.TextToSpeech import StopAudio

# Direct import of your automation engine core to execute native intents
from Backend.Automation import TranslateAndExecute

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP_FILE = os.path.join(BASE_DIR, "Data", "SnapAction.txt")

CHANNELS = 1
RATE = 16000  
CHUNK = 1024  

is_cooling_down = False
last_file_creation_time = 0
last_known_actions = ""

def run_async_automation(commands):
    """Bypasses browser layers and executes the native automation coroutine inside a sub-thread loop."""
    async def worker():
        try:
            # Direct pass-through execution into your existing automation node architecture
            async for result in TranslateAndExecute(commands):
                print(f"⚙️ Whistle Automation Native Result: {result}")
        except Exception as e:
            print(f"❌ Whistle Task Async Failure: {e}")
            
    # Safely creates and manages a background execution loop for the automation thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(worker())
    loop.close()

def execute_single_action(action_string):
    """Directly routes actions either to web portals or targets native play nodes directly."""
    action_clean = action_string.lower().strip()
    if not action_clean:
        return

    # 🚀 THE BULLETPROOF NATIVE AUTOMATION ROUTER
    if action_clean.startswith("play_song:"):
        song_name = action_string.split(":", 1)[1].strip()
        
        # We rebuild the clean intent array just like FirstLayerDMM does natively
        native_intent = [f"play {song_name}"]
        print(f"⚙️ Injecting direct intent into automation layer: {native_intent}")
        
        # Spawning a parallel non-blocking operating thread to process the video instantly
        import threading
        t = threading.Thread(target=run_async_automation, args=(native_intent,))
        t.daemon = True
        t.start()
        
    else:
        known_urls = {
            "youtube": "https://www.youtube.com",
            "whatsapp": "https://web.whatsapp.com",
            "facebook": "https://www.facebook.com",
            "fb": "https://www.facebook.com",
            "instagram": "https://www.instagram.com",
            "insta": "https://www.instagram.com",
            "linkedin": "https://www.linkedin.com"
        }
        target_link = known_urls.get(action_clean, f"https://www.google.com/search?q={action_clean}")

        try:
            subprocess.Popen(
                f'start chrome "{target_link}"',
                shell=True,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        except:
            os.system(f'start chrome "{target_link}"')

def audio_callback(indata, frames, time_info, status):
    global is_cooling_down, last_file_creation_time, last_known_actions
    if status or is_cooling_down:
        return

    try:
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            if last_file_creation_time > 0:
                last_file_creation_time = time.time()  
            return
    except:
        pass

    if os.path.exists(SNAP_FILE):
        raw_actions = ""
        try:
            with open(SNAP_FILE, "r", encoding="utf-8") as sf:
                raw_actions = sf.read().strip()
        except:
            pass
        
        if raw_actions and raw_actions != "":
            current_time = time.time()
            
            if raw_actions != last_known_actions or last_file_creation_time == 0:
                last_known_actions = raw_actions
                last_file_creation_time = current_time
                return
                
            if (current_time - last_file_creation_time) < 4.0:
                return

            # FFT SIGNAL ANALYSIS
            audio_samples = indata[:, 0]
            fft_data = np.abs(np.fft.rfft(audio_samples))
            frequencies = np.fft.rfftfreq(len(audio_samples), d=1.0/RATE)

            whistle_mask = (frequencies >= 800) & (frequencies <= 3200)
            whistle_energy = np.max(fft_data[whistle_mask]) if np.any(whistle_mask) else 0.0
            
            total_energy = np.sum(fft_data) + 1e-5
            peak_index = np.argmax(fft_data)
            peak_frequency = frequencies[peak_index]

            surrounding_energy = np.sum(fft_data[max(0, peak_index-2):min(len(fft_data), peak_index+3)])
            concentration_ratio = surrounding_energy / total_energy

            if whistle_energy > 0.015 and concentration_ratio > 0.18:
                if 800 <= peak_frequency <= 3200:
                    is_cooling_down = True
                    print(f"\n⚡ [🔥 SYSTEM SHIELD] Whistle detected! Firing native code execution layer...")
                    
                    try:
                        os.remove(SNAP_FILE)
                    except:
                        pass
                    
                    action_list = raw_actions.split(",")
                    for action in action_list:
                        execute_single_action(action)
                        time.sleep(0.3)
                    
                    last_known_actions = ""
                    last_file_creation_time = 0
    else:
        last_known_actions = ""
        last_file_creation_time = 0
        StopAudio()

async def continuous_snap_monitor():
    global is_cooling_down
    print("\n🎙️ Jarvis Custom Calibrated Whistle Engine: ACTIVE 🚀")
    try:
        stream = sd.InputStream(channels=CHANNELS, samplerate=RATE, blocksize=CHUNK, callback=audio_callback)
        with stream:
            while True:
                if is_cooling_down:
                    await asyncio.sleep(1.5)
                    is_cooling_down = False
                await asyncio.sleep(0.05)
    except Exception as e:
        print(f"❌ Engine Error: {e}")