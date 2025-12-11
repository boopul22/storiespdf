#!/usr/bin/env python3
"""
Unofficial API wrapper for Google's Whisk AI image generation tool.
This is a reverse-engineered wrapper and may break if Google changes their API.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Union
import requests
import uuid
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASPECT_RATIO_MAP = {
    "landscape": "IMAGE_ASPECT_RATIO_LANDSCAPE",
    "portrait": "IMAGE_ASPECT_RATIO_PORTRAIT",
    "square": "IMAGE_ASPECT_RATIO_SQUARE",
}

class GenerationRequest:
    """Represents a request to generate images with Whisk."""
    
    def __init__(
        self,
        prompt: str,
        aspect_ratio: str = "landscape",
        precise_mode: bool = False,
        safe_mode: bool = True,
        image_model: str = "IMAGEN_3_5",
        seed: Optional[int] = None,
        media_category: str = "MEDIA_CATEGORY_BOARD",
    ):
        self.prompt = prompt
        self.aspect_ratio = aspect_ratio
        self.precise_mode = precise_mode
        self.safe_mode = safe_mode
        self.image_model = image_model
        self.seed = seed if seed is not None else random.randint(1, 10**6)
        self.media_category = media_category
    
    def to_dict(self) -> Dict:
        """Convert the request to a dictionary for the API."""
        aspect_enum = ASPECT_RATIO_MAP.get(self.aspect_ratio, ASPECT_RATIO_MAP["landscape"])
        return {
            "clientContext": {
                "workflowId": str(uuid.uuid4()),
                "tool": "BACKBONE",
                # sessionId is optional; server accepts it missing
            },
            "imageModelSettings": {
                "imageModel": self.image_model,
                "aspectRatio": aspect_enum,
            },
            "seed": self.seed,
            "prompt": self.prompt,
            "mediaCategory": self.media_category,
        }

class WhiskClient:
    """Client for interacting with Google's Whisk AI image generation API."""
    
    def __init__(self, access_token: str, endpoint_type: str = "generateImage"):
        """
        Initialize the Whisk client.
        
        Args:
            access_token: OAuth access token from Google
            endpoint_type: Type of endpoint to use - "generateImage" (default) or "runImageRecipe"
        """
        self.access_token = access_token
        self.endpoint_type = endpoint_type
        self.base_url = "https://aisandbox-pa.googleapis.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Origin": "https://labs.google",
            "Referer": "https://labs.google/fx/tools/whisk",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Ch-Ua": '"Google Chrome";v="139", "Chromium";v="139", "Not_A Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
        })
    
    def generate_image(
        self, 
        request: GenerationRequest,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Dict:
        """
        Generate an image using the Whisk API.
        
        Args:
            request: GenerationRequest object containing the generation parameters
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            API response as a dictionary
            
        Raises:
            Exception: If all retry attempts fail
        """
        # Choose endpoint based on endpoint_type
        if self.endpoint_type == "runImageRecipe":
            endpoint = f"{self.base_url}/whisk:runImageRecipe"
        else:
            endpoint = f"{self.base_url}/whisk:generateImage"
            
        payload = request.to_dict()
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Making request to Whisk API (attempt {attempt})")
                logger.info(f"Endpoint: {endpoint}")
                logger.info(f"Endpoint Type: {self.endpoint_type}")
                logger.info(f"Payload: {json.dumps(payload, indent=2)}")
                
                response = self.session.post(endpoint, json=payload)
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif response.status_code == 400:
                    # Provide detailed error information for 400 errors
                    try:
                        error_body = response.json()
                        logger.error(f"Bad Request (400) - Response body: {json.dumps(error_body, indent=2)}")
                    except:
                        logger.error(f"Bad Request (400) - Response text: {response.text}")
                    
                    if attempt == max_retries:
                        raise Exception(f"Bad Request (400): {response.text}")
                    time.sleep(retry_delay)
                elif response.status_code == 401:
                    logger.error("Unauthorized (401) - Check your access token")
                    if attempt == max_retries:
                        raise Exception("Unauthorized (401): Invalid or expired access token")
                    time.sleep(retry_delay)
                elif response.status_code == 403:
                    logger.error("Forbidden (403) - Access denied to Whisk API")
                    if attempt == max_retries:
                        raise Exception("Forbidden (403): Access denied to Whisk API")
                    time.sleep(retry_delay)
                else:
                    logger.warning(f"Request failed with status {response.status_code}")
                    if attempt == max_retries:
                        response.raise_for_status()
                    time.sleep(retry_delay)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt == max_retries:
                    raise Exception(f"All retry attempts failed: {e}")
                time.sleep(retry_delay)
        
        raise Exception("All retry attempts failed")

def main():
    print("Whisk API Wrapper Example")
    print("=" * 50)
    
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    access_token = os.getenv("WHISK_ACCESS_TOKEN")
    if not access_token:
        print("Error: WHISK_ACCESS_TOKEN not found in .env")
        return
        
    client = WhiskClient(access_token)
    request = GenerationRequest(
        prompt="A beautiful sunset over mountains",
        aspect_ratio="landscape"
    )
    try:
        result = client.generate_image(request)
        print("Generation successful!")
        print(f"Top level keys: {list(result.keys())}")
        
        if 'imagePanels' in result:
            print(f"Found 'imagePanels' with {len(result['imagePanels'])} items")
            if len(result['imagePanels']) > 0:
                panel = result['imagePanels'][0]
                print(f"First panel keys: {list(panel.keys())}")
                # Check for generatedImages inside panel
                if 'generatedImages' in panel:
                     print(f"Found 'generatedImages' in panel with {len(panel['generatedImages'])} items")
                     if len(panel['generatedImages']) > 0:
                         print(f"First generatedImage keys: {list(panel['generatedImages'][0].keys())}")
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    main()
