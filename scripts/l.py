# import os
# import requests
# import json
# import re
# import random

# from moviepy.editor import *
# from PIL import Image, ImageDraw, ImageFont

# # -------------------------------
# # PIL FIX (REMOVE OLD ISSUE)
# # -------------------------------
# from PIL import Image as PILImage
# if not hasattr(PILImage, "Resampling"):
#     PILImage.Resampling = PILImage.LANCZOS

# from config.config import config
# from groq import Groq
# from gtts import gTTS

# client = Groq(api_key=config["GROQ_API_KEY"])

# # -------------------------------
# # JSON EXTRACTOR
# # -------------------------------
# def extract_json(text):
#     try:
#         text = re.sub(r"```json|```", "", text).strip()

#         start = text.find("[")
#         end = text.rfind("]")

#         if start == -1 or end == -1:
#             return []

#         return json.loads(text[start:end+1])

#     except Exception as e:
#         print("❌ JSON ERROR:", e)
#         return []

# # -------------------------------
# # GENERATE SCENES
# # -------------------------------
# def generate_scenes(query):
#     for _ in range(3):
#         try:
#             response = client.chat.completions.create(
#                 model="llama-3.1-8b-instant",
#                 messages=[{
#                     "role": "user",
#                     "content": f"""
# Return ONLY valid JSON array:

# [
#   {{
#     "text": "short narration",
#     "image_prompt": "cinematic scene"
#   }}
# ]

# Topic: {query}
# """
#                 }]
#             )

#             scenes = extract_json(response.choices[0].message.content)
#             if scenes:
#                 return scenes

#         except Exception as e:
#             print("Retry error:", e)

#     return []

# # -------------------------------
# # TITLE
# # -------------------------------
# def generate_seo_title(query):
#     response = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=[{
#             "role": "user",
#             "content": f"Generate ONE short viral YouTube title only: {query}"
#         }]
#     )

#     return response.choices[0].message.content.strip().split("\n")[0]

# # -------------------------------
# # DESCRIPTION
# # -------------------------------
# def generate_description(query):
#     return client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=[{
#             "role": "user",
#             "content": f"Write SEO YouTube description: {query}"
#         }]
#     ).choices[0].message.content.strip()

# # -------------------------------
# # AUDIO
# # -------------------------------
# def generate_audio(text, index):
#     path = f"audio_{index}.mp3"
#     gTTS(text=text, lang="hi").save(path)
#     return path

# # -------------------------------
# # PEXELS VIDEO
# # -------------------------------
# def generate_pexels_video(query):
#     try:
#         res = requests.get(
#             "https://api.pexels.com/videos/search",
#             headers={"Authorization": config["PEXELS_API_KEY"]},
#             params={"query": query, "per_page": 1},
#             timeout=10
#         )

#         data = res.json()

#         if "videos" not in data or not data["videos"]:
#             return None

#         video_files = data["videos"][0].get("video_files", [])

#         video_url = None
#         for v in sorted(video_files, key=lambda x: x.get("width", 0), reverse=True):
#             if v.get("file_type") == "video/mp4":
#                 video_url = v["link"]
#                 break

#         if not video_url:
#             return None

#         path = f"pexels_{random.randint(1,999)}.mp4"

#         with open(path, "wb") as f:
#             f.write(requests.get(video_url).content)

#         if os.path.getsize(path) < 50000:
#             return None

#         return path

#     except Exception as e:
#         print("❌ Pexels error:", e)
#         return None

# # -------------------------------
# # IMAGE FALLBACK
# # -------------------------------
# def generate_image(query):
#     try:
#         res = requests.get(
#             "https://api.pexels.com/v1/search",
#             headers={"Authorization": config["PEXELS_API_KEY"]},
#             params={"query": query, "per_page": 1}
#         )

#         img_url = res.json()["photos"][0]["src"]["large"]
#         path = f"img_{random.randint(1,999)}.jpg"

