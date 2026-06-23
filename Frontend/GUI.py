# File Path: Frontend/GUI.py
import pygame
import os
import glob
import json
import sys
import ctypes
import threading
import time
import math
import psutil
import subprocess

# --- LIVE STATE TRACKING VARIABLES ---
current_status = "Listening..."
user_said_text = "Maya Console Active."
maya_response_text = ""  
STATUS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "Files", "Status.data"))
MIC_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "Files", "MicControl.data"))

# --- MIC TOGGLE STATES ---
mic_active = True  

# --- KEYBOARD INPUT GLOBALS ---
user_input_string = ""
is_input_box_active = False
cursor_visible = True
cursor_time_accumulator = 0

# --- UTILITY SYSTEM WIDGET GLOBALS ---
live_time = "00:00:00"
live_date = "01-01-2026"
battery_percent = 100
battery_plugged = False
wifi_status = "Disconnected"

def update_mic_file_state(is_active):
    """ Shared memory file configuration me state push karta hai """
    try:
        os.makedirs(os.path.dirname(MIC_FILE), exist_ok=True)
        with open(MIC_FILE, "w", encoding="utf-8") as f:
            json.dump({"mic_state": "ACTIVE" if is_active else "MUTED"}, f)
    except Exception as e:
        print(f"⚠️ Mic status write error: {e}")

# Initial Sync state check on execution boot
update_mic_file_state(mic_active)

def status_polling_worker():
    """ Read target shared file state and live user/assistant dialogue streams """
    global current_status, user_said_text, maya_response_text
    while True:
        try:
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # 🔥 FIXED: GUI is now the absolute Boss of its own visual state!
                    # Backend agar lag bhi kare, toh GUI override kar dega instantly.
                    if not mic_active:
                        current_status = "Muted..."
                    else:
                        if data and "status" in data:
                            # Agar backend abhi bhi Muted bhej raha hai par humne on kar diya, toh ignore karo
                            if data["status"] == "Muted...":
                                current_status = "Listening..."
                            else:
                                current_status = data["status"]

                    if data and "user_said" in data and data["user_said"].strip():
                        user_said_text = data["user_said"]
                    if data and "maya_response" in data:  
                        maya_response_text = data["maya_response"]
        except Exception:
            pass
        time.sleep(0.1)

def system_widgets_worker():
    global live_time, live_date, battery_percent, battery_plugged, wifi_status
    while True:
        try:
            t_struct = time.localtime()
            live_time = time.strftime("%I:%M:%S %p", t_struct)
            live_date = time.strftime("%A, %B %d, %Y", t_struct)

            battery = psutil.sensors_battery()
            if battery:
                battery_percent = battery.percent
                battery_plugged = battery.power_plugged

            cmd = "netsh wlan show interfaces"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, _ = process.communicate()
            
            found_ssid = False
            for line in stdout.split("\n"):
                if "SSID" in line and "BSSID" not in line:
                    wifi_status = f"Connected: {line.split(':')[1].strip()}"
                    found_ssid = True
                    break
            if not found_ssid:
                wifi_status = "Network Active (LAN)" if psutil.net_if_stats() else "Disconnected"
        except Exception:
            pass
        time.sleep(1.0)

def draw_text_wrapped(surface, text, font, color, rect, line_spacing=2):
    words = text.split(' ')
    box_w, box_h = rect[2], rect[3]
    x, y = rect[0], rect[1]
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] < box_w:
            current_line = test_line
        else:
            surface.blit(font.render(current_line, True, color), (x, y))
            y += font.size(current_line)[1] + line_spacing
            current_line = word + " "
            if y + font.size(current_line)[1] > rect[1] + box_h:
                return
    if current_line:
        surface.blit(font.render(current_line, True, color), (x, y))

