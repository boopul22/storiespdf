#!/usr/bin/env python3
"""
Tamil Story Generator - Batch Processing GUI
A Tkinter-based UI for processing multiple YouTube videos at once.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the processing functions
import process_video

class TamilStoryGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tamil Story Generator - Batch Processor")
        self.root.geometry("800x700")
        self.root.configure(bg='#1a1a2e')
        
        # Queue for thread-safe logging
        self.log_queue = queue.Queue()
        
        # Processing state
        self.is_processing = False
        self.current_thread = None
        
        self.setup_ui()
        self.check_log_queue()
    
    def setup_ui(self):
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Helvetica', 18, 'bold'), 
                       background='#1a1a2e', foreground='#e94560')
        style.configure('TLabel', background='#1a1a2e', foreground='#eaeaea')
        style.configure('TButton', font=('Helvetica', 11), padding=10)
        style.configure('Green.TButton', font=('Helvetica', 12, 'bold'))
        style.configure('Red.TButton', font=('Helvetica', 11))
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a2e', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎬 Tamil Story Generator", style='Title.TLabel')
        title_label.pack(pady=(0, 10))
        
        subtitle = ttk.Label(main_frame, text="Generate cartoon-style illustrated Tamil stories from YouTube videos",
                            style='TLabel')
        subtitle.pack(pady=(0, 20))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="📝 Enter YouTube URLs (one per line):",
                                style='TLabel', font=('Helvetica', 11))
        instructions.pack(anchor='w', pady=(0, 5))
        
        # URL Input Area
        url_frame = tk.Frame(main_frame, bg='#16213e', padx=2, pady=2)
        url_frame.pack(fill=tk.BOTH, pady=(0, 15))
        
        self.url_text = scrolledtext.ScrolledText(
            url_frame, 
            height=8, 
            width=80,
            font=('Consolas', 11),
            bg='#0f3460',
            fg='#eaeaea',
            insertbackground='#e94560',
            selectbackground='#e94560'
        )
        self.url_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.url_text.insert(tk.END, "# Paste YouTube URLs here, one per line\n# Lines starting with # are ignored\n")
        
        # Buttons Frame
        button_frame = tk.Frame(main_frame, bg='#1a1a2e')
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.process_btn = tk.Button(
            button_frame, 
            text="▶ Start Processing",
            command=self.start_processing,
            font=('Helvetica', 12, 'bold'),
            bg='#00d98c',
            fg='white',
            activebackground='#00b876',
            activeforeground='white',
            padx=30,
            pady=10,
            cursor='hand2'
        )
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹ Stop",
            command=self.stop_processing,
            font=('Helvetica', 11),
            bg='#e94560',
            fg='white',
            activebackground='#c73e54',
            activeforeground='white',
            padx=20,
            pady=10,
            state=tk.DISABLED,
            cursor='hand2'
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = tk.Button(
            button_frame,
            text="🗑 Clear Log",
            command=self.clear_log,
            font=('Helvetica', 11),
            bg='#16213e',
            fg='white',
            activebackground='#0f3460',
            activeforeground='white',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.clear_btn.pack(side=tk.LEFT)
        
        # Progress Section
        progress_frame = tk.Frame(main_frame, bg='#1a1a2e')
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(progress_frame, text="Status: Ready", style='TLabel', 
                                     font=('Helvetica', 11, 'bold'))
        self.status_label.pack(anchor='w')
        
        self.progress_label = ttk.Label(progress_frame, text="", style='TLabel')
        self.progress_label.pack(anchor='w')
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Log Output Area
        log_label = ttk.Label(main_frame, text="📋 Processing Log:", style='TLabel', font=('Helvetica', 11))
        log_label.pack(anchor='w', pady=(10, 5))
        
        log_frame = tk.Frame(main_frame, bg='#16213e', padx=2, pady=2)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=80,
            font=('Consolas', 10),
            bg='#0f0f0f',
            fg='#00ff00',
            insertbackground='#00ff00',
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Configure tags for colored output
        self.log_text.tag_configure('success', foreground='#00d98c')
        self.log_text.tag_configure('error', foreground='#e94560')
        self.log_text.tag_configure('info', foreground='#00b4d8')
        self.log_text.tag_configure('warning', foreground='#ffc107')
    
    def log(self, message, tag='normal'):
        """Thread-safe logging"""
        self.log_queue.put((message, tag))
    
    def check_log_queue(self):
        """Check for new log messages and display them"""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                self.log_text.config(state=tk.NORMAL)
                if tag != 'normal':
                    self.log_text.insert(tk.END, message + '\n', tag)
                else:
                    self.log_text.insert(tk.END, message + '\n')
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.root.after(100, self.check_log_queue)
    
    def get_urls(self):
        """Extract valid URLs from input"""
        text = self.url_text.get("1.0", tk.END)
        urls = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and ('youtube.com' in line or 'youtu.be' in line):
                urls.append(line)
        return urls
    
    def start_processing(self):
        """Start processing URLs in a separate thread"""
        urls = self.get_urls()
        
        if not urls:
            messagebox.showwarning("No URLs", "Please enter at least one valid YouTube URL.")
            return
        
        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.url_text.config(state=tk.DISABLED)
        
        self.current_thread = threading.Thread(target=self.process_urls, args=(urls,), daemon=True)
        self.current_thread.start()
    
    def stop_processing(self):
        """Stop processing"""
        self.is_processing = False
        self.log("⏹ Processing stopped by user", 'warning')
        self.reset_ui()
    
    def reset_ui(self):
        """Reset UI to initial state"""
        self.process_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.url_text.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Ready")
        self.progress_label.config(text="")
    
    def clear_log(self):
        """Clear the log output"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def process_urls(self, urls):
        """Process multiple URLs one by one"""
        total = len(urls)
        successful = 0
        failed = 0
        
        self.log(f"🚀 Starting batch processing of {total} video(s)...", 'info')
        self.log("=" * 60)
        
        for i, url in enumerate(urls, 1):
            if not self.is_processing:
                break
            
            # Update progress
            progress = (i - 1) / total * 100
            self.root.after(0, lambda p=progress: self.progress_bar.configure(value=p))
            self.root.after(0, lambda i=i, t=total: self.status_label.config(text=f"Status: Processing {i}/{t}"))
            self.root.after(0, lambda u=url: self.progress_label.config(text=f"URL: {u[:60]}..."))
            
            self.log(f"\n📹 [{i}/{total}] Processing: {url}", 'info')
            
            try:
                # Process the video using existing logic
                self.process_single_video(url)
                successful += 1
                self.log(f"✅ [{i}/{total}] Completed successfully!", 'success')
            except Exception as e:
                failed += 1
                self.log(f"❌ [{i}/{total}] Failed: {str(e)}", 'error')
        
        # Final progress update
        self.root.after(0, lambda: self.progress_bar.configure(value=100))
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log(f"🎉 Batch Processing Complete!", 'success')
        self.log(f"   ✅ Successful: {successful}", 'success')
        if failed > 0:
            self.log(f"   ❌ Failed: {failed}", 'error')
        self.log(f"   📊 Total: {total}")
        
        self.root.after(0, self.reset_ui)
        self.is_processing = False
    
    def process_single_video(self, url):
        """Process a single video - adapted from process_video.main()"""
        import youtube_hindi_subtitle
        import whsik_image
        from datetime import datetime
        
        # 1. Fetch Subtitles
        self.log("   📥 Fetching subtitles...")
        sub_file, sub_content = youtube_hindi_subtitle.get_hindi_subtitles(url)
        if not sub_content:
            raise Exception("Failed to fetch subtitles")
        
        # Clean subtitles
        sub_content = process_video.cleanup_subtitles(sub_content)
        self.log(f"   📝 Subtitle length: {len(sub_content)} chars")
        
        # 2. Generate Metadata
        self.log("   🧠 Generating metadata...")
        metadata = process_video.generate_story_metadata(sub_content)
        if not metadata:
            raise Exception("Failed to generate metadata")
        
        tamil_title = metadata.get('tamil_title', 'Unknown')
        english_title = metadata.get('english_title', 'Unknown')
        self.log(f"   📋 Title: {tamil_title} ({english_title})")
        
        visual_scenes = metadata.get('visual_scenes', [])
        self.log(f"   🎨 Visual scenes: {len(visual_scenes)}")
        
        # 3. Generate Images
        if len(visual_scenes) < 2:
            visual_scenes.append({
                "scene_name": "Story Scene", 
                "description": "Characters in an emotional moment",
                "tamil_caption": "கதை காட்சி"
            })
        
        hero_image_url = ""
        scene_images = []
        
        for j, scene in enumerate(visual_scenes):
            if not self.is_processing:
                return
            
            is_hero = (j == 0)
            scene_name = scene.get('scene_name', f'Scene {j+1}')
            tamil_caption = scene.get('tamil_caption', 'கதை காட்சி')
            
            self.log(f"   🖼️ Generating image {j+1}/{len(visual_scenes)}: {scene_name}")
            
            try:
                img_prompt = process_video.generate_image_prompt(
                    scene, 
                    is_hero=is_hero, 
                    title_text=english_title if is_hero else None
                )
                
                whisk_req = whsik_image.GenerationRequest(prompt=img_prompt, aspect_ratio="landscape")
                whisk_res = process_video.whisk_client.generate_image(whisk_req)
                
                # Sanitize filename prefix to remove special characters for safe URLs
                raw_prefix = f"{english_title}_{scene_name}".replace(' ', '_')
                fname_prefix = "".join(x for x in raw_prefix if x.isalnum() or x == "_")
                
                image_url = process_video.download_and_upload_image(whisk_res, fname_prefix)
                
                if image_url:
                    if is_hero:
                        hero_image_url = image_url
                    else:
                        scene_images.append({"url": image_url, "caption": tamil_caption})
            except Exception as e:
                self.log(f"   ⚠️ Image {j+1} failed: {str(e)}", 'warning')
        
        self.log(f"   📊 Images: Hero={bool(hero_image_url)}, Scenes={len(scene_images)}")
        
        # 4. Generate Content
        self.log("   📝 Generating Tamil content...")
        content = process_video.generate_readable_content(
            sub_content, 
            hero_image_url=hero_image_url or "", 
            scene_images=scene_images,
            title_override=tamil_title
        )
        
        if not content:
            raise Exception("Failed to generate content")
        
        # 5. Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = english_title.replace(' ', '_').lower()
        safe_title = "".join(x for x in safe_title if x.isalnum() or x == "_")
        output_filename = f"{safe_title}_{timestamp}.md"
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.log(f"   💾 Saved: {output_filename}", 'success')


def main():
    root = tk.Tk()
    app = TamilStoryGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
