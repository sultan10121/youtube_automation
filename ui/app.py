import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from scripts.video_generator import generate_video_from_query
from scripts.n8n_trigger import trigger_n8n_upload

# ---------------- UI ----------------
st.set_page_config(page_title="YouTube Automation Agent", layout="centered")
st.title("🎬 YouTube Automation Agent")

# ---------------- INPUTS ----------------
query = st.text_input("Enter your video topic/query")
youtube_channel_id = st.text_input("Enter YouTube Channel ID")

# Scene control
num_scenes = st.slider("Number of scenes", min_value=2, max_value=10, value=3)

st.markdown("### (Optional) Override AI Title & Description")
video_title = st.text_input("Video Title (optional)")
video_description = st.text_area("Video Description (optional)")

# ---------------- ACTION ----------------
if st.button("🚀 Generate & Upload Video"):

    if not query or not youtube_channel_id:
        st.error("⚠️ Please fill Query and Channel ID")
        st.stop()

    try:
        # -------- VIDEO GENERATION --------
        with st.spinner("🎥 Generating video..."):
            result = generate_video_from_query(query, num_scenes)

        # -----------------------------------
        # 🔥 FIX: HANDLE 1 / 2 / 3 RETURN VALUES
        # -----------------------------------
        video_file = None
        auto_title = query
        auto_description = query

        if isinstance(result, tuple):

            if len(result) == 3:
                video_file, auto_title, auto_description = result

            elif len(result) == 2:
                video_file, auto_title = result

            elif len(result) == 1:
                video_file = result[0]

            else:
                video_file = result[0]

        else:
            video_file = result

        # -------- DEBUG --------
        print("DEBUG RESULT:", result)
        print("DEBUG VIDEO FILE:", video_file)
        print("DEBUG TYPE:", type(video_file))

        if not video_file or not isinstance(video_file, str):
            st.error("❌ Invalid video file generated.")
            st.stop()

        st.success(f"✅ Video generated: {video_file}")

        # -------- FINAL TITLE / DESCRIPTION --------
        final_title = video_title.strip() if video_title.strip() else auto_title
        final_description = (
            video_description.strip()
            if video_description.strip()
            else auto_description
        )

        # -------- UPLOAD --------
        with st.spinner("📤 Uploading to YouTube via n8n..."):
            response = trigger_n8n_upload(
                video_file,
                final_title,
                final_description,
                youtube_channel_id
            )

        st.success("🚀 Upload triggered successfully!")

        # -------- DISPLAY --------
        st.markdown("### 📌 Final Upload Data")
        st.write("**Title:**", final_title)
        st.write("**Description:**", final_description)

        st.json(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        st.error(f"❌ Error: {str(e)}")