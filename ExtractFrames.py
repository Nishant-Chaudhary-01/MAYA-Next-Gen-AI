# File Path: ExtractFrames.py
import cv2
import os

# Pure computer me jahan bhi file hai, uske hisab se automated safe directory paths
base_dir = os.path.dirname(os.path.abspath(__file__))
video_path = os.path.join(base_dir, "Frontend", "Graphics", "maya_wallpaper.mp4")
output_folder = os.path.join(base_dir, "Data", "MayaFrames")

if not os.path.exists(video_path):
    print(f"❌ ERROR: Mujhe file nahi mili is path par: {video_path}")
    print("💡 Ek baar check karo ki 'Frontend' ke andar jo 'Graphics' folder hai, video uske andar hi hai na?")
else:
    print("✅ Video mil gayi! Frames extraction shuru ho raha hai...")
    os.makedirs(output_folder, exist_ok=True)
    
    cam = cv2.VideoCapture(video_path)
    currentframe = 0
    
    while True:
        ret, frame = cam.read()
        if ret:
            name = os.path.join(output_folder, f"frame_{currentframe:04d}.jpg")
            cv2.imwrite(name, frame)
            currentframe += 1
        else:
            break
            
    cam.release()
    print(f"🔥 Sahi hai bhai! Total {currentframe} frames cleanly save ho gaye hain Data\\MayaFrames folder me!")