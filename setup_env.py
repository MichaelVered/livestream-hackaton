#!/usr/bin/env python3
"""
Setup script to create .env file for Gemini Live API
"""

import os

def create_env_file():
    """Create .env file with API key prompt"""
    print("Gemini Live API Setup")
    print("=" * 30)
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    # Get API key from user
    print("\nPlease enter your Gemini API key:")
    print("Get your API key from: https://aistudio.google.com/app/apikey")
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Setup cancelled.")
        return
    
    # Create .env content
    env_content = f"""# Gemini Live API Configuration
# Get your API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY={api_key}

# Camera Configuration
DEFAULT_CAMERA_INDEX=0
DEFAULT_FRAME_INTERVAL=0.5

# Video Configuration
DEFAULT_WIDTH=1280
DEFAULT_HEIGHT=720
DEFAULT_FPS=30
JPEG_QUALITY=85
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("\n✅ .env file created successfully!")
        print("You can now run: python gemini_live_integration.py")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    create_env_file()

