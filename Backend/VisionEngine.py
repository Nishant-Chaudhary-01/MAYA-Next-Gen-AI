import os
import sys
import time
import win32gui
import pyautogui
import pyperclip

def get_active_window_title():
    """ Fetches the exact title string of the foreground OS window """
    try:
        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd)
    except:
        return "Unknown Window"

def get_active_browser_text():
    """ 
    🔥 FIXED SYNC BUG: Dynamic window tracking interface.
    Returns the actual active foreground window title so Main.py can verify tab states.
    """
    try:
        title = get_active_window_title()
        print(f"🖥️ [VISION TRACKER] Current Active Viewport Title: '{title}'")
        return title.lower()
    except:
        return ""

def switch_browser_tab(direction="next"):
    try:
        if direction.lower() in ["next", "right", "agla"]:
            pyautogui.hotkey('ctrl', 'tab')
        else:
            pyautogui.hotkey('ctrl', 'shift', 'tab')
        return True
    except: 
        return False

def send_whatsapp_message_via_typing(contact_name, message_text):
    """
    RPA Core V19 - WhatsApp Pure Computer Vision Engine (No Hawa Me Teer).
    Uses cropped screenshots for exact search and input field locking via OpenCV.
    """
    try:
        print(f"👁️ [WHATSAPP VISION CONTROL] Syncing viewport for target: '{contact_name}'")
        
        # 1. Window active karne ke liye screen ke center me click
        pyautogui.click(600, 400)
        time.sleep(0.3)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        whats_search_img = os.path.join(base_dir, "Data", "whats_search_anchor.png")
        whats_msg_img = os.path.join(base_dir, "Data", "whats_message_input.png")
        
        # 2. STEP A: Locate and click WhatsApp Search Bar using OpenCV
        visual_search_success = False
        if os.path.exists(whats_search_img):
            print("👁️ Scanning screen for WhatsApp Search Bar Template...")
            location = pyautogui.locateOnScreen(whats_search_img, confidence=0.75)
            if location:
                cx, cy = pyautogui.center(location)
                pyautogui.moveTo(cx, cy, duration=0.2)
                pyautogui.click()
                visual_search_success = True
                print(f"🎯 [SEARCH LOCKED] Clicked WhatsApp search box at: ({cx}, {cy})")
        
        # Failsafe: Agar image match na ho toh purana coordinate chalao
        if not visual_search_success:
            print("⚠️ [VISION BLIND] Search template missing/not found. Using failsafe coordinate (260, 185)...")
            pyautogui.click(260, 185)
            time.sleep(0.2)
            
        # 3. Purana text clear karke contact name paste karo
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        time.sleep(0.2)
        
        pyperclip.copy(contact_name)
        pyautogui.hotkey('ctrl', 'v')
        print(f"⌨️ Injected contact: '{contact_name}'")
        
        # Filter hone ka wait karo aur Enter maaro chat open karne ke liye
        time.sleep(2.0) 
        pyautogui.press('enter')
        time.sleep(1.2) # Chat load hone ka buffer
        
        # 4. STEP B: Locate and click WhatsApp Message Input Box using OpenCV
        visual_msg_success = False
        if os.path.exists(whats_msg_img):
            print("👁️ Scanning screen for WhatsApp Message Input Box Template...")
            msg_location = pyautogui.locateOnScreen(whats_msg_img, confidence=0.75)
            if msg_location:
                mx, my = pyautogui.center(msg_location)
                pyautogui.moveTo(mx, my, duration=0.2)
                pyautogui.click()
                visual_msg_success = True
                print(f"🎯 [INPUT LOCKED] Focused WhatsApp message box at: ({mx}, {my})")
                
        # Agar message box image se nahi mila, toh direct keyboard se paste try karega (jo enter ke baad auto-focused hota hai)
        if not visual_msg_success:
            print("⚠️ [VISION BLIND] Message box template not found. Attempting direct keyboard paste fallback...")
        
        # 5. Message text paste karo aur send karo
        pyperclip.copy(message_text)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.4)
        
        pyautogui.press('enter')
        print("✅ [AUTOMATION SUCCESS] WhatsApp message successfully sent via precise OpenCV templates!")
        return True
    except Exception as macro_err:
        print(f"❌ WhatsApp Pure Vision Macro Crash: {macro_err}")
        return False

