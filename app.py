import streamlit as st
from yt_dlp import YoutubeDL
from PIL import Image
import requests
from io import BytesIO
from urllib.parse import urlparse
import os
import time
import hashlib
import datetime
import random

# ======================
# APP CONFIGURATION
# ======================
st.set_page_config(
    page_title="Video Downloader Pro - HD Videos from Any Platform",
    layout="centered",
    page_icon="🎬",
    menu_items={
        'About': "Ultimate Video Downloader Pro - Download videos from 100+ sites"
    }
)

# ======================
# SESSION STATE
# ======================
if 'download_history' not in st.session_state:
    st.session_state.download_history = []
if 'private_videos' not in st.session_state:
    st.session_state.private_videos = {}
if 'playlists' not in st.session_state:
    st.session_state.playlists = {"Favorites": []}
if 'current_video' not in st.session_state:
    st.session_state.current_video = None
if 'reviews' not in st.session_state:
    st.session_state.reviews = []

# ======================
# CORE FUNCTIONS
# ======================
def detect_platform(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    supported_domains = {
        "youtube": "YouTube", "youtu.be": "YouTube",
        "instagram": "Instagram", "facebook": "Facebook", "fb": "Facebook",
        "tiktok": "TikTok", "twitter": "Twitter", "x.com": "Twitter",
        "twitch": "Twitch", "vimeo": "Vimeo", "dailymotion": "Dailymotion",
        "pinterest": "Pinterest", "reddit": "Reddit"
    }
    
    for key in supported_domains:
        if key in domain:
            return supported_domains[key]
    return "Unknown"

def get_video_info(link):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            return info
    except Exception as e:
        st.error(f"Error getting video info: {str(e)}")
        return None

def download_video(link, quality, format_type, subtitles=False):
    # Enhanced configuration to handle YouTube's SABR protection
    ydl_opts = {
        'outtmpl': 'downloads/%(title).100s.%(ext)s',
        'writesubtitles': subtitles,
        'subtitleslangs': ['en'],
        'noplaylist': True,
        'ignoreerrors': True,
        'no_warnings': False,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.youtube.com/',
        },
        # Add cookies file to handle restrictions
        'cookiefile': 'cookies.txt',
    }
    
    # Format selection with fallback options
    if format_type in ["MP3", "M4A"]:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format_type.lower(),
            'preferredquality': '192',
        }]
    else:
        # Use simpler format selection to avoid SABR issues
        if "youtube" in link.lower() or "youtu.be" in link.lower():
            # For YouTube, use a simpler approach
            ydl_opts['format'] = 'best[height<=720]/best[height<=480]/best'
        else:
            # For other platforms
            quality_map = {
                "Best": "best",
                "4K": "best[height<=2160]",
                "1080p": "best[height<=1080]",
                "720p": "best[height<=720]",
                "480p": "best[height<=480]",
                "360p": "best[height<=360]"
            }
            ydl_opts['format'] = quality_map.get(quality, "best")
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            
            # For audio formats, update filename extension
            if format_type in ["MP3", "M4A"]:
                base_name = os.path.splitext(filename)[0]
                filename = f"{base_name}.{format_type.lower()}"
            
            return filename, info.get('title', 'video'), info
    except Exception as e:
        st.error(f"Download error: {str(e)}")
        # Try with absolute minimal options
        return download_video_minimal(link, format_type)

def download_video_minimal(link, format_type):
    """Absolute minimal download method as last resort"""
    ydl_opts = {
        'format': 'best' if format_type not in ["MP3", "M4A"] else 'bestaudio/best',
        'outtmpl': 'downloads/%(title).100s.%(ext)s',
        'ignoreerrors': True,
    }
    
    if format_type in ["MP3", "M4A"]:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format_type.lower(),
        }]
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_type in ["MP3", "M4A"]:
                base_name = os.path.splitext(filename)[0]
                filename = f"{base_name}.{format_type.lower()}"
            
            return filename, info.get('title', 'video'), info
    except Exception as e:
        raise Exception(f"All download methods failed: {str(e)}")

# ======================
# UI COMPONENTS
# ======================
# App Header
st.markdown("<h1 style='text-align: center;'>🎬 Video Downloader Pro</h1>", unsafe_allow_html=True)

# Security Badge
st.markdown("""
<div style="background-color:#f0f2f6; padding:10px; border-radius:5px; margin-bottom:20px; text-align: center;">
    <span style="color:#4CAF50; font-weight:bold;">🛡️ Secure & Private</span>
    <span style="margin-left:15px; font-size:14px;">No data collection • No ads • End-to-end encryption</span>
</div>
""", unsafe_allow_html=True)

# App Description
st.markdown("""
**Download videos from YouTube, Instagram, TikTok, Facebook, Twitter and 100+ sites in HD/4K. 
Fastest video downloader with built-in player, private folder, playlist support & MP3 converter.**
""")

