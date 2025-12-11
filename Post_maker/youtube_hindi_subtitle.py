#!/usr/bin/env python3
"""
YouTube Hindi Subtitle Fetcher
Fetches Hindi subtitles from a YouTube video URL using yt-dlp Python API.
"""

import sys
import os
import re

try:
    import yt_dlp
except ImportError:
    print("❌ yt-dlp is not installed!")
    print("\n📦 Install it using one of these methods:")
    print("   pip install yt-dlp")
    print("   or")
    print("   pip install yt-dlp --break-system-packages")
    print("   or")
    print("   brew install yt-dlp")
    sys.exit(1)


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    return url


def get_hindi_subtitles(video_url: str, output_dir: str = ".") -> tuple:
    """
    Fetch Hindi subtitles from a YouTube video using yt-dlp Python API.
    
    Args:
        video_url: YouTube video URL
        output_dir: Directory to save subtitles
    
    Returns:
        Tuple of (file_path, content)
    """
    video_id = extract_video_id(video_url)
    print(f"📺 Video ID: {video_id}")
    
    output_template = os.path.join(output_dir, f"hindi_subtitles_{video_id}")
    
    print("\n🔍 Looking for Hindi subtitles...")
    
    # yt-dlp options for downloading subtitles
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['hi', 'hi-IN'],
        'subtitlesformat': 'srt/vtt/best',
        'skip_download': True,
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'srt',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First, get video info to check available subtitles
            info = ydl.extract_info(video_url, download=False)
            
            # Check available subtitles
            subtitles = info.get('subtitles', {})
            auto_captions = info.get('automatic_captions', {})
            
            has_hindi = any(lang in subtitles for lang in ['hi', 'hi-IN'])
            has_auto_hindi = any(lang in auto_captions for lang in ['hi', 'hi-IN'])
            
            if has_hindi:
                print("✅ Found manual Hindi subtitles!")
            elif has_auto_hindi:
                print("✅ Found auto-generated Hindi subtitles!")
            else:
                print("⚠️  No Hindi subtitles available.")
                print("\n📋 Available subtitle languages:")
                if subtitles:
                    print(f"   Manual: {', '.join(subtitles.keys())}")
                if auto_captions:
                    print(f"   Auto: {', '.join(list(auto_captions.keys())[:10])}...")
                
                # Try English as fallback
                if 'en' in subtitles or 'en' in auto_captions:
                    print("\n🔄 Downloading English subtitles as fallback...")
                    ydl_opts['subtitleslangs'] = ['en', 'en-US', 'en-GB']
                else:
                    return None, None
            
            # Download the subtitles
            ydl.download([video_url])
        
        # Find the downloaded subtitle file
        subtitle_file = None
        for f in os.listdir(output_dir):
            if f.startswith(f"hindi_subtitles_{video_id}") and (f.endswith('.srt') or f.endswith('.vtt')):
                subtitle_file = os.path.join(output_dir, f)
                break
        
        if subtitle_file and os.path.exists(subtitle_file):
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n💾 Subtitles saved to: {subtitle_file}")
            return subtitle_file, content
        else:
            print("❌ Subtitle file not created.")
            return None, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None


def main():
    """Main function to run the subtitle fetcher."""
    print("=" * 50)
    print("🎬 YouTube Hindi Subtitle Fetcher")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    else:
        video_url = input("\n📎 Enter YouTube URL: ").strip()
    
    if not video_url:
        print("❌ No URL provided!")
        return
    
    print(f"\n🔗 Processing: {video_url}")
    
    subtitle_file, content = get_hindi_subtitles(video_url)
    
    if content:
        print("\n" + "=" * 50)
        print("📝 SUBTITLES PREVIEW (first 1000 chars):")
        print("=" * 50)
        print(content[:1000])
        if len(content) > 1000:
            print("\n... (truncated)")
        print("=" * 50)
        print(f"\n✅ Total characters: {len(content)}")
        print(f"📄 File saved: {subtitle_file}")


if __name__ == "__main__":
    main()