#         with open(path, "wb") as f:
#             f.write(requests.get(img_url).content)

#         return path

#     except:
#         return None

# # -------------------------------
# # CREATE CLIP (FINAL FIXED)
# # -------------------------------
# def create_clip(video_path, img_path, duration):
#     try:
#         W, H = 1080, 1920

#         # -------------------------------
#         # LOAD MEDIA
#         # -------------------------------
#         if video_path and os.path.exists(video_path):
#             clip = VideoFileClip(video_path)
#             clip = clip.subclip(0, min(duration, clip.duration))
#         elif img_path and os.path.exists(img_path):
#             clip = ImageClip(img_path).set_duration(duration)
#         else:
#             return ColorClip((W, H), color=(0, 0, 0)).set_duration(duration)

#         # -------------------------------
#         # FORCE SIZE (NO CROPPING BUG)
#         # -------------------------------
#         clip = clip.resize(height=H)

#         if clip.w < W:
#             clip = clip.resize(width=W)

#         clip = clip.set_position(("center", "center"))

#         # -------------------------------
#         # BACKGROUND
#         # -------------------------------
#         bg = ColorClip((W, H), color=(0, 0, 0)).set_duration(duration)

#         final = CompositeVideoClip([bg, clip], size=(W, H)).set_duration(duration)

#         # -------------------------------
#         # SAFE ZOOM
#         # -------------------------------
#         final = final.resize(lambda t: 1 + 0.01 * t)

#         return final

#     except Exception as e:
#         print("❌ Clip error:", e)
#         return ColorClip((1080, 1920), color=(0, 0, 0)).set_duration(duration)

# # -------------------------------
# # SUBTITLE
# # -------------------------------
# def create_subtitle_clip(text, duration):
#     img = Image.new("RGBA", (1000, 200), (0, 0, 0, 150))
#     draw = ImageDraw.Draw(img)

#     try:
#         font = ImageFont.truetype("arial.ttf", 45)
#     except:
#         font = ImageFont.load_default()

#     bbox = draw.textbbox((0, 0), text, font=font)
#     w = bbox[2] - bbox[0]
#     h = bbox[3] - bbox[1]

#     draw.text(((1000 - w) / 2, (200 - h) / 2), text, fill="white", font=font)

#     path = f"subtitle_{random.randint(1,999)}.png"
#     img.save(path)

#     txt_clip = ImageClip(path).set_duration(duration)
#     txt_clip = txt_clip.set_position(("center", "bottom"))

#     return txt_clip

# # -------------------------------
# # MAIN FUNCTION
# # -------------------------------
# def generate_video_from_query(query):

#     title = generate_seo_title(query)
#     description = generate_description(query)

#     scenes = generate_scenes(query)

#     if not scenes:
#         scenes = [{"text": query, "image_prompt": query}]

#     clips = []
#     audio_clips = []

#     for i, scene in enumerate(scenes):

#         text = scene.get("text", query)
#         prompt = scene.get("image_prompt", query)

#         audio_path = generate_audio(text, i)
#         audio = AudioFileClip(audio_path)

#         duration = audio.duration

#         video_path = generate_pexels_video(prompt)
#         img_path = None

#         if not video_path:
#             img_path = generate_image(prompt)

#         clip = create_clip(video_path, img_path, duration)
#         subtitle = create_subtitle_clip(text, duration)

#         final_clip = CompositeVideoClip([clip, subtitle]).set_audio(audio)

#         clips.append(final_clip)
#         audio_clips.append(audio)

#     if not clips:
#         raise Exception("❌ No clips generated")

#     final = concatenate_videoclips(clips, method="compose")

#     final_audio = concatenate_audioclips(audio_clips)
#     final = final.set_audio(final_audio)

#     output = "final_video.mp4"

#     final.write_videofile(
#         output,
#         fps=30,
#         codec="libx264",
#         audio_codec="aac",
#         threads=4,
#         preset="ultrafast"
#     )

#     return output, title, description  