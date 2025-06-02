import streamlit as st
from processor import separate_audio, download_youtube_audio, convert_to_mp3
from pathlib import Path
import tempfile

# Custom color theme - Spotify inspired
st.set_page_config(
    page_title="🎧 Instrumentalizer", 
    layout="centered",
    page_icon="🎧",
    initial_sidebar_state="expanded"
)

st.title("🎸 Instrumentalizer", anchor=False)
st.subheader("Separate vocals and instruments from any song")
st.caption("🚀 Powered by Demucs + YouTube Downloader")

st.subheader("🎧 Select stems to separate:")
stems_to_separate = {
    "Vocals": st.checkbox("Vocals", value=True),
    "Drums": st.checkbox("Drums", value=True),
    "Bass": st.checkbox("Bass", value=True),
    "Other": st.checkbox("Other", value=True),
}

st.subheader("Choose how to upload your song:")
option = st.radio(
    "Select:",
    ["File Upload", "YouTube Link"],
    horizontal=True
)

file_path = None
process_button = None

if option == "File Upload":
    uploaded_file = st.file_uploader("Choose your audio file", type=["mp3", "wav"])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.read())
            file_path = Path(tmp_file.name)
        process_button = st.button("Process Audio")

elif option == "YouTube Link":
    youtube_url = st.text_input("Paste YouTube link here:")
    if youtube_url:
        process_button = st.button("Download and Process")

if process_button:
    if option == "YouTube Link" and youtube_url:
        with st.spinner("🔻 Downloading audio from YouTube..."):
            try:
                file_path = download_youtube_audio(youtube_url)
                st.success("✅ Download complete!")
            except Exception as e:
                st.error(f"❌ Download error: {e}")
                file_path = None

    if file_path:
        with st.spinner("🔍 Separating instruments..."):
            try:
                stems = separate_audio(file_path, stems_to_separate)
                st.success("✅ Separation complete!")

                st.subheader("🎧 Listen to separated instruments:")
                for label, path in stems.items():
                    if stems_to_separate.get(label, False):  # Only show selected stems
                        st.markdown(f"**{label}**")

                        mp3_path = convert_to_mp3(path)

                        st.audio(str(mp3_path))

                        with open(mp3_path, "rb") as file:
                            st.download_button(
                                label=f"📥 Download {label}",
                                data=file,
                                file_name=mp3_path.name,
                                mime="audio/mpeg"
                            )

            except Exception as e:
                st.error(f"❌ Processing error: {e}")
