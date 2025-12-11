#!/usr/bin/env python3
"""
YouTube to Tamil Readable Content Converter
Orchestrates the workflow:
1. Fetch Subtitles (youtube_hindi_subtitle)
2. Convert to Readable Tamil Content (Gemini)
3. Generate Image Prompt (Gemini)
4. Generate Image (Whisk)
5. Upload Image (R2)
6. Save Markdown
"""

import os
import sys
import json
import time
import requests
import boto3
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Import local modules
# Assuming these are in the same directory
import youtube_hindi_subtitle
import whsik_image

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WHISK_ACCESS_TOKEN = os.getenv("WHISK_ACCESS_TOKEN")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

# Validate Config
missing_config = []
if not GEMINI_API_KEY: missing_config.append("GEMINI_API_KEY")
if not WHISK_ACCESS_TOKEN: missing_config.append("WHISK_ACCESS_TOKEN")
if not R2_ACCESS_KEY_ID: missing_config.append("R2_ACCESS_KEY_ID")
if not R2_SECRET_ACCESS_KEY: missing_config.append("R2_SECRET_ACCESS_KEY")
if not R2_ACCOUNT_ID: missing_config.append("R2_ACCOUNT_ID")
if not R2_BUCKET_NAME: missing_config.append("R2_BUCKET_NAME")
if not R2_PUBLIC_URL: missing_config.append("R2_PUBLIC_URL")

if missing_config:
    print(f"❌ Missing environment variables: {', '.join(missing_config)}")
    sys.exit(1)

# Initialize Clients
genai.configure(api_key=GEMINI_API_KEY)
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 600000,
  "response_mime_type": "text/plain",
}
gemini_model = genai.GenerativeModel(
  model_name="gemini-flash-latest",
  generation_config=generation_config,
)

whisk_client = whsik_image.WhiskClient(WHISK_ACCESS_TOKEN)

s3_client = boto3.client(
    's3',
    endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name='auto'  # R2 doesn't use regions like standard S3, 'auto' is fine
)

