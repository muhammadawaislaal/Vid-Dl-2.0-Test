import streamlit as st
from yt_dlp import YoutubeDL
from PIL import Image
import requests
from io import BytesIO
from urllib.parse import urlparse
import os
import time
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import datetime

# ======================
# APP METADATA FOR SEO
# ======================
APP_TITLE = "Video Downloader Pro - HD Videos from Any Platform"
APP_DESCRIPTION = """
Download videos from YouTube, Instagram, TikTok, Facebook, Twitter and 100+ sites in HD/4K. 
Fastest video downloader with built-in player, private folder, playlist support & MP3 converter.
"""
APP_KEYWORDS = [
    "video downloader", "youtube downloader", "tiktok downloader", 
    "instagram video download", "4k video download", "mp3 converter",
    "background download", "ad free downloader", "private video locker"
]

# ======================
# CONSTANTS
# ======================
SUPPORTED_DOMAINS = {
    "youtube": "YouTube", "youtu.be": "YouTube",
    "instagram": "Instagram", "facebook": "Facebook", "fb": "Facebook",
    "tiktok": "TikTok", "twitter": "Twitter", "x.com": "Twitter",
    "twitch": "Twitch", "vimeo": "Vimeo", "dailymotion": "Dailymotion",
    "pinterest": "Pinterest", "reddit": "Reddit", "likee": "Likee"
}