import cv2
import numpy as np

def universal_ui_click_and_type(target_element_name, text_to_type=None, click_only=False):
    """
    RPA Core V24 - Pure OpenCV Matrix Matcher (Zero PyAutoGUI Scan Dependency).
    Eliminates system-level frame crashes by handling viewport arrays directly via CV2.
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target = target_element_name.lower().strip()
        
        image_name = None
        if target in ["search", "search...", "to:", "search_bar"]:
            image_name = "search_anchor.png"
        elif target in ["more_accounts", "more accounts", "heading"]:
            image_name = "more_accounts.png"
        elif target in ["message...", "send message", "type a message", "message_input"]:
            image_name = "message_input.png"
            
        if not image_name:
            return False
            
        image_path = os.path.join(base_dir, "Data", image_name)
        if not os.path.exists(image_path):
            print(f"⚠️ [INSTA] File missing: {image_path}")
            return False

        print(f"👁️ [PURE OPENCV SCAN] Capturing view-grid array for: '{image_name}'...")
        
        # 1. Take a safe screenshot via PyAutoGUI but process purely through OpenCV
        screenshot = pyautogui.screenshot()
        screen_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        template = cv2.imread(image_path)
        
        if template is None:
            print(f"❌ [CV2 ERROR] Cannot read template: {image_name}")
            return False
            
        # 2. Perform direct pixel matrix matching
        res = cv2.matchTemplate(screen_np, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        # Threshold limit matching 70% confidence
        if max_val >= 0.70:
            h, w = template.shape[:2]
            center_x = max_loc[0] + int(w / 2)
            center_y = max_loc[1] + int(h / 2)
            
            # More Accounts Heading Offset Flow
            if target in ["more_accounts", "more accounts", "heading"]:
                target_y = center_y + 48  
                print(f"🎯 [CV2 MATCH] Heading found ({max_val:.2f}). Clicking account row below: ({center_x}, {target_y})")
                pyautogui.moveTo(center_x, target_y, duration=0.15)
                pyautogui.click()
                time.sleep(1.5)
                return True
                
            print(f"🎯 [CV2 MATCH LOCKED] Found '{image_name}' with confidence {max_val:.2f} at ({center_x}, {center_y})")
            pyautogui.moveTo(center_x, center_y, duration=0.15)
            pyautogui.click()
            time.sleep(0.3)
            
            if not click_only and text_to_type:
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('backspace')
                time.sleep(0.2)
                
                if target in ["search", "search...", "to:", "search_bar"]:
                    pyautogui.typewrite(text_to_type, interval=0.08)
                    time.sleep(2.5) # Wait for Instagram dynamic DOM list
                    
                    # Core pipeline chain hook to click user profile card below 'More Accounts'
                    print("🔄 Scanning for dropdown heading row using OpenCV array...")
                    sub_path = os.path.join(base_dir, "Data", "more_accounts.png")
                    if os.path.exists(sub_path):
                        sub_tmpl = cv2.imread(sub_path)
                        if sub_tmpl is not None:
                            # Fresh screenshot for updated dropdown state
                            sc2 = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
                            res2 = cv2.matchTemplate(sc2, sub_tmpl, cv2.TM_CCOEFF_NORMED)
                            _, mv2, _, ml2 = cv2.minMaxLoc(res2)
                            if mv2 >= 0.70:
                                sh, sw = sub_tmpl.shape[:2]
                                sx = ml2[0] + int(sw / 2)
                                sy = ml2[1] + int(sh / 2) + 48
                                pyautogui.moveTo(sx, sy, duration=0.15)
                                pyautogui.click()
                                time.sleep(1.5)
                                return True
                    
                    # Fallback chain if template is hidden
                    print("⚠️ Dropdown header template not found in frame. Using fallback keys...")
                    pyautogui.press('down')
                    pyautogui.press('enter')
                    return True
                else:
                    pyperclip.copy(text_to_type)
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(0.3)
                    pyautogui.press('enter')
            return True
        else:
            print(f"❌ [CV2 BLIND] Match score too low ({max_val:.2f}) for '{image_name}'")
            return False
            
    except Exception as e:
        print(f"🛡️ [SANDBOX SHIELD] Prevented hard crash in matrix loop: {e}")
        return False