def read_format_file(path="format.md"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️ Warning: {path} not found. Using default format.")
        return """---
title: '{title}'
description: '{description}'
pubDate: '{date}'
heroImage: '{image_url}'
---

{content}
"""

def cleanup_subtitles(srt_content):
    """Remove timestamps and line numbers from SRT to reduce token count"""
    import re
    
    lines = srt_content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
        # Skip line numbers (just digits)
        if line.isdigit():
            continue
        # Skip timestamp lines (format: 00:00:00,000 --> 00:00:00,000)
        if re.match(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', line):
            continue
        # Keep the actual text
        cleaned_lines.append(line)
    
    # Join with spaces, then clean up multiple spaces
    text = ' '.join(cleaned_lines)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def generate_story_metadata(subtitle_text):
    """Generate title and visual concepts from story - now generates 2-3 scene visuals for better SEO"""
    print("🧠 Analyzing story for metadata and multiple visual scenes...")
    
    prompt = f"""
    Analyze the following subtitle text and extract/generate metadata for a story.
    
    **Subtitle Text:**
    {subtitle_text[:6000]}... (truncated)
    
    **Requirements:**
    1. **Tamil Title**: Short, catchy title (max 5 words).
    2. **English Title**: Translation of the Tamil title (max 5 words).
    3. **Visual Scenes**: Generate 2-3 different visual scene descriptions from key moments in the story.
       - Each scene should describe characters, setting, emotion, and action
       - Scenes should be from different parts of the story (beginning, middle, climax)
       - Focus on visually interesting moments
    
    **Output (JSON format):**
    {{
        "tamil_title": "...",
        "english_title": "...",
        "visual_scenes": [
            {{"scene_name": "Opening Scene", "description": "...", "tamil_caption": "..."}},
            {{"scene_name": "Key Moment", "description": "...", "tamil_caption": "..."}},
            {{"scene_name": "Climax", "description": "...", "tamil_caption": "..."}}
        ]
    }}
    """
    
    try:
        response = gemini_model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ Metadata Generation Error: {e}")
        return {
            "tamil_title": "ஒரு சுவாரஸ்யமான கதை", 
            "english_title": "An Interesting Story", 
            "visual_scenes": [
                {"scene_name": "Scene 1", "description": "A magical forest with cute animals", "tamil_caption": "மந்திர காடு"},
                {"scene_name": "Scene 2", "description": "Characters having an adventure", "tamil_caption": "சாகசம்"}
            ]
        }

def generate_readable_content(subtitle_text, hero_image_url="", scene_images=None, title_override=None):
    """Convert subtitle text to clean, readable Tamil story with multiple embedded images for SEO"""
    print("🤖 Converting to readable Tamil story with embedded images...")
    
    from datetime import datetime
    today = datetime.now().strftime("%b %d %Y")
    
    title_line = f"title: '{title_override}'" if title_override else "title: 'கதையின் தலைப்பு'"
    
    # Prepare image insertion instructions
    scene_images = scene_images or []
    image_instructions = ""
    if scene_images:
        image_list = "\n".join([
            f"- Image {i+1}: URL=`{img['url']}` Caption=`{img['caption']}`" 
            for i, img in enumerate(scene_images)
        ])
        image_instructions = f"""
    **IMPORTANT - IMAGE INSERTION FOR SEO:**
    You MUST insert these images into the content at appropriate story points:
    {image_list}
    
    **Image Format:** Insert each image using this exact markdown format:
    ![caption](image_url)
    *caption*
    
    **Placement Rules:**
    - Insert images at natural story breaks (between paragraphs)
    - Space images evenly throughout the content
    - First image: after the first 2-3 paragraphs
    - Second image: near the middle or climax of the story
    - Third image (if any): near the end
    - DO NOT cluster images together
    """
    
    prompt = f"""
    You are a Tamil translator. Convert the Hindi/English subtitle text to Tamil.
    
    **CRITICAL - STRICT TRANSLATION:**
    - ONLY translate what is in the subtitles - DO NOT add any new content
    - DO NOT invent new dialogues, scenes, or descriptions that are not in the subtitles
    - DO NOT cut or summarize - include EVERYTHING from start to end
    - If the subtitles end mid-story, your output should also end there
    - This is a TRANSLATION task, not a creative writing task
    {image_instructions}
    
    **OUTPUT FORMAT:**
    ---
    {title_line}
    description: 'சுருக்கமான விளக்கம்'
    pubDate: '{today}'
    heroImage: '{hero_image_url}'
    ---
    
    கதையின் உள்ளடக்கம்...
    
    **CONTENT RULES:**
    - Translate all dialogues and narration exactly as in subtitles
    - NO section headers (##), NO bullet points, NO lists
    - Write as flowing paragraphs only
    - Keep all dialogues in quotes
    - Make it readable in Tamil
    - INSERT the provided images at appropriate story breaks
    
    **SUBTITLE TEXT TO TRANSLATE:**
    {subtitle_text}
    
    **OUTPUT:**
    Frontmatter + Complete translation with embedded images throughout.
    DO NOT wrap the output in markdown code blocks (no ```markdown or ``` wrappers).
    Start directly with '---' for the frontmatter.
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        content = response.text
        
        # Post-process: Remove markdown code block wrappers if present
        content = content.strip()
        if content.startswith('```markdown'):
            content = content[len('```markdown'):].strip()
        elif content.startswith('```'):
            content = content[3:].strip()
        if content.endswith('```'):
            content = content[:-3].strip()
        
        return content
    except Exception as e:
        print(f"❌ Gemini Generation Error: {e}")
        return None

def generate_image_prompt(scene, is_hero=False, title_text=None):
    """Generate a cartoon-style image prompt for a scene"""
    print(f"🎨 Generating cartoon-style prompt for: {scene.get('scene_name', 'Scene')}...")
    
    visual_description = scene.get('description', 'A story scene')
    
    if is_hero and title_text:
        # Hero image includes title text
        prompt = f"""
        Create a prompt for an AI image generator (Imagen 3) to generate a "3D Animated Cartoon Movie Style" image.
        
        **Visual Subject:**
        {visual_description}
        
        **Style Requirements:**
        - **Style:** 3D Animated Cartoon Movie / Pixar / Disney / DreamWorks style
        - **Quality:** Ultra high quality, cute characters, vibrant colors, expressive faces
        - **Text Integration:** The image MUST feature the text "{title_text}" as a stylized title
        - **Text Style:** Integrate text artistically (floating, on a sign, or as movie title overlay)
        - **Composition:** Cinematic lighting, depth of field, dramatic angles
        - **Characters:** Cartoon-style with big expressive eyes, cute proportions
        
        **Output:**
        Just the prompt text (1-2 lines), nothing else.
        """
    else:
        # Scene images - no title, focus on story moment
        prompt = f"""
        Create a prompt for an AI image generator (Imagen 3) to generate a "3D Animated Cartoon Movie Style" scene.
        
        **Visual Subject:**
        {visual_description}
        
        **Style Requirements:**
        - **Style:** 3D Animated Cartoon Movie / Pixar / Disney / DreamWorks style
        - **Quality:** Ultra high quality, vibrant colors, expressive characters
        - **NO TEXT:** Do not include any text or titles in this image
        - **Composition:** Cinematic shot, story moment, emotional scene
        - **Characters:** Cartoon-style with big expressive eyes, cute/realistic proportions
        - **Mood:** Capture the emotion of the scene (happy, tense, dramatic, etc.)
        
        **Output:**
        Just the prompt text (1-2 lines), nothing else.
        """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Prompt Generation Error: {e}")
        return f"3D animated cartoon style, Pixar quality, {visual_description}"

def download_and_upload_image(whisk_response, prompt_short):
    print("☁️ Processing image...")
    try:
        # Extract Image URL from Whisk response
        # Note: Adjusting logic based on expected Whisk API response structure
        # Usually deeply nested: imagePanels -> [0] -> generatedImages -> [0] -> encodedImage or url
        # If it's encodedImage (base64) vs url. 
        # Looking at whsik_image.py, it doesn't explicitly show the structure, but typical Google Labs APIs return a temporary URL.
        
        image_url = None
        if 'imagePanels' in whisk_response and whisk_response['imagePanels']:
             if 'generatedImages' in whisk_response['imagePanels'][0]:
                 img_obj = whisk_response['imagePanels'][0]['generatedImages'][0]
                 if 'image' in img_obj and 'gcsUri' in img_obj['image']:
                     # If it returns a GCS URI (gs://), we might'nt be able to access it directly without auth.
                     # But often there is a 'url' or 'signedUrl' field.
                     # Let's check for 'url' first.
                     pass
                 
                 # Using the 'url' field if present, otherwise we iterate keys to find a likely candidate
                 # Based on my knowledge of this API, it might return a 'url' key directly in the generated image object
                 image_url = img_obj.get('url')
                 
                 # Backup: check for 'encodedImage'
                 if not image_url and 'encodedImage' in img_obj:
                    # It's base64 encoded
                    import base64
                    image_data = base64.b64decode(img_obj['encodedImage'])
                    return upload_to_r2(image_data, prompt_short)

        # If we didn't find a direct way, we might need to debug. 
        # For now, let's assume we can find a 'url'
        
        if not image_url: 
             # Fallback debug
             print(f"⚠️ Could not find obvious image URL. Response keys: {whisk_response.keys()}")
             return None

        # Download image
        img_resp = requests.get(image_url)
        if img_resp.status_code == 200:
            return upload_to_r2(img_resp.content, prompt_short)
        else:
            print(f"❌ Failed to download image from Whisk: {img_resp.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Image Processing Error: {e}")
        return None

def upload_to_r2(image_data, name_prefix):
    """Upload image to R2 in WebP format for better compression and speed"""
    from io import BytesIO
    from PIL import Image
    
    timestamp = int(time.time())
    filename = f"blog_hero_{timestamp}_{name_prefix[:20].replace(' ', '_')}.webp"
    key = f"generated_images/{filename}"
    
    print(f"⬆️ Converting to WebP and uploading to R2: {key}...")
    try:
        # Convert image to WebP format
        img = Image.open(BytesIO(image_data))
        webp_buffer = BytesIO()
        img.save(webp_buffer, format='WEBP', quality=85, method=6)
        webp_data = webp_buffer.getvalue()
        
        original_size = len(image_data)
        webp_size = len(webp_data)
        print(f"   📦 Size: {original_size/1024:.1f}KB → {webp_size/1024:.1f}KB ({100-webp_size*100/original_size:.0f}% smaller)")
        
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=key,
            Body=webp_data,
            ContentType='image/webp'
        )
        url = f"{R2_PUBLIC_URL}/{key}"
        print(f"✅ Upload successful: {url}")
        return url
    except Exception as e:
        print(f"❌ R2 Upload Error: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        url = input("🔗 Enter YouTube URL: ").strip()
    else:
        url = sys.argv[1]

    if not url:
        print("❌ No URL provided.")
        return


    # 1. Fetch Subtitles
    print("\n--- STEP 1: Fetching Subtitles ---")
    sub_file, sub_content = youtube_hindi_subtitle.get_hindi_subtitles(url)
    if not sub_content:
        print("❌ Failed to fetch subtitles.")
        return
    
    # Clean up subtitles (remove timestamps to reduce tokens)
    sub_content = cleanup_subtitles(sub_content)
    print(f"📝 Cleaned subtitle length: {len(sub_content)} chars")

    # 2. Generate Metadata (Title & Multiple Visual Scenes)
    print("\n--- STEP 2: Generating Story Metadata ---")
    metadata = generate_story_metadata(sub_content)
    if not metadata:
        print("❌ Failed to generate metadata.")
        return
        
    print(f"📋 Title (Tamil): {metadata.get('tamil_title')}")
    print(f"📋 Title (English): {metadata.get('english_title')}")
    
    visual_scenes = metadata.get('visual_scenes', [])
    print(f"🎨 Found {len(visual_scenes)} visual scenes to generate")
    for i, scene in enumerate(visual_scenes):
        print(f"   Scene {i+1}: {scene.get('scene_name', 'Unknown')} - {scene.get('description', '')[:50]}...")

    # 3. Generate Multiple Cartoon-Style Images (minimum 2 for SEO)
    print("\n--- STEP 3: Generating Cartoon-Style Images ---")
    
    # Ensure we have at least 2 scenes
    if len(visual_scenes) < 2:
        visual_scenes.append({
            "scene_name": "Story Scene", 
            "description": "Characters in an emotional moment from the story",
            "tamil_caption": "கதை காட்சி"
        })
    
    hero_image_url = ""
    scene_images = []  # List of {url, caption} for embedding in content
    
    english_title = metadata.get('english_title', 'Story')
    
    for i, scene in enumerate(visual_scenes):
        is_hero = (i == 0)  # First image is the hero image
        scene_name = scene.get('scene_name', f'Scene {i+1}')
        tamil_caption = scene.get('tamil_caption', 'கதை காட்சி')
        
        print(f"\n🖼️ Generating image {i+1}/{len(visual_scenes)}: {scene_name}")
        
        # Generate prompt (hero includes title, others don't)
        img_prompt = generate_image_prompt(
            scene, 
            is_hero=is_hero, 
            title_text=english_title if is_hero else None
        )
        print(f"   📝 Prompt: {img_prompt[:100]}...")
        
        try:
            whisk_req = whsik_image.GenerationRequest(prompt=img_prompt, aspect_ratio="landscape")
            whisk_res = whisk_client.generate_image(whisk_req)
            
            # Create filename prefix
            # Sanitize filename prefix to remove special characters
            raw_prefix = f"{english_title}_{scene_name}".replace(' ', '_')
            fname_prefix = "".join(x for x in raw_prefix if x.isalnum() or x == "_")
            image_url = download_and_upload_image(whisk_res, fname_prefix)
            
            if image_url:
                if is_hero:
                    hero_image_url = image_url
                    print(f"   ✅ Hero image generated: {image_url}")
                else:
                    scene_images.append({
                        "url": image_url,
                        "caption": tamil_caption
                    })
                    print(f"   ✅ Scene image generated: {image_url}")
            else:
                print(f"   ⚠️ Image {i+1} failed to upload")
                
        except Exception as e:
            print(f"   ❌ Image {i+1} Generation Failed: {e}")
    
    print(f"\n📊 Image Summary: Hero={bool(hero_image_url)}, Scenes={len(scene_images)}")
    print(f"   Total images for blog: {1 + len(scene_images)} (minimum 2 for SEO)")

    # 4. Generate Content (with hero image in frontmatter + scene images embedded)
    print("\n--- STEP 4: Generating Content with Embedded Images ---")
    content = generate_readable_content(
        sub_content, 
        hero_image_url=hero_image_url or "", 
        scene_images=scene_images,
        title_override=metadata.get('tamil_title')
    )
    if not content:
        print("❌ Failed to generate content.")
        return

    # 4. Save to file
    print("\n--- STEP 5: Saving ---")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use english title in filename if possible
    safe_title = metadata.get('english_title', 'tamil_story').replace(' ', '_').lower()
    # Remove special chars
    safe_title = "".join(x for x in safe_title if x.isalnum() or x == "_")
    output_filename = f"{safe_title}_{timestamp}.md"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"\n🎉 Success! Story saved to: {output_filename}")
    
    # Cleanup: Delete subtitle file after processing
    if sub_file and os.path.exists(sub_file):
        try:
            os.remove(sub_file)
            print(f"🧹 Cleaned up subtitle file: {sub_file}")
        except Exception as e:
            print(f"⚠️ Could not delete subtitle file: {e}")

if __name__ == "__main__":
    main()