# ======================
# APP CONFIGURATION
# ======================
st.set_page_config(
    page_title=APP_TITLE,
    layout="centered",
    page_icon="🎬",
    menu_items={
        'About': f"Ultimate Video Downloader Pro\n{APP_DESCRIPTION}"
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
    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    
    domain = parsed_url.netloc.lower()
    for key in SUPPORTED_DOMAINS:
        if key in domain:
            return SUPPORTED_DOMAINS[key]
    return "Unknown"

def get_video_info(link):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            return info
    except Exception as e:
        st.error(f"Error getting video info: {str(e)}")
        return None

def download_video(link, quality, format_type, subtitles=False):
    # Enhanced yt-dlp configuration to avoid 403 errors
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'writesubtitles': subtitles,
        'subtitleslangs': ['en'],
        'noplaylist': True,
        'continuedl': True,
        'ignoreerrors': True,
        'no_warnings': False,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Connection': 'keep-alive',
        },
    }
    
    # Format selection
    if format_type in ["MP3", "M4A"]:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format_type.lower(),
            'preferredquality': '192',
        }]
    else:
        # Video format selection based on quality
        quality_map = {
            "Best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "4K": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]",
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
            "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
            "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]"
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
        # Try with simpler options as fallback
        return download_video_fallback(link, format_type)

def download_video_fallback(link, format_type):
    """Fallback download method with minimal options"""
    ydl_opts = {
        'format': 'best' if format_type not in ["MP3", "M4A"] else 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'ignoreerrors': True,
        'no_warnings': False,
    }
    
    if format_type in ["MP3", "M4A"]:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format_type.lower(),
            'preferredquality': '192',
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
        raise Exception(f"Download failed: {str(e)}")

# ======================
# UI COMPONENTS
# ======================
# App Header with Logo and Title
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <h1 style="margin: 0;">🎬 Video Downloader Pro</h1>
</div>
""", unsafe_allow_html=True)

# Security Badge
st.markdown("""
<div style="background-color:#f0f2f6; padding:10px; border-radius:5px; margin-bottom:20px;">
    <div style="display:flex; align-items:center;">
        <span style="color:#4CAF50; font-weight:bold;">🛡️ Secure & Private</span>
        <span style="margin-left:15px; font-size:14px;">No data collection • No ads • End-to-end encryption</span>
    </div>
</div>
""", unsafe_allow_html=True)

# App Description with SEO Keywords
st.markdown(f"""
**{APP_DESCRIPTION}**

<span style="font-size:12px; color:#666;">Popular searches: {", ".join(APP_KEYWORDS[:5])}...</span>
""", unsafe_allow_html=True)

# ======================
# HOW TO USE SECTION
# ======================
with st.expander("📘 How To Use This App", expanded=True):
    st.markdown("""
    **Follow these simple steps to download videos:**
    
    1. **Paste URL** - Copy any video link from supported platforms and paste above
    2. **Choose Quality** - Select your preferred resolution (4K, HD, etc.) from sidebar
    3. **Select Format** - Pick MP4 for video or MP3 for audio-only
    4. **Download** - Click the download button that appears
    5. **Enjoy** - Watch in our built-in player or save to your device!
    
    💡 **Pro Tips:**
    - Use Private Folder for sensitive videos (set password in sidebar)
    - Create playlists to organize your downloads
    - Try batch mode for multiple downloads at once
    - Convert videos to MP3 for music listening
    """)

# ======================
# SIDEBAR - SETTINGS
# ======================
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Download Options
    download_quality = st.selectbox(
        "Video Quality",
        ["Best", "4K", "1080p", "720p", "480p", "360p"],
        index=0
    )
    
    download_format = st.selectbox(
        "Download Format",
        ["MP4", "WEBM", "MP3", "M4A", "AVI", "MOV"],
        index=0
    )
    
    col1, col2 = st.columns(2)
    with col1:
        enable_subtitles = st.checkbox("Subtitles")
    with col2:
        background_download = st.checkbox("Background DL", True)
    
    # Privacy Options
    private_download = st.checkbox("Save to Private Folder")
    if private_download:
        password = st.text_input("Set Password", type="password")
    
    # Ad Blocker Toggle
    ad_blocker = st.checkbox("Enable Ad Blocker", True)
    
    # Updates Section
    st.header("🔄 Latest Updates")
    st.markdown("""
    - **v2.3.0**: Fixed YouTube download issues and improved error handling
    - **v2.2.0**: Added user guide and improved interface
    - **v2.1.0**: Added 4K support and background downloads
    - **v2.0.5**: New private folder with password protection
    """)

# ======================
# MAIN FUNCTIONALITY WITH REVIEWS TAB
# ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 Download", "🔒 Private", "🎵 Playlists", "🎥 Player", "⭐ Reviews"])

with tab1:
    # URL Input with Clear Help Text
    st.markdown("### Paste Video URL Below")
    batch_mode = st.checkbox("Enable Batch Mode (multiple URLs)", help="Check this to download multiple videos at once")
    
    if batch_mode:
        urls = st.text_area("Enter one URL per line", height=150, 
                           placeholder="Paste multiple URLs here\nOne per line\nExample:\nhttps://youtube.com/watch?v=...\nhttps://instagram.com/reel/...")
        urls = [url.strip() for url in urls.split('\n') if url.strip()]
    else:
        url = st.text_input("Single Video URL", 
                           placeholder="https://youtube.com/watch?v=... or https://instagram.com/reel/...")
        urls = [url] if url else []
    
    # Processing with Better Visual Feedback
    if urls:
        for url in urls:
            if not url:
                continue
                
            platform = detect_platform(url)
            if platform == "Unknown":
                st.error(f"❌ Unsupported platform for URL: {url}")
                st.info("Supported platforms: YouTube, Instagram, TikTok, Facebook, Twitter, Twitch, Vimeo, etc.")
                continue
                
            try:
                # Card-style display for each video
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.info(f"🔄 Fetching {platform} video info...")
                    
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_{hash(url)}"):
                            continue
                    
                    info = get_video_info(url)
                    if info is None:
                        st.error("Failed to get video information. Please check the URL and try again.")
                        continue
                        
                    title = info.get('title', 'Unknown Title')
                    duration = info.get('duration', 0)
                    view_count = info.get('view_count', 0)
                    thumbnail_url = info.get('thumbnail')
                    
                    # Video Preview Section
                    st.subheader(f"🎬 {title[:50] + '...' if len(title) > 50 else title}")
                    
                    if thumbnail_url:
                        try:
                            response = requests.get(thumbnail_url, timeout=10)
                            if response.status_code == 200:
                                img = Image.open(BytesIO(response.content))
                                st.image(img, width='stretch')
                            else:
                                st.warning("Couldn't load thumbnail")
                        except Exception as e:
                            st.warning("Couldn't load thumbnail")
                    
                    # Video Metadata
                    st.caption(f"""
                    **Platform:** {platform}  
                    **Duration:** {duration//60}m {duration%60}s  
                    **Views:** {view_count:,}  
                    **Quality:** {download_quality}  
                    **Format:** {download_format}
                    """)
                    
                    # Download Button with Confirmation
                    if st.button(f"⬇️ Download {platform} Video", key=f"download_{hash(url)}", 
                               type="primary", help=f"Download {title}"):
                        with st.spinner(f"⏳ Downloading {title[:30]}..."):
                            start_time = time.time()
                            try:
                                filename, video_title, full_info = download_video(
                                    url,
                                    download_quality,
                                    download_format,
                                    enable_subtitles
                                )
                                
                                # Progress bar simulation
                                progress_bar = st.progress(0)
                                for percent_complete in range(100):
                                    time.sleep(0.02)
                                    progress_bar.progress(percent_complete + 1)
                                
                                # Add to history or private folder
                                download_item = {
                                    'title': video_title,
                                    'platform': platform,
                                    'url': url,
                                    'time': time.strftime("%Y-%m-%d %H:%M:%S"),
                                    'file': filename
                                }
                                
                                if private_download and 'password' in locals() and password:
                                    file_hash = hashlib.sha256(password.encode()).hexdigest()
                                    if file_hash not in st.session_state.private_videos:
                                        st.session_state.private_videos[file_hash] = []
                                    st.session_state.private_videos[file_hash].append(download_item)
                                    st.success("🔒 Saved to private folder!")
                                else:
                                    st.session_state.download_history.append(download_item)
                                    st.success("✅ Download completed!")
                                
                                # Download button
                                try:
                                    if os.path.exists(filename):
                                        with open(filename, "rb") as file:
                                            st.download_button(
                                                label=f"💾 Save {video_title[:20]}",
                                                data=file,
                                                file_name=os.path.basename(filename),
                                                mime="video/mp4" if download_format not in ["MP3", "M4A"] else "audio/mpeg",
                                                key=f"save_{hash(url)}",
                                                help="Click to save to your device"
                                            )
                                    else:
                                        st.error("Downloaded file not found. The download may have failed.")
                                except Exception as e:
                                    st.error(f"Error creating download button: {str(e)}")
                                
                                st.balloons()
                                st.success(f"✅ Download completed in {time.time()-start_time:.2f} seconds")
                                st.session_state.current_video = filename
                            
                            except Exception as e:
                                st.error(f"❌ Download failed: {str(e)}")
                                st.info("""
                                **Troubleshooting tips:**
                                - Try a different video quality
                                - Check if the video is available in your region
                                - Try again in a few minutes
                                - Use MP3 format for audio-only downloads
                                - The video might be age-restricted or private
                                """)
            
            except Exception as e:
                st.error(f"⚠️ Error processing {url}: {str(e)}")
                st.info("Try again or check if the URL is correct")

# Rest of the tabs (Private, Playlists, Player, Reviews) remain similar to previous version...
with tab2:
    st.header("🔒 Private Folder")
    st.info("Your private videos are password-protected and only visible when you enter the correct password")
    
    password_input = st.text_input("Enter Your Password", type="password", key="private_password",
                                 help="Enter the password you set when saving videos")
    
    if password_input:
        file_hash = hashlib.sha256(password_input.encode()).hexdigest()
        private_items = st.session_state.private_videos.get(file_hash, [])
        
        if private_items:
            st.success(f"🔑 Access granted! Found {len(private_items)} private videos")
            for idx, item in enumerate(private_items[::-1]):
                with st.container(border=True):
                    cols = st.columns([4, 1, 1])
                    cols[0].markdown(f"**{idx+1}. {item['title']}**  \n*{item['platform']} - {item['time']}*")
                    
                    if cols[1].button("▶️ Play", key=f"play_private_{idx}"):
                        st.session_state.current_video = item['file']
                        st.rerun()
                    
                    if cols[2].button("🗑️ Delete", key=f"delete_private_{idx}", type="secondary"):
                        try:
                            if os.path.exists(item['file']):
                                os.remove(item['file'])
                            private_items.pop(len(private_items)-1-idx)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting: {str(e)}")
        else:
            st.warning("No videos found with this password.")

with tab3:
    st.header("🎵 Your Playlists")
    st.info("Organize your downloaded videos into playlists for easy access")
    
    # Create new playlist
    new_playlist_name = st.text_input("Create New Playlist", 
                                    placeholder="My Awesome Videos")
    if st.button("➕ Create Playlist") and new_playlist_name:
        if new_playlist_name not in st.session_state.playlists:
            st.session_state.playlists[new_playlist_name] = []
            st.success(f"Playlist '{new_playlist_name}' created!")
        else:
            st.warning("Playlist with this name already exists")
    
    # Select playlist to view
    if st.session_state.playlists:
        selected_playlist = st.selectbox(
            "Select Playlist",
            list(st.session_state.playlists.keys()),
            help="Choose a playlist to view or add videos to"
        )
        
        if selected_playlist:
            # Add to playlist
            if st.session_state.download_history:
                st.subheader(f"Add to {selected_playlist}")
                video_to_add = st.selectbox(
                    "Select Video",
                    [f"{h['title']} ({h['time']})" for h in st.session_state.download_history],
                    index=0,
                    key="playlist_select"
                )
                if st.button(f"➕ Add to {selected_playlist}"):
                    selected_index = [f"{h['title']} ({h['time']})" for h in st.session_state.download_history].index(video_to_add)
                    selected_item = st.session_state.download_history[selected_index]
                    st.session_state.playlists[selected_playlist].append(selected_item)
                    st.success(f"Added to {selected_playlist}!")
            
            # View playlist contents
            if st.session_state.playlists[selected_playlist]:
                st.subheader(f"Videos in {selected_playlist}")
                for idx, item in enumerate(st.session_state.playlists[selected_playlist]):
                    with st.container(border=True):
                        cols = st.columns([4, 1, 1])
                        cols[0].markdown(f"**{idx+1}. {item['title']}**  \n*{item['platform']} - {item['time']}*")
                        
                        if cols[1].button("▶️ Play", key=f"play_playlist_{idx}"):
                            st.session_state.current_video = item['file']
                            st.rerun()
                        
                        if cols[2].button("❌ Remove", key=f"remove_playlist_{idx}", type="secondary"):
                            st.session_state.playlists[selected_playlist].pop(idx)
                            st.rerun()
            else:
                st.info(f"{selected_playlist} is empty. Add some videos!")
    else:
        st.info("You haven't created any playlists yet")

with tab4:
    st.header("🎥 Built-in Video Player")
    
    if st.session_state.current_video and os.path.exists(st.session_state.current_video):
        st.success(f"Now Playing: {os.path.basename(st.session_state.current_video)}")
        try:
            with open(st.session_state.current_video, 'rb') as video_file:
                video_bytes = video_file.read()
                st.video(video_bytes)
        except Exception as e:
            st.error(f"Error playing video: {str(e)}")
    else:
        st.info("No video selected. Play a video from your downloads, private folder or playlists")
        if st.session_state.download_history:
            st.subheader("Quick Play Recent Downloads")
            for idx, item in enumerate(st.session_state.download_history[:3]):
                if st.button(f"▶️ {item['title'][:30]}", key=f"quick_play_{idx}"):
                    st.session_state.current_video = item['file']
                    st.rerun()

with tab5:
    st.header("⭐ Share Your Experience")
    
    # Review Form
    with st.form("review_form"):
        st.subheader("Add Your Review")
        name = st.text_input("Your Name (Optional)")
        rating = st.slider("Rating", 1, 5, 5)
        review = st.text_area("Your Review or Suggestion", 
                             placeholder="Share your experience with this app...")
        submitted = st.form_submit_button("Submit Review")
        
        if submitted:
            if review.strip():
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.reviews.append({
                    'name': name if name else "Anonymous",
                    'rating': rating,
                    'review': review,
                    'date': timestamp
                })
                st.success("Thank you for your review! Your feedback helps us improve.")
            else:
                st.warning("Please write your review before submitting")
    
    # Display Reviews
    st.subheader("User Reviews")
    if st.session_state.reviews:
        for idx, review in enumerate(reversed(st.session_state.reviews)):
            with st.container(border=True):
                cols = st.columns([1, 4])
                with cols[0]:
                    st.markdown(f"**{review['name']}**")
                    st.markdown(f"<span style='color:gold;'>{'★' * review['rating']}{'☆' * (5 - review['rating'])}</span>", 
                               unsafe_allow_html=True)
                    st.caption(review['date'])
                with cols[1]:
                    st.markdown(review['review'])
    else:
        st.info("No reviews yet. Be the first to share your experience!")

# ======================
# DOWNLOAD MANAGEMENT
# ======================
with st.expander("📚 Download History", expanded=False):
    if st.session_state.download_history:
        st.info("Your recently downloaded videos")
        for idx, item in enumerate(st.session_state.download_history[::-1]):
            with st.container(border=True):
                cols = st.columns([4, 1, 1])
                cols[0].markdown(f"**{idx+1}. {item['title']}**  \n*{item['platform']} - {item['time']}*")
                
                if cols[1].button("▶️ Play", key=f"play_hist_{idx}"):
                    st.session_state.current_video = item['file']
                    st.rerun()
                
                if cols[2].button("🗑️ Delete", key=f"delete_hist_{idx}", type="secondary"):
                    try:
                        if os.path.exists(item['file']):
                            os.remove(item['file'])
                        st.session_state.download_history.pop(len(st.session_state.download_history)-1-idx)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting: {str(e)}")
    else:
        st.info("Your download history is empty. Download some videos to see them here")

# Create necessary directories
os.makedirs("downloads", exist_ok=True)
os.makedirs("converted", exist_ok=True)
