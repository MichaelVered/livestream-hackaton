#!/usr/bin/env python3
"""
Test script to check available Gemini models
"""

import google.generativeai as genai
from config import GEMINI_API_KEY

def test_models():
    """Test available Gemini models"""
    print("Testing Gemini API models...")
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    # List available models
    try:
        models = genai.list_models()
        print("Available models:")
        for model in models:
            print(f"  - {model.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
    
    # Test different model configurations
    model_configs = [
        {"name": "gemini-1.5-flash", "version": "v1beta"},
        {"name": "gemini-1.5-flash", "version": "v1"},
        {"name": "gemini-1.5-pro", "version": "v1beta"},
        {"name": "gemini-1.5-pro", "version": "v1"},
        {"name": "gemini-1.0-pro", "version": "v1beta"},
        {"name": "gemini-1.0-pro", "version": "v1"},
        {"name": "gemini-pro", "version": "v1beta"},
        {"name": "gemini-pro", "version": "v1"},
        {"name": "gemini-pro-vision", "version": "v1beta"},
        {"name": "gemini-pro-vision", "version": "v1"},
    ]
    
    for config in model_configs:
        try:
            print(f"\nTrying {config['name']} with {config['version']}...")
            model = genai.GenerativeModel(config['name'])
            response = model.generate_content("Hello")
            if response.text:
                print(f"✅ {config['name']} works!")
                return config['name']
            else:
                print(f"❌ {config['name']} responded but no text")
        except Exception as e:
            print(f"❌ {config['name']} failed: {e}")
    
    return None

if __name__ == "__main__":
    working_model = test_models()
    if working_model:
        print(f"\n🎉 Working model found: {working_model}")
    else:
        print("\n❌ No working models found")


