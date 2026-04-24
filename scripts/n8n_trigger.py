import os
import requests
from config.config import config

def trigger_n8n_upload(video_file: str, title: str, description: str, youtube_channel_id: str):
    
    url = config.get("N8N_WEBHOOK_URL")

    # -------------------------------
    # VALIDATION ✅
    # -------------------------------
    if not url:
        return {"error": "❌ N8N_WEBHOOK_URL is missing in config"}

    if not video_file or not isinstance(video_file, str):
        return {"error": "❌ video_file must be a valid file path string"}

    if not os.path.exists(video_file):
        return {"error": f"❌ File not found: {video_file}"}

    try:
        print(f"🚀 Uploading to n8n: {video_file}")

        with open(video_file, "rb") as f:

            files = {
                "data": ("video.mp4", f, "video/mp4")  # MUST be 'data'
            }

            payload = {
                "title": title or "",
                "description": description or "",
                "youtube_channel_id": youtube_channel_id or ""
            }
            headers = {
                "Accept": "application/json"
          }
            response = requests.post(
                url,
                files=files,
                data=payload,
                timeout=60
            )

        # -------------------------------
        # RESPONSE DEBUG ✅
        # -------------------------------
        print("📡 N8N STATUS:", response.status_code)

        if response.status_code != 200:
            print("❌ N8N RESPONSE ERROR:", response.text)

        # Try JSON response
        try:
            return response.json()
        except:
            return {
                "status_code": response.status_code,
                "response": response.text
            }

    # -------------------------------
    # ERROR HANDLING ✅
    # -------------------------------
    except requests.exceptions.ConnectionError:
        return {"error": "❌ Cannot connect to n8n webhook"}

    except requests.exceptions.Timeout:
        return {"error": "❌ Request timed out"}

    except requests.exceptions.HTTPError as e:
        return {"error": f"❌ HTTP error: {str(e)}"}

    except Exception as e:
        return {"error": f"❌ Unexpected error: {str(e)}"}