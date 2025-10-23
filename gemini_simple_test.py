#!/usr/bin/env python3
"""
Simple test for Gemini Live API integration
Tests the connection and basic functionality
"""

import asyncio
import json
import websockets
import base64
import cv2
import time
from config import GEMINI_API_KEY

async def test_gemini_connection():
    """Test basic connection to Gemini Live API"""
    print("Testing Gemini Live API connection...")
    
    # Test with a simple image
    try:
        # Create a simple test image
        test_image = cv2.imread('test_image.jpg')
        if test_image is None:
            # Create a simple colored rectangle if no test image exists
            import numpy as np
            test_image = np.zeros((480, 640, 3), dtype=np.uint8)
            test_image = cv2.rectangle(test_image, (100, 100), (540, 380), (0, 255, 0), -1)
            cv2.putText(test_image, "TEST IMAGE", (200, 250), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Encode image
        _, buffer = cv2.imencode('.jpg', test_image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Connect to Gemini Live API
        uri = "wss://generativelanguage.googleapis.com/ws/v1beta/models/gemini-2.0-flash-exp:streamGenerateContent"
        
        async with websockets.connect(uri) as websocket:
            print("Connected to Gemini Live API!")
            
            # Send setup message
            setup_message = {
                "setup": {
                    "generationConfig": {
                        "responseModalities": ["TEXT"],
                        "responseMimeType": "text/plain"
                    },
                    "systemInstruction": {
                        "parts": [{
                            "text": "Describe what you see in this image in one sentence."
                        }]
                    }
                }
            }
            
            await websocket.send(json.dumps(setup_message))
            print("Setup message sent")
            
            # Send test image
            message = {
                "realtimeInput": {
                    "mediaChunks": [{
                        "mimeType": "image/jpeg",
                        "data": image_base64
                    }]
                }
            }
            
            await websocket.send(json.dumps(message))
            print("Test image sent")
            
            # Wait for response
            print("Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print("Response received:")
            print(json.dumps(response_data, indent=2))
            
            if "serverContent" in response_data and "text" in response_data["serverContent"]:
                print(f"\nGemini's description: {response_data['serverContent']['text']}")
                return True
            else:
                print("No text response received")
                return False
                
    except Exception as e:
        print(f"Error testing Gemini connection: {e}")
        return False

async def main():
    """Main test function"""
    if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        print("❌ Please set your Gemini API key in config.py")
        print("Get your API key from: https://aistudio.google.com/app/apikey")
        return
    
    print("Gemini Live API Simple Test")
    print("=" * 40)
    
    success = await test_gemini_connection()
    
    if success:
        print("\n✅ Gemini Live API test PASSED!")
        print("You can now run the full video analysis:")
        print("python gemini_live_integration.py --api-key YOUR_API_KEY")
    else:
        print("\n❌ Gemini Live API test FAILED!")
        print("Check your API key and internet connection")

if __name__ == "__main__":
    asyncio.run(main())
