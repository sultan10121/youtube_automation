import os
from dotenv import load_dotenv
import requests
import json
import re
import random
import textwrap
from elevenlabs.client import ElevenLabs
from config.config import config
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout

from groq import Groq
from gtts import gTTS

groq_client = Groq(api_key=config["GROQ_API_KEY"])
elevenlabs_client = ElevenLabs(
    api_key=config.get("ELEVENLABS_API_KEY")
)

load_dotenv()

# -------------------------------
# MODE SELECTOR 🔥
# -------------------------------
VIDEO_MODE = "youtube"

if VIDEO_MODE == "shorts":
    WIDTH, HEIGHT = 1080, 1920
else:
    WIDTH, HEIGHT = 1920, 1080

# --- PILLOW FIX ---
from PIL import Image, ImageDraw, ImageFont
if not hasattr(Image, "Resampling"):
    Image.Resampling = Image.LANCZOS
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

BASE_DIR = os.getcwd()
TEMP_DIR = os.path.join(BASE_DIR, "assets", "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

temp_files = []

# -------------------------------
# CLEANUP
# -------------------------------
def cleanup():
    for f in temp_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

# -------------------------------
# CLEAN TEXT
# -------------------------------
def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'["“”]', '', text)
    text = re.sub(r'\n+', ' ', text)
    return text

# -------------------------------
# JSON EXTRACTOR (FIXED FOR GROQ META)
# -------------------------------
def extract_json(text):
    try:
        text = re.sub(r"```json|```", "", text).strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            match = re.search(r"\[.*\]", text, re.DOTALL)

        if not match:
            return []

        data = json.loads(match.group())

        return data if isinstance(data, (dict, list)) else []

    except Exception as e:
        print("❌ JSON Error:", e)
        return []

# -------------------------------
# VIRAL STORY PROMPT 🔥
# -------------------------------
def build_prompt(query, num_scenes):
    return f"""
You are a VIRAL STORYTELLING EXPERT.

Create a HIGH-RETENTION cinematic story.

Return ONLY JSON:
[
  {{
    "text": "short narration",
    "image_prompt": "cinematic visual"
  }}
]

Topic: {query}
Scenes: {num_scenes}
"""

# -------------------------------
# AI SCENES
# -------------------------------
def generate_scenes(query, num_scenes):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": build_prompt(query, num_scenes)}]
        )

        content = response.choices[0].message.content
        scenes = extract_json(content)

        if not scenes or len(scenes) < num_scenes:
            scenes = [{
                "text": query,
                "image_prompt": "cinematic scene"
            }] * num_scenes

        return scenes[:num_scenes]

    except:
        return [{
            "text": query,
            "image_prompt": "cinematic scene"
        }] * num_scenes