def Start_Maya_GUI():
    global current_status, user_said_text, maya_response_text, user_input_string, is_input_box_active, cursor_visible, cursor_time_accumulator
    global live_time, live_date, battery_percent, battery_plugged, wifi_status, mic_active
    
    try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except: pass

    pygame.init()
    pygame.font.init()
    
    monitor_info = pygame.display.Info()
    screen_width = monitor_info.current_w
    screen_height = monitor_info.current_h
    
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN | pygame.NOFRAME | pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("Maya Virtual Control Dashboard")
    clock = pygame.time.Clock()

    base_dir = os.path.dirname(os.path.abspath(__file__)) 
    frame_folder = os.path.abspath(os.path.join(base_dir, "..", "Data", "MayaFrames"))
    frame_paths = sorted(glob.glob(os.path.join(frame_folder, "frame_*.jpg")))
    
    if not frame_paths:
        print(f"❌ Error: Frames directory empty at {frame_folder}")
        sys.exit()

    frames_cache = []
    for fp in frame_paths:
        loaded_img = pygame.image.load(fp).convert()
        scaled_img = pygame.transform.smoothscale(loaded_img, (screen_width, screen_height))
        frames_cache.append(scaled_img)

    panel_width = int(screen_width * 0.26)
    remaining_width = screen_width - panel_width

    # Layout Boxes Dimension Positioning 
    input_box_w = 720
    input_box_h = 56
    input_box_x = panel_width + (remaining_width - input_box_w) // 2
    input_box_y = screen_height - input_box_h - 55

    font_title = pygame.font.SysFont("Segoe UI", 26, bold=True)
    font_section = pygame.font.SysFont("Segoe UI", 15, bold=True)
    font_body = pygame.font.SysFont("Segoe UI", 14, bold=False)
    font_bold_data = pygame.font.SysFont("Segoe UI", 15, bold=True)
    font_clock = pygame.font.SysFont("Segoe UI", 32, bold=True)
    font_prompt = pygame.font.SysFont("Consolas", 15, bold=False)
    
    threading.Thread(target=status_polling_worker, daemon=True).start()
    threading.Thread(target=system_widgets_worker, daemon=True).start()

    current_frame_index = 0
    total_frames = len(frames_cache)
    pygame.mouse.set_visible(True)

    # Clickable Mic Interceptor Box dimensions configuration
    card_x = 25
    card_w = panel_width - (card_x * 2)
    card4_y = 615
    card4_h = 95
    mic_btn_rect = pygame.Rect(card_x + 20, card4_y + 45, card_w - 40, 38)

    running = True
    while running:
        dt = clock.tick(30)
        cursor_time_accumulator += dt
        if cursor_time_accumulator >= 500:
            cursor_visible = not cursor_visible
            cursor_time_accumulator = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                box_rect = pygame.Rect(input_box_x, input_box_y, input_box_w, input_box_h)
                
                if box_rect.collidepoint(mouse_pos):
                    is_input_box_active = True
                else:
                    is_input_box_active = False
                
                if mic_btn_rect.collidepoint(mouse_pos):
                    mic_active = not mic_active
                    update_mic_file_state(mic_active)
                    
                    # 🔥 Force instant local update bypassing thread lag
                    current_status = "Listening..." if mic_active else "Muted..."
                    print(f"🎙️ [GUI OVERDRIVE] Toggle Mic Intercept Triggered. State is active: {mic_active}")
                    
            elif event.type == pygame.KEYDOWN:
                if not is_input_box_active:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_q: 
                        running = False
                else:
                    if event.key == pygame.K_ESCAPE:
                        is_input_box_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        user_input_string = user_input_string[:-1]
                    elif event.key == pygame.K_RETURN:
                        if user_input_string.strip():
                            user_said_text = user_input_string
                            user_input_string = ""
                    else:
                        if len(user_input_string) < 65:
                            user_input_string += event.unicode

        # --- DRAW CORE CANVAS ---
        screen.blit(frames_cache[current_frame_index], (0, 0))
        
        sidebar_layer = pygame.Surface((panel_width, screen_height), pygame.SRCALPHA)
        sidebar_layer.fill((12, 14, 18, 100)) 
        screen.blit(sidebar_layer, (0, 0))
        pygame.draw.line(screen, (80, 85, 95, 40), (panel_width, 0), (panel_width, screen_height), 1)
        
        screen.blit(font_title.render("Maya Hub", True, (255, 255, 255)), (35, 45))
        screen.blit(font_body.render("v2.1.0-stable", True, (160, 165, 175)), (160, 54))
        
        # Card 1: Operational Status Mode Box
        card1_y = 120
        c1_surf = pygame.Surface((card_w, 90), pygame.SRCALPHA)
        c1_surf.fill((20, 24, 30, 140))
        screen.blit(c1_surf, (card_x, card1_y))
        pygame.draw.rect(screen, (100, 105, 115, 60), (card_x, card1_y, card_w, 90), width=1, border_radius=10)
        
        status_up = current_status.upper()
        dot_color = (240, 240, 240)
        
        # 🔥 Added specific red dot styling for MUTED state
        if "LISTENING" in status_up: dot_color = (100, 180, 255)
        elif "THINKING" in status_up: dot_color = (190, 140, 255)
        elif "SPEAKING" in status_up: dot_color = (255, 100, 100)
        elif "MUTED" in status_up: dot_color = (231, 76, 60)
        
        pygame.draw.circle(screen, dot_color, (45, card1_y + 26), 5)
        screen.blit(font_section.render("OPERATIONAL STATE", True, (170, 180, 195)), (60, card1_y + 17))
        screen.blit(font_title.render(current_status, True, (255, 255, 255)), (45, card1_y + 42))

        # Card 2: System Utilities Panel
        card2_y = 230
        card2_h = 240
        c2_surf = pygame.Surface((card_w, card2_h), pygame.SRCALPHA)
        c2_surf.fill((20, 24, 30, 140))
        screen.blit(c2_surf, (card_x, card2_y))
        pygame.draw.rect(screen, (100, 105, 115, 60), (card_x, card2_y, card_w, card2_h), width=1, border_radius=10)
        
        screen.blit(font_section.render("LIVE UTILITIES LINK", True, (170, 180, 195)), (45, card2_y + 18))
        screen.blit(font_clock.render(live_time, True, (255, 255, 255)), (45, card2_y + 46))
        screen.blit(font_body.render(live_date, True, (150, 160, 175)), (45, card2_y + 90))
        
        pygame.draw.line(screen, (75, 80, 95, 80), (45, card2_y + 118), (card_x + card_w - 45, card2_y + 118), 1)

        gauge_center_x = card_x + 55
        gauge_center_y = card2_y + 175
        gauge_radius = 28
        pygame.draw.circle(screen, (40, 45, 55), (gauge_center_x, gauge_center_y), gauge_radius, width=4)
        
        percentage_factor = min(max(battery_percent / 100.0, 0.0), 1.0)
        start_angle = math.pi / 2.0
        end_angle = start_angle - (2.0 * math.pi * percentage_factor)
        arc_rect = pygame.Rect(gauge_center_x - gauge_radius, gauge_center_y - gauge_radius, gauge_radius * 2, gauge_radius * 2)
        arc_color = (100, 220, 140) if battery_percent > 20 else (255, 100, 100)
        
        if percentage_factor > 0:
            pygame.draw.arc(screen, arc_color, arc_rect, end_angle, start_angle, width=4)

        bat_num_surf = font_body.render(f"{battery_percent}%", True, (255, 255, 255))
        num_w, num_h = font_body.size(f"{battery_percent}%")
        screen.blit(bat_num_surf, (gauge_center_x - num_w // 2, gauge_center_y - num_h // 2))

        charging_desc = "Charging Core Active" if battery_plugged else "Discharging Battery Source"
        screen.blit(font_body.render(charging_desc, True, (220, 225, 235)), (gauge_center_x + 45, gauge_center_y - 12))
        screen.blit(font_prompt.render("Power Grid Status", True, (130, 140, 155)), (gauge_center_x + 45, gauge_center_y + 6))

        screen.blit(font_body.render("Wireless Network Link:", True, (220, 225, 235)), (45, card2_y + 220))
        wifi_color = (140, 180, 255) if "Connected" in wifi_status else (160, 165, 175)
        screen.blit(font_bold_data.render(wifi_status, True, wifi_color), (195, card2_y + 220))

        # Card 3: Neural Channels
        card3_y = 490
        card3_h = 110
        c3_surf = pygame.Surface((card_w, card3_h), pygame.SRCALPHA)
        c3_surf.fill((20, 24, 30, 140))
        screen.blit(c3_surf, (card_x, card3_y))
        pygame.draw.rect(screen, (100, 105, 115, 60), (card_x, card3_y, card_w, card3_h), width=1, border_radius=10)
        screen.blit(font_section.render("LIVE ENGINE NETWORKS", True, (170, 180, 195)), (45, card3_y + 18))
        screen.blit(font_body.render("✦ Main Thread Pipe: Isolated Performance Core", True, (230, 235, 245)), (45, card3_y + 48))
        screen.blit(font_body.render("✦ Model Core Architecture: Gemini-Flash Pipeline", True, (140, 150, 165)), (45, card3_y + 74))

        # Card 4: Interactive Mic Dashboard Control Matrix
        c4_surf = pygame.Surface((card_w, card4_h), pygame.SRCALPHA)
        c4_surf.fill((20, 24, 30, 140))
        screen.blit(c4_surf, (card_x, card4_y))
        pygame.draw.rect(screen, (100, 105, 115, 60), (card_x, card4_y, card_w, card4_h), width=1, border_radius=10)
        screen.blit(font_section.render("HARDWARE PERIPHERAL RADAR", True, (170, 180, 195)), (45, card4_y + 16))
        
        btn_bg_color = (39, 174, 96, 200) if mic_active else (192, 57, 43, 200)
        btn_border_color = (46, 204, 113) if mic_active else (231, 76, 60)
        
        pygame.draw.rect(screen, btn_bg_color, mic_btn_rect, border_radius=6)
        pygame.draw.rect(screen, btn_border_color, mic_btn_rect, width=1, border_radius=6)
        
        mic_label = "🎙️ BIOMETRIC AUDIO: ON" if mic_active else "🔇 BIOMETRIC AUDIO: MUTED"
        mic_lbl_surf = font_bold_data.render(mic_label, True, (255, 255, 255))
        lbl_w, lbl_h = font_bold_data.size(mic_label)
        screen.blit(mic_lbl_surf, (mic_btn_rect.x + (mic_btn_rect.width - lbl_w) // 2, mic_btn_rect.y + (mic_btn_rect.height - lbl_h) // 2))

        # --- USER PROMPT CONSOLE WINDOW ---
        chat_box_w = 720
        chat_box_h = 90
        chat_box_x = panel_width + (remaining_width - chat_box_w) // 2
        chat_box_y = screen_height - chat_box_h - 260  
        
        user_bubble = pygame.Surface((chat_box_w, chat_box_h), pygame.SRCALPHA)
        user_bubble.fill((14, 16, 20, 200)) 
        screen.blit(user_bubble, (chat_box_x, chat_box_y))
        
        border_color = (100, 150, 220) if "LISTENING" in status_up else (90, 95, 105)
        pygame.draw.rect(screen, border_color, (chat_box_x, chat_box_y, chat_box_w, chat_box_h), width=1, border_radius=8)
        
        screen.blit(font_section.render("USER PROMPT STREAM", True, (150, 160, 180)), (chat_box_x + 25, chat_box_y + 13))
        draw_text_wrapped(screen, user_said_text, font_body, (255, 255, 255), (chat_box_x + 25, chat_box_y + 40, chat_box_w - 50, chat_box_h - 50))

        # --- MAYA OUTPUT RESPONSE STREAM WINDOW ---
        if maya_response_text:
            resp_box_h = 95
            resp_box_y = chat_box_y + chat_box_h + 15  
            
            maya_bubble = pygame.Surface((chat_box_w, resp_box_h), pygame.SRCALPHA)
            maya_bubble.fill((20, 16, 24, 210))  
            screen.blit(maya_bubble, (chat_box_x, resp_box_y))
            
            resp_border_color = (255, 110, 110) if "SPEAKING" in status_up else (80, 85, 100)
            pygame.draw.rect(screen, resp_border_color, (chat_box_x, resp_box_y, chat_box_w, resp_box_h), width=1, border_radius=8)
            
            screen.blit(font_section.render("MAYA CORE RESPONSE STREAM", True, (230, 160, 160)), (chat_box_x + 25, resp_box_y + 13))
            draw_text_wrapped(screen, maya_response_text, font_body, (235, 240, 250), (chat_box_x + 25, resp_box_y + 40, chat_box_w - 50, resp_box_h - 50))

        # --- KEYBOARD TEXT INPUT CAPSULE BAR ---
        input_surf = pygame.Surface((input_box_w, input_box_h), pygame.SRCALPHA)
        if is_input_box_active:
            input_surf.fill((30, 35, 45, 245))
            border_render_color = (240, 240, 240)
        else:
            input_surf.fill((22, 25, 30, 220))
            border_render_color = (85, 90, 105)
            
        screen.blit(input_surf, (input_box_x, input_box_y))
        pygame.draw.rect(screen, border_render_color, (input_box_x, input_box_y, input_box_w, input_box_h), width=1, border_radius=28)
        
        if user_input_string == "" and not is_input_box_active:
            screen.blit(font_prompt.render("Click here to type query manually & hit Enter...", True, (110, 115, 125)), (input_box_x + 30, input_box_y + 18))
        else:
            typed_surf = font_prompt.render(user_input_string, True, (255, 255, 255))
            screen.blit(typed_surf, (input_box_x + 30, input_box_y + 18))
            
            if is_input_box_active and cursor_visible:
                cursor_x_offset = input_box_x + 30 + font_prompt.size(user_input_string)[0]
                pygame.draw.line(screen, (255, 255, 255), (cursor_x_offset, input_box_y + 18), (cursor_x_offset, input_box_y + 36), 2)
        
        pygame.draw.circle(screen, dot_color, (input_box_x + input_box_w - 30, input_box_y + 28), 5)

        current_frame_index = (current_frame_index + 1) % total_frames
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    Start_Maya_GUI()