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

# ======================
# APP CONFIGURATION
# ======================
st.set_page_config(
    page_title="Video Downloader Pro",
    layout="centered",
    page_icon="🎬",
    menu_items={
        'About': "Video Downloader - Download from supported platforms"
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
    
    # Focus on platforms that work better
    supported_domains = {
        "vimeo": "Vimeo",
        "dailymotion": "Dailymotion",
        "facebook": "Facebook",
        "instagram": "Instagram",
        "tiktok": "TikTok",
        "twitter": "Twitter",
        "x.com": "Twitter",
        "twitch": "Twitch",
        "reddit": "Reddit",
        "pinterest": "Pinterest"
    }
    
    for key in supported_domains:
        if key in domain:
            return supported_domains[key]
    
    # YouTube detection (with warning)
    if "youtube" in domain or "youtu.be" in domain:
        return "YouTube*"
    
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

def download_video(link, format_type):
    # Simple configuration that works better on Streamlit Cloud
    ydl_opts = {
        'outtmpl': 'downloads/%(title).80s.%(ext)s',
        'noplaylist': True,
        'ignoreerrors': True,
        'no_warnings': False,
        'retries': 3,
        'fragment_retries': 3,
    }
    
    # For YouTube, use simpler format selection
    if "youtube" in link.lower() or "youtu.be" in link.lower():
        ydl_opts['format'] = 'best[height<=720]/best[height<=480]/best'
    else:
        # For other platforms
        ydl_opts['format'] = 'best'
    
    # Audio conversion
    if format_type in ["MP3", "M4A"]:
        ydl_opts['format'] = 'bestaudio/best'
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
        raise Exception(f"Download failed: {str(e)}")

# ======================
# UI COMPONENTS
# ======================
st.title("🎬 Video Downloader Pro")

st.markdown("""
<div style="background-color:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:20px;">
    <h4 style="margin:0; color:#4CAF50;">📱 Supported Platforms</h4>
    <p style="margin:5px 0; font-size:14px;">
        <strong>Works Well:</strong> Vimeo, Dailymotion, Facebook, Instagram, TikTok, Twitter<br>
        <strong>Limited:</strong> YouTube* (may not work due to restrictions)<br>
        <strong>Also:</strong> Twitch, Reddit, Pinterest
    </p>
</div>
""", unsafe_allow_html=True)

# ======================
# MAIN DOWNLOAD INTERFACE
# ======================
st.header("📥 Download Video")

url = st.text_input(
    "Paste Video URL Here", 
    placeholder="https://vimeo.com/... or https://facebook.com/...",
    key="url_input"
)

if url:
    platform = detect_platform(url)
    
    if platform == "Unknown":
        st.error("❌ Unsupported platform. Please use Vimeo, Facebook, Instagram, TikTok, or other supported sites.")
        st.info("""
        **Recommended platforms that work well:**
        - Vimeo.com
        - Facebook.com/...
        - Instagram.com/reel/...
        - TikTok.com/...
        - Twitter.com/...
        - Dailymotion.com
        """)
    else:
        if platform == "YouTube*":
            st.warning("⚠️ YouTube downloads are currently limited due to platform restrictions. Try other platforms for better results.")
        
        with st.spinner(f"🔍 Analyzing {platform} video..."):
            info = get_video_info(url)
            
        if info is None:
            st.error("❌ Failed to get video information.")
            st.markdown("""
            **Possible reasons:**
            - Video is private or age-restricted
            - Platform is blocking access
            - URL is incorrect
            - Try a different video platform
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
                        else:
                            st.info("📺 Video Preview")
                    except:
                        st.info("📺 Video Preview")
                else:
                    st.info("📺 Video Preview")
            
            with col2:
                st.subheader(title[:60] + '...' if len(title) > 60 else title)
                st.caption(f"**Platform:** {platform}")
                if duration > 0:
                    minutes = duration // 60
                    seconds = duration % 60
                    st.caption(f"**Duration:** {minutes}:{seconds:02d}")
                
                # Format selection
                download_format = st.selectbox(
                    "Download Format",
                    ["MP4", "MP3"],
                    index=0,
                    help="MP3 works better for restricted videos"
                )
                
                # Download button
                if st.button("⬇️ Download Video", type="primary", use_container_width=True):
                    with st.spinner("⏳ Downloading... Please wait"):
                        progress_bar = st.progress(0)
                        
                        try:
                            filename, video_title, full_info = download_video(url, download_format)
                            
                            # Simulate progress
                            for i in range(100):
                                progress_bar.progress(i + 1)
                                time.sleep(0.02)
                            
                            # Save to history
                            download_item = {
                                'title': video_title,
                                'platform': platform,
                                'url': url,
                                'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'file': filename,
                                'format': download_format
                            }
                            
                            st.session_state.download_history.append(download_item)
                            st.success("✅ Download completed!")
                            
                            # Download button
                            try:
                                if os.path.exists(filename):
                                    file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
                                    with open(filename, "rb") as file:
                                        st.download_button(
                                            label=f"💾 Save File ({file_size:.1f} MB)",
                                            data=file,
                                            file_name=os.path.basename(filename),
                                            mime="video/mp4" if download_format != "MP3" else "audio/mpeg",
                                            use_container_width=True
                                        )
                                else:
                                    st.error("Downloaded file not found.")
                            except Exception as e:
                                st.error(f"Error creating download button: {str(e)}")
                                
                        except Exception as e:
                            st.error(f"❌ Download failed: {str(e)}")
                            st.markdown("""
                            **Troubleshooting tips:**
                            - Try **MP3 format** instead of video
                            - Try a **different video platform**
                            - The video might be **region-restricted**
                            - Wait a few minutes and try again
                            - Use **Vimeo or Facebook** for more reliable downloads
                            """)

# ======================
# ADDITIONAL FEATURES
# ======================
tab1, tab2, tab3 = st.tabs(["📚 History", "🎵 Playlists", "⭐ Reviews"])

with tab1:
    st.header("Download History")
    
    if st.session_state.download_history:
        for idx, item in enumerate(reversed(st.session_state.download_history)):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(f"**{item['title']}**")
                col1.caption(f"{item['platform']} - {item['time']} - {item['format']}")
                
                if col2.button("Download", key=f"dl_{idx}"):
                    if os.path.exists(item['file']):
                        with open(item['file'], "rb") as f:
                            st.download_button(
                                label="Save Again",
                                data=f,
                                file_name=os.path.basename(item['file']),
                                mime="video/mp4" if item['format'] != "MP3" else "audio/mpeg",
                                key=f"save_again_{idx}"
                            )
                
                if col3.button("Delete", key=f"del_{idx}"):
                    try:
                        if os.path.exists(item['file']):
                            os.remove(item['file'])
                        st.session_state.download_history.pop(len(st.session_state.download_history)-1-idx)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting: {str(e)}")
                st.divider()
    else:
        st.info("No download history yet. Download some videos to see them here!")

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
            video_options = [f"{vid['title']} ({vid['platform']})" for vid in st.session_state.download_history]
            if video_options:
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
                col1.caption(f"{item['platform']} - {item['time']}")
                
                if col2.button("Remove", key=f"rem_pl_{idx}"):
                    st.session_state.playlists[selected].pop(idx)
                    st.rerun()
        else:
            st.info(f"{selected} is empty. Add some videos!")
    else:
        st.info("You haven't created any playlists yet")

with tab3:
    st.header("User Reviews")
    
    with st.form("review_form"):
        name = st.text_input("Your Name (optional)")
        rating = st.select_slider("Rating", options=[1, 2, 3, 4, 5], value=5)
        review = st.text_area("Your Review", placeholder="Share your experience...")
        
        if st.form_submit_button("Submit Review"):
            if review.strip():
                st.session_state.reviews.append({
                    'name': name or "Anonymous",
                    'rating': rating,
                    'review': review,
                    'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.success("Thank you for your review!")
            else:
                st.warning("Please write your review before submitting")
    
    # Display reviews
    if st.session_state.reviews:
        for rev in reversed(st.session_state.reviews):
            with st.container():
                st.write(f"**{rev['name']}** {'⭐' * rev['rating']}")
                st.write(rev['review'])
                st.caption(rev['date'])
                st.divider()
    else:
        st.info("No reviews yet. Be the first to share your experience!")

# ======================
# SIDEBAR
# ======================
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.info("""
    **Platform Recommendations:**
    
    ✅ **Vimeo** - Best results
    ✅ **Facebook** - Good compatibility  
    ✅ **Instagram** - Works well
    ✅ **TikTok** - Usually works
    ✅ **Twitter** - Generally reliable
    
    ⚠️ **YouTube** - Limited due to restrictions
    """)
    
    st.header("📊 Stats")
    st.write(f"Total Downloads: {len(st.session_state.download_history)}")
    st.write(f"Playlists: {len(st.session_state.playlists)}")
    st.write(f"Reviews: {len(st.session_state.reviews)}")

# Create necessary directories
os.makedirs("downloads", exist_ok=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 12px;'>"
    "Video Downloader Pro • Download from supported platforms • "
    "<a href='https://github.com/yt-dlp/yt-dlp' target='_blank'>Powered by yt-dlp</a>"
    "</div>",
    unsafe_allow_html=True
)
