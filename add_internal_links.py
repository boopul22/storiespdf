#!/usr/bin/env python3
"""
Script to inject 'tamil story reading' keyword with link into all blog posts.
This adds an HTML anchor tag with the keyword for SEO purposes.
"""

import os
import re
from pathlib import Path
import shutil
from datetime import datetime

# Configuration
BLOG_DIR = Path("src/content/blog")
SITE_URL = "https://tamilkathai.in"
KEYWORD = "tamil story reading"
BACKUP_DIR = Path("backup_blog_posts")

# The HTML link to inject
LINK_HTML = f'<a href="{SITE_URL}">{KEYWORD}</a>'

# Text to add at the end of each blog post (after the content, before closing)
INJECTION_TEXT = f"""

---

**More stories**: For {LINK_HTML}, visit our collection of hundreds of Tamil stories.
"""


def create_backup():
    """Create a backup of all blog posts before modification."""
    if BACKUP_DIR.exists():
        # Add timestamp to avoid overwriting previous backups
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"backup_blog_posts_{timestamp}")
        shutil.copytree(BLOG_DIR, backup_path)
        print(f"✓ Backup created at: {backup_path}")
    else:
        shutil.copytree(BLOG_DIR, BACKUP_DIR)
        print(f"✓ Backup created at: {BACKUP_DIR}")


def process_blog_post(file_path):
    """
    Process a single blog post to inject the keyword with link.
    
    Args:
        file_path: Path to the markdown file
    
    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if link already exists
        if KEYWORD in content or SITE_URL in content:
            print(f"  ⊘ Skipped (already contains keyword/link): {file_path.name}")
            return False
        
        # Split frontmatter and content
        parts = content.split('---', 2)
        if len(parts) >= 3:
            # Has frontmatter
            frontmatter = parts[1]
            body = parts[2]
            
            # Add the injection text at the end of the body
            new_content = f"---{frontmatter}---{body.rstrip()}\n{INJECTION_TEXT}\n"
        else:
            # No frontmatter, just add at the end
            new_content = f"{content.rstrip()}\n{INJECTION_TEXT}\n"
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✓ Modified: {file_path.name}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error processing {file_path.name}: {e}")
        return False


def main(dry_run=False):
    """
    Main function to process all blog posts.
    
    Args:
        dry_run: If True, only show what would be done without making changes
    """
    print("=" * 60)
    print("Tamil Story Reading - Internal Link Injection Script")
    print("=" * 60)
    print(f"Blog directory: {BLOG_DIR}")
    print(f"Keyword: {KEYWORD}")
    print(f"Link URL: {SITE_URL}")
    print(f"Dry run: {dry_run}")
    print("=" * 60)
    
    if not BLOG_DIR.exists():
        print(f"✗ Error: Blog directory not found: {BLOG_DIR}")
        return
    
    # Get all markdown files
    md_files = list(BLOG_DIR.glob("*.md"))
    print(f"\nFound {len(md_files)} blog posts\n")
    
    if dry_run:
        print("DRY RUN MODE - No files will be modified\n")
        print("Sample injection text that would be added:")
        print("-" * 60)
        print(INJECTION_TEXT)
        print("-" * 60)
        print(f"\nThis would be added to {len(md_files)} files.")
        return
    
    # Create backup before making changes
    print("Creating backup...")
    create_backup()
    print()
    
    # Process each file
    modified_count = 0
    skipped_count = 0
    
    print("Processing blog posts...")
    for md_file in md_files:
        if process_blog_post(md_file):
            modified_count += 1
        else:
            skipped_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files: {len(md_files)}")
    print(f"Modified: {modified_count}")
    print(f"Skipped: {skipped_count}")
    print("=" * 60)
    print("\n✓ Done! All blog posts have been processed.")
    print(f"✓ Backup available at: {BACKUP_DIR}")


if __name__ == "__main__":
    import sys
    
    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv
    
    main(dry_run=dry_run)