# -------------------------------
# META DATA (FIXED + SMART GROQ OUTPUT)
# -------------------------------
def generate_youtube_metadata(topic):
    prompt = f"""
You are a YouTube SEO expert.

Generate:
- title (viral)
- description (SEO optimized)
- tags (comma separated)

Return ONLY JSON:
{{
  "title": "...",
  "description": "...",
  "tags": "tag1, tag2, tag3"
}}

Topic: {topic}
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.choices[0].message.content
        data = extract_json(content)

        if isinstance(data, dict):
            return data
        elif isinstance(data, list) and len(data) > 0:
            return data[0]

    except:
        pass

    return {
        "title": topic,
        "description": topic,
        "tags": topic
    }

# -------------------------------
# THUMBNAIL
# -------------------------------
def create_thumbnail(topic):
    img = Image.new("RGB", (1280, 720), color=(20, 20, 20))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("Montserrat-Bold.ttf", 90)
    except:
        font = ImageFont.load_default()

    text = topic.upper()
    lines = textwrap.wrap(text, width=20)

    y = 200
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]

        draw.text(((1280 - w) / 2, y), line, fill="yellow", font=font)
        y += 120

    path = os.path.join(TEMP_DIR, f"thumb_{random.randint(100,999)}.png")
    img.save(path)

    return path

# -------------------------------
# AUDIO (UNCHANGED)
# -------------------------------
def get_audio(text, index):
    path = os.path.join(TEMP_DIR, f"audio_{index}.mp3")

    voice_id = config.get("ELEVENLABS_VOICE_ID")

    try:
        if not voice_id:
            raise ValueError("Missing voice id")

        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_monolingual_v1",
            text=text[:250]
        )

        with open(path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        temp_files.append(path)
        return path

    except:
        try:
            tts = gTTS(text=text[:200], lang="en")
            tts.save(path)
            temp_files.append(path)
            return path
        except:
            return None

# -------------------------------
# PEXELS VIDEO
# -------------------------------
def get_pexels_video(query):
    try:
        res = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": config["PEXELS_API_KEY"]},
            params={"query": query, "per_page": 1},
            timeout=10
        )

        data = res.json()

        if "videos" not in data or not data["videos"]:
            return None

        video_files = data["videos"][0].get("video_files", [])

        video_url = None
        for v in sorted(video_files, key=lambda x: x.get("width", 0), reverse=True):
            if v.get("file_type") == "video/mp4":
                video_url = v["link"]
                break

        if not video_url:
            return None

        path = os.path.join(TEMP_DIR, f"pexels_{random.randint(1,999)}.mp4")

        with open(path, "wb") as f:
            f.write(requests.get(video_url).content)

        if os.path.getsize(path) < 50000:
            return None

        temp_files.append(path)
        return path

    except Exception as e:
        print("❌ Pexels error:", e)
        return None

# -------------------------------
# CREATE CLIP
# -------------------------------
def create_clip(video_path, duration):
    try:
        if video_path and os.path.exists(video_path):
            try:
                # 🔥 Safe video load (ignore broken audio streams)
                clip = VideoFileClip(video_path, audio=False)

            except Exception as e:
                print("⚠️ Broken video file:", e)
                return ColorClip((WIDTH, HEIGHT), color=(0, 0, 0)).set_duration(duration)

            # Safe duration check
            if not clip.duration or clip.duration <= 0:
                duration = 5
            elif clip.duration < duration:
                duration = clip.duration

            clip = clip.subclip(0, duration)

        else:
            clip = ColorClip((WIDTH, HEIGHT), color=(0, 0, 0)).set_duration(duration)

        # 🔥 Force exact size
        clip = clip.resize((WIDTH, HEIGHT))

        return clip.set_duration(duration)

    except Exception as e:
        print("❌ Clip error:", e)
        return ColorClip((WIDTH, HEIGHT), color=(0, 0, 0)).set_duration(duration)
# -------------------------------
# SUBTITLE
# -------------------------------
def create_subtitle_clip(text, duration):
    # Full frame transparent image (prevents size mismatch issues)
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 45)
    except:
        font = ImageFont.load_default()

    # 🔥 Wrap text to avoid overflow
    wrapped_text = textwrap.fill(text, width=40)

    # Get text size
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # 🔥 Subtitle position (bottom center with padding)
    x = (WIDTH - w) / 2
    y = HEIGHT - h - 80

    # 🔥 Optional background box for readability
    padding = 20
    draw.rectangle(
        [
            (x - padding, y - padding),
            (x + w + padding, y + h + padding)
        ],
        fill=(0, 0, 0, 150)
    )

    # Draw text
    draw.text((x, y), wrapped_text, fill="white", font=font)

    # Save
    path = os.path.join(TEMP_DIR, f"subtitle_{random.randint(1,999)}.png")
    img.save(path)
    temp_files.append(path)

    # Create clip
    txt_clip = ImageClip(path).set_duration(duration)

    return txt_clip

# -------------------------------
# MAIN ENGINE 🔥 (ONLY META FIXED)
# -------------------------------
def generate_video_from_query(query, num_scenes):
    scenes = generate_scenes(query, num_scenes)

    meta = generate_youtube_metadata(query)

    print("\n🔥 YOUTUBE META:")
    print("TITLE:", meta.get("title"))
    print("DESCRIPTION:", meta.get("description"))
    print("TAGS:", meta.get("tags"))

    thumb_path = create_thumbnail(query)
    print("🖼 Thumbnail saved at:", thumb_path)

    clips = []

    for i, scene in enumerate(scenes):
        txt = clean_text(scene.get("text", query))
        prmpt = scene.get("image_prompt", "cinematic scene")

        audio_path = get_audio(txt, i)

        audio = None
        duration = 5

        if audio_path and os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            duration = audio.duration if audio.duration else 5

        vid_path = get_pexels_video(prmpt)

        # ---------------------------
# SAFE DURATION FIX
# ---------------------------
        if not duration or duration <= 0:
            duration = 5

        main_clip = create_clip(vid_path, duration)
        sub_clip = create_subtitle_clip(txt, duration)

        final = CompositeVideoClip([main_clip, sub_clip])
        # 🔥 SAFE AUDIO ATTACH
        try:
            if audio:
                final = final.set_audio(audio)
        except Exception as e:
            print("⚠️ Audio attach error:", e)

        # 🔥 SAFE FADE EFFECTS
        try:
            final = fadein(final, 0.5).fx(fadeout, 0.5)
        except Exception as e:
            print("⚠️ Fade error:", e)

        # 🔥 ENSURE CONSISTENT SIZE & DURATION
        final = final.set_duration(duration).resize((WIDTH, HEIGHT))

        clips.append(final)

    # -------------------------------
    # 🔥 SAFE CONCATENATION (CRITICAL FIX)
    # -------------------------------
    try:
        video = concatenate_videoclips(clips, method="compose")
    except Exception as e:
        print("❌ Concatenate error:", e)
        video = clips[0] if clips else None

    # -------------------------------
    # 🔥 EXPORT
    # -------------------------------
    output = f"final_{VIDEO_MODE}.mp4"

    if video:
        video.write_videofile(output, fps=30)
    else:
        print("❌ No video generated")
        return None

    cleanup()

    return output

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    topic = input("Video Topic: ")
    scenes = int(input("Scenes: "))

    try:
        file = generate_video_from_query(topic, scenes)
        print("✅ DONE:", file)
    except Exception as e:
        import traceback
        traceback.print_exc()