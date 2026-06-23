import os
import asyncio
import requests
import random
import json  # Explicit JSON module decode karne ke liye
import warnings
import urllib3
from PIL import Image
from time import sleep

warnings.filterwarnings("ignore", category=UserWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://api.siliconflow.com/v1/images/generations"

# Apni API Key ensure kar lena sahi ho
headers = {
    "Authorization": "Bearer sk-kasapowljunqpbejhkwjrvtfvtzxxhuhlhszokptxpyvuwxy",
    "Content-Type": "application/json"
}

async def query(payload):
    # response.text return karenge taaki manually safe decode ho sake
    response = await asyncio.to_thread(
        lambda: requests.post(API_URL, headers=headers, json=payload, verify=False, timeout=30)
    )
    return response.text

async def generate_images(prompt: str):
    file_prefix = prompt.lower().strip().replace(" ", "_")
    base_prompt = prompt.lower().strip()
    
    print(f"\n⚡ Cypher AI: Generating 3 unique images using SiliconFlow...")
    print(f"🎯 Prompt: '{prompt}'")
    
    if not os.path.exists("Data"):
        os.makedirs("Data")

    for i in range(3):
        seed = random.randint(1, 999999)
        
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": f"{base_prompt}, cinematic lighting, photorealistic, hyper-detailed, variant {i+1}",
            "image_size": "1024x1024",
            "batch_size": 1,
            "seed": seed
        }
        
        try:
            print(f"📸 Requesting Image {i+1}/3 from SiliconFlow...")
            raw_response = await query(payload)
            
            # Text response ko securely dictionary me load karenge
            res_data = json.loads(raw_response)
            
            # SiliconFlow Response parsing block
            if "images" in res_data and len(res_data["images"]) > 0:
                img_url = res_data["images"][0]["url"]
                
                # Image download directly from CDN URL
                img_response = await asyncio.to_thread(lambda: requests.get(img_url, verify=False))
                img_bytes = img_response.content
                
                if len(img_bytes) > 15000:
                    file_name = fr"Data\{file_prefix}{i + 1}.jpg"
                    with open(file_name, "wb") as f:
                        f.write(img_bytes)
                    print(f"✅ Image {i+1} saved successfully!")
                else:
                    print(f"⚠️ Image {i+1} saved bytes size too low.")
            else:
                error_msg = res_data.get('message', 'Unknown API Response Error')
                print(f"⚠️ SiliconFlow API Error on Image {i+1}: {error_msg}")
                
            await asyncio.sleep(1)
                
        except Exception as e:
            print(f"❌ Image {i+1} failure: {e}")
            await asyncio.sleep(1)
            continue

def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
   