import subprocess
import tempfile
from pathlib import Path
from yt_dlp import YoutubeDL
from pydub import AudioSegment
import re
import shutil
import os
import uuid


def sanitize_filename(filename):
    # Replace invalid characters with underscores and add random UUID to prevent conflicts
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return f"{sanitized}_{str(uuid.uuid4())[:8]}"


def download_youtube_audio(url):
    # Create temp directory for this session
    temp_dir = Path(tempfile.mkdtemp())
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(temp_dir / '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'noplaylist': True
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        sanitized_title = sanitize_filename(info['title'])
        downloaded_path = Path(ydl.prepare_filename(info)).with_suffix('.mp3')
        final_path = temp_dir / f"{sanitized_title}.mp3"
        downloaded_path.rename(final_path)
        return final_path


def separate_audio(file_path, stems_to_separate=None):
    if stems_to_separate is None:
        stems_to_separate = {
            "Vocals": True,
            "Drums": True,
            "Bass": True,
            "Other": True,
        }

    # Create persistent temp directory with unique name
    temp_dir = Path(tempfile.mkdtemp())
    song_name = file_path.stem
    output_dir = temp_dir / song_name
    output_dir.mkdir(exist_ok=True, parents=True)

    result = subprocess.run(
        ["demucs", "-o", str(output_dir), str(file_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        shutil.rmtree(temp_dir)  # Clean up on error
        raise Exception(f"Error in demucs: {result.stderr}")

    stems_folder = output_dir / "htdemucs" / song_name

    stems = {
        "Vocals": stems_folder / "vocals.wav",
        "Drums": stems_folder / "drums.wav",
        "Bass": stems_folder / "bass.wav",
        "Other": stems_folder / "other.wav",
    }

    session_stems = {}
    for label, path in stems.items():
        if stems_to_separate.get(label, False):
            try:
                mp3_path = convert_to_mp3(path)
                session_stems[label] = mp3_path
            except Exception as e:
                print(f"Error converting {label} to mp3: {e}")
                continue

    return session_stems


def convert_to_mp3(wav_path):
    # Create unique output filename
    mp3_path = wav_path.with_name(f"{wav_path.stem}_{str(uuid.uuid4())[:8]}.mp3")
    
    # First try reading as wav
    try:
        audio = AudioSegment.from_wav(wav_path)
    except:
        # If wav fails, try reading as raw audio
        try:
            audio = AudioSegment.from_file(wav_path, format="raw", 
                                        frame_rate=44100, channels=2, 
                                        sample_width=2)
        except Exception as e:
            raise Exception(f"Failed to read audio file: {e}")
    
    try:
        audio.export(mp3_path, format="mp3", bitrate="192k")
        return mp3_path
    except Exception as e:
        raise Exception(f"Failed to export to mp3: {e}")
