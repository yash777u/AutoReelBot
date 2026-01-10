import os
import time
import random
import json
import shutil
from dotenv import load_dotenv

# --- 🛠️ FIX FOR PILLOW 10+ CRASH (MUST BE AT TOP) ---
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
# ----------------------------------------------------

# Google AI
from google import genai
from google.genai import types
 

# Instagram Login
from login import login_user

# Advanced Video Editor
from video_editor import create_viral_reel_advanced, generate_thumbnail 

# --- CONFIGURATION ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Folders
OUTPUT_DIR = "output"
IMAGES_DIR = "images"

def clean_output():
    """Wipes the output folder to prevent old files from mixing in."""
    if os.path.exists(OUTPUT_DIR):
        try:
            shutil.rmtree(OUTPUT_DIR)
        except PermissionError:
            print("⚠️ Could not delete output folder (file in use). Skipping cleanup.")
            return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    print("🧹 Workspace cleaned.")

# --- STEP 1: VIRAL CONTENT (GEMINI) ---
# --- STEP 1: VIRAL CONTENT (GEMINI) ---
def get_viral_content():
    print("🧠 Brainstorming viral hook...")
    
    if not GOOGLE_API_KEY:
        raise ValueError("❌ GOOGLE_API_KEY missing in .env file!")

    client = genai.Client(api_key=GOOGLE_API_KEY)
    
    # Make prompt dynamic with random themes/topics for variety
    themes = [
        "conquering fear and taking action",
        "success requires sacrifice",
        "being unstoppable in pursuit of goals",
        "becoming the best version of yourself",
        "discipline over motivation",
        "warrior mindset and mental toughness",
        "breaking free from average thinking",
        "rising after failure",
        "dominating your competition",
        "building an empire from nothing"
    ]
    
    selected_theme = random.choice(themes)
    timestamp = int(time.time())  # Add timestamp for uniqueness
    
    prompt = (
        f"You are a high-testosterone motivational speaker creating UNIQUE viral content. "
        f"Theme for THIS video: {selected_theme}. "
        f"Session: {timestamp}. "
        f"Generate a FRESH 15-second viral script in Hindi (Devanagari). "
        f"Requirements: "
        f"1. THE HOOK (First 2-3 sec): Shocking, controversial, or powerful truth that grabs attention "
        f"2. THE BODY (10-12 sec): Deep stoic/warrior wisdom with actionable insight "
        f"3. Must be COMPLETELY DIFFERENT from previous quotes - no repetition! "
        f"4. OUTPUT STRICT JSON with keys: 'hindi_quote', 'english_translation', 'caption', 'hashtags' "
        f"5. Caption: Short (15-20 words), SEO-optimized, engaging "
        f"6. Hashtags: 12-15 high-traffic Hindi/English tags (mix trending + niche) "
        f"7. NO MARKDOWN. RAW JSON ONLY. "
        f"Make it VIRAL-WORTHY and UNIQUE!"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # Better rate limits than exp
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.9  # High creativity while staying within limits
            )
        )
        
        content = json.loads(response.text)
        
        # Validate response has required fields
        required_fields = ['hindi_quote', 'english_translation', 'caption', 'hashtags']
        if not all(field in content for field in required_fields):
            raise ValueError(f"❌ Gemini response missing required fields! Got: {list(content.keys())}")
        
        print(f"✅ Generated unique content (Theme: {selected_theme})")
        return content
        
    except Exception as e:
        # DON'T use fallback - fail properly so user knows Gemini isn't working
        print(f"❌ GEMINI API FAILED: {e}")
        print("💡 Check your GOOGLE_API_KEY in .env")
        print("💡 Verify API quota at: https://aistudio.google.com/apikey")
        raise RuntimeError(f"Failed to generate content from Gemini: {e}")

# --- STEP 3: ADVANCED VIDEO EDITING ---
def create_viral_reel(audio_path, hindi_text):
    """
    Create viral reel using advanced video editor with:
    - Progressive color grading (B&W → Full Color)
    - Crossfade transitions
    - edgeTTS deep voice (if available)
    - Fast-paced editing (0.5s per clip)
    - Automatic cleanup
    """
    print("🎬 Creating Viral Reel with Advanced Effects...")
    
    # Use the advanced video editor with all the tested features
    output_path = create_viral_reel_advanced(
        hindi_text=hindi_text,
        output_name="viral_reel.mp4",
        use_voice=True  # Generate edgeTTS voice
    )
    
    return output_path

# --- STEP 4: UPLOAD TO INSTAGRAM ---
def upload_reel(video_path, caption):
    print("🚀 Connecting to Instagram...")
    cl = login_user() 
    if not cl:
        print("❌ Login failed. Video saved but not uploaded.")
        return

    # VERIFY we're actually logged in
    try:
        user = cl.account_info()
        print(f"✅ Logged in as: @{user.username}")
    except Exception as e:
        print(f"❌ Not actually logged in! Error: {e}")
        print("💡 Get fresh INSTA_SESSIONID from browser cookies (see FIX_INSTAGRAM_LOGIN.md)")
        return

    # Generate thumbnail
    thumbnail_path = generate_thumbnail(video_path)
    
    print(f"📤 Uploading reel to Instagram...")
    print(f"   Caption: {caption[:60]}...")
    
    try:
        media = cl.clip_upload(
            video_path,
            caption=caption,
            thumbnail=thumbnail_path
        )
        
        # Success
        if media and hasattr(media, 'code'):
            print(f"\n🎉 SUCCESS! REEL POSTED!")
            print(f"📱 Code: {media.code}")
            print(f"🔗 URL: https://www.instagram.com/reel/{media.code}/")
            print(f"👀 Profile: https://www.instagram.com/{user.username}/")
            return media
        else:
            print("⚠️ Upload returned but no media code")
            return None
            
    except Exception as e:
        error_str = str(e)
        
        # Sometimes instagrapi throws pydantic errors even when upload succeeds
        if "pydantic" in error_str.lower() or "validation" in error_str.lower():
            print("\n✅ Upload likely SUCCEEDED (pydantic parsing error)")
            print(f"👀 Check your profile: https://www.instagram.com/{user.username}/")
            return None
        
        # Real errors
        print(f"\n❌ UPLOAD FAILED: {error_str}")
        
        if "login_required" in error_str.lower():
            print("\n💡 FIX: Session expired! Get fresh sessionid from browser")
        elif "challenge" in error_str.lower():
            print("\n💡 FIX: Complete verification in Instagram app")
        elif "spam" in error_str.lower() or "limit" in error_str.lower():
            print("\n💡 FIX: Wait 1-2 hours (posting too fast)")
        
        return None

# --- MAIN LOOP ---
if __name__ == "__main__":
    try:
        clean_output()
        
        # 1. Content Generation
        data = get_viral_content()
        print(f"📜 Hook: {data['hindi_quote'][:40]}...")
        
        # 2. Video Creation (with integrated voice generation)
        # The advanced video editor handles both voice and video creation
        video_file = create_viral_reel(None, data['hindi_quote'])
        
        # 3. Upload
        caption = f"{data['caption']}\n\n{data['hashtags']}"
        upload_reel(video_file, caption)
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")