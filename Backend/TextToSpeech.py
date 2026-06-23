import pygame
import random
import asyncio
import edge_tts
import os
import time
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-ChristopherNeural")

SHOULD_STOP_AUDIO = False

# Strict Initialization Module Framework
def EnsureMixerInit():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception as e:
        print(f"⚠️ Audio Driver Init Fallback Triggered: {e}")

async def textToAudioFile(text) -> None:
    file_path = r"Data\speech.mp3"
    
    # Safe audio handle releasing block to prevent PermissionError
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.unload()
    except:
        pass
        
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
            
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(file_path)

def StopAudio():
    """
    Safely terminates any active voice stream or music overlay 
    bina program run context ko crash kiye.
    """
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
    except Exception as tts_err:
        pass

def TextToSpeech(Text, func=lambda r=None: True):
    global SHOULD_STOP_AUDIO
    SHOULD_STOP_AUDIO = False
    file_path = r"Data\speech.mp3"
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(textToAudioFile(Text), loop)
        while not future.done():
            time.sleep(0.05)
    else:
        loop.run_until_complete(textToAudioFile(Text))

    try:
        # Core fix: Safe state checking
        EnsureMixerInit()
        
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            if SHOULD_STOP_AUDIO or func() == False:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                break
            pygame.time.Clock().tick(10)
            
        return True
    except Exception as e:
        print(f"Error in TTS execution block: {e}")
        return False
    finally:
        # FIXED: Quit() ko permanently hata diya taaki hardware system process loop layer active rhe
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.unload()
        except:
            pass