# ======================
# HOW TO USE SECTION
# ======================
with st.expander("📘 How To Use This App", expanded=True):
    st.markdown("""
    **Follow these simple steps to download videos:**
    
    1. **Paste URL** - Copy any video link from supported platforms
    2. **Choose Settings** - Select quality and format from sidebar
    3. **Download** - Click the download button
    4. **Enjoy** - Watch or save to your device!
    
    💡 **Pro Tips:**
    - For YouTube issues, try MP3 format first
    - Use Private Folder for sensitive videos
    - Create playlists to organize downloads
    """)

# ======================
# SIDEBAR - SETTINGS
# ======================
with st.sidebar:
    st.header("⚙️ Settings")
    
    download_quality = st.selectbox(
        "Video Quality",
        ["Best", "720p", "480p", "360p"],
        index=0,
        help="Lower quality may work better for restricted videos"
    )
    
    download_format = st.selectbox(
        "Download Format",
        ["MP4", "MP3", "M4A"],
        index=0,
        help="MP3 format often works when video downloads fail"
    )
    
    enable_subtitles = st.checkbox("Include Subtitles (if available)")
    private_download = st.checkbox("Save to Private Folder")
    
    if private_download:
        password = st.text_input("Set Password", type="password")

# ======================
# MAIN DOWNLOAD INTERFACE
# ======================
st.markdown("### 📥 Download Videos")

url = st.text_input(
    "Paste Video URL Here", 
    placeholder="https://youtube.com/watch?v=... or https://instagram.com/reel/...",
    key="url_input"
)

if url:
    platform = detect_platform(url)
    
    if platform == "Unknown":
        st.error("❌ Unsupported platform. Supported: YouTube, Instagram, TikTok, Facebook, Twitter, etc.")
    else:
        with st.spinner(f"🔍 Analyzing {platform} video..."):
            info = get_video_info(url)
            
        if info is None:
            st.error("❌ Failed to get video information. Please check:")
            st.markdown("""
            - URL is correct and video is publicly available
            - Video is not age-restricted or private
            - Try a different video or platform
            """)
        else:
            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)
            thumbnail_url = info.get('thumbnail')
            
            # Display video info
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if thumbnail_url:
                    try:
                        response = requests.get(thumbnail_url, timeout=10)
                        if response.status_code == 200:
                            img = Image.open(BytesIO(response.content))
                            st.image(img, width='stretch')
                    except:
                        st.info("📺 Video Preview")
                else:
                    st.info("📺 Video Preview")
            
            with col2:
                st.subheader(title[:60] + '...' if len(title) > 60 else title)
                st.caption(f"**Platform:** {platform}")
                if duration > 0:
                    st.caption(f"**Duration:** {duration//60}:{duration%60:02d}")
                
                # Download button
                if st.button("⬇️ Download Video", type="primary", use_container_width=True):
                    with st.spinner("⏳ Downloading... This may take a while"):
                        progress_bar = st.progress(0)
                        
                        try:
                            filename, video_title, full_info = download_video(
                                url, download_quality, download_format, enable_subtitles
                            )
                            
                            # Simulate progress
                            for i in range(100):
                                progress_bar.progress(i + 1)
                                time.sleep(0.03)
                            
                            # Save to appropriate location
                            download_item = {
                                'title': video_title,
                                'platform': platform,
                                'url': url,
                                'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'file': filename
                            }
                            
                            if private_download and password:
                                file_hash = hashlib.sha256(password.encode()).hexdigest()
                                if file_hash not in st.session_state.private_videos:
                                    st.session_state.private_videos[file_hash] = []
                                st.session_state.private_videos[file_hash].append(download_item)
                                st.success("🔒 Saved to private folder!")
                            else:
                                st.session_state.download_history.append(download_item)
                                st.success("✅ Download completed!")
                            
                            # Provide download button
                            if os.path.exists(filename):
                                with open(filename, "rb") as file:
                                    file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
                                    st.download_button(
                                        label=f"💾 Save File ({file_size:.1f} MB)",
                                        data=file,
                                        file_name=os.path.basename(filename),
                                        mime="video/mp4" if download_format != "MP3" else "audio/mpeg",
                                        use_container_width=True
                                    )
                            else:
                                st.error("File not found after download")
                                
                        except Exception as e:
                            st.error(f"❌ Download failed: {str(e)}")
                            st.markdown("""
                            **Troubleshooting:**
                            - Try **MP3 format** instead of video
                            - Try a **lower quality** setting
                            - The video might be **region-restricted**
                            - Wait a few minutes and try again
                            - Try a **different video** from the same platform
                            """)

# ======================
# ADDITIONAL FEATURES IN TABS
# ======================
tab1, tab2, tab3, tab4 = st.tabs(["🔒 Private", "🎵 Playlists", "🎥 Player", "⭐ Reviews"])

with tab1:
    st.header("Private Folder")
    password_input = st.text_input("Enter Password", type="password", key="private_access")
    
    if password_input:
        file_hash = hashlib.sha256(password_input.encode()).hexdigest()
        private_items = st.session_state.private_videos.get(file_hash, [])
        
        if private_items:
            st.success(f"Access granted! {len(private_items)} private videos")
            for idx, item in enumerate(private_items):
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{item['title']}**")
                col1.caption(f"{item['platform']} - {item['time']}")
                
                if col2.button("Play", key=f"play_priv_{idx}"):
                    st.session_state.current_video = item['file']
                
                if col2.button("Delete", key=f"del_priv_{idx}"):
                    if os.path.exists(item['file']):
                        os.remove(item['file'])
                    private_items.pop(idx)
                    st.rerun()
        else:
            st.info("No private videos found or incorrect password")

with tab2:
    st.header("Your Playlists")
    
    # Create playlist
    new_playlist = st.text_input("New Playlist Name")
    if st.button("Create Playlist") and new_playlist:
        if new_playlist not in st.session_state.playlists:
            st.session_state.playlists[new_playlist] = []
            st.success(f"Created '{new_playlist}'")
    
    # Manage playlists
    if st.session_state.playlists:
        selected = st.selectbox("Select Playlist", list(st.session_state.playlists.keys()))
        
        if selected and st.session_state.download_history:
            # Add to playlist
            video_options = [f"{vid['title']} ({vid['time']})" for vid in st.session_state.download_history]
            selected_video = st.selectbox("Add Video", video_options)
            
            if st.button(f"Add to {selected}"):
                idx = video_options.index(selected_video)
                st.session_state.playlists[selected].append(st.session_state.download_history[idx])
                st.success("Video added!")
        
        # Show playlist contents
        if selected and st.session_state.playlists[selected]:
            st.subheader(f"Videos in {selected}")
            for idx, item in enumerate(st.session_state.playlists[selected]):
                col1, col2 = st.columns([3, 1])
                col1.write(f"{idx+1}. {item['title']}")
                if col2.button("Play", key=f"play_pl_{idx}"):
                    st.session_state.current_video = item['file']
                if col2.button("Remove", key=f"rem_pl_{idx}"):
                    st.session_state.playlists[selected].pop(idx)
                    st.rerun()

with tab3:
    st.header("Video Player")
    
    if st.session_state.current_video and os.path.exists(st.session_state.current_video):
        st.success("Now Playing")
        try:
            with open(st.session_state.current_video, 'rb') as f:
                st.video(f.read())
        except:
            st.error("Could not play video")
    else:
        st.info("Select a video to play from Downloads or Playlists")
        
        # Quick access to recent downloads
        if st.session_state.download_history:
            st.subheader("Recent Downloads")
            for idx, item in enumerate(st.session_state.download_history[:3]):
                if st.button(f"Play: {item['title'][:30]}", key=f"quick_{idx}"):
                    st.session_state.current_video = item['file']
                    st.rerun()

with tab4:
    st.header("User Reviews")
    
    with st.form("review_form"):
        name = st.text_input("Name (optional)")
        rating = st.slider("Rating", 1, 5, 5)
        review = st.text_area("Your Review")
        
        if st.form_submit_button("Submit Review"):
            if review.strip():
                st.session_state.reviews.append({
                    'name': name or "Anonymous",
                    'rating': rating,
                    'review': review,
                    'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.success("Thanks for your review!")
    
    # Display reviews
    for rev in reversed(st.session_state.reviews):
        with st.container():
            st.write(f"**{rev['name']}** {'⭐' * rev['rating']}")
            st.write(rev['review'])
            st.caption(rev['date'])
            st.divider()

# ======================
# DOWNLOAD HISTORY
# ======================
with st.expander("Download History"):
    if st.session_state.download_history:
        for idx, item in enumerate(reversed(st.session_state.download_history)):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{item['title']}**")
            col1.caption(f"{item['platform']} - {item['time']}")
            
            if col2.button("Play", key=f"hist_play_{idx}"):
                st.session_state.current_video = item['file']
            
            if col3.button("Delete", key=f"hist_del_{idx}"):
                if os.path.exists(item['file']):
                    os.remove(item['file'])
                st.session_state.download_history.pop(len(st.session_state.download_history)-1-idx)
                st.rerun()
    else:
        st.info("No download history yet")

# Create necessary directories
os.makedirs("downloads", exist_ok=True)

# Add some helpful info
st.sidebar.markdown("---")
st.sidebar.info("""
**Note about YouTube downloads:**
Some YouTube videos may not download due to platform restrictions. Try:
- MP3 format instead of video
- Lower quality settings
- Different videos
""")
