#!/usr/bin/env python3
"""
Correct Gemini Live API Integration for Real-time Video Analysis
Uses the actual Gemini Live API WebSocket for real-time video processing.
"""

import cv2
import base64
import json
import asyncio
import websockets
import threading
import time
from datetime import datetime
import argparse
import os
from config import GEMINI_API_KEY, DEFAULT_CAMERA_INDEX, DEFAULT_FRAME_INTERVAL

class GeminiLiveCorrect:
    def __init__(self, api_key, camera_index=0):
        """
        Initialize Gemini Live integration
        
        Args:
            api_key (str): Google AI API key
            camera_index (int): Camera index (0 for default camera)
        """
        self.api_key = api_key
        self.camera_index = camera_index
        self.cap = None
        self.websocket = None
        self.running = False
        self.latest_description = "Initializing..."
        self.frame_count = 0
        self.last_frame_time = 0
        self.frame_interval = 0.5  # Send frame every 500ms
        
    def initialize_camera(self):
        """Initialize the camera capture"""
        print(f"Initializing camera {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise Exception(f"Error: Could not open camera {self.camera_index}")
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        print(f"Camera initialized: {width}x{height} @ {fps}fps")
        return width, height, fps
    
    async def connect_to_gemini(self):
        """Connect to Gemini Live API via WebSocket"""
        # Correct WebSocket URL for Gemini Live API
        uri = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService/BidiGenerateContent?key={self.api_key}"
        
        try:
            print("Connecting to Gemini Live API...")
            self.websocket = await websockets.connect(uri)
            
            # Send setup message
            setup_message = {
                "setup": {
                    "model": "models/gemini-2.0-flash-exp",
                    "generationConfig": {
                        "responseModalities": ["TEXT"],
                        "responseMimeType": "text/plain"
                    },
                    "systemInstruction": {
                        "parts": [{
                            "text": "You are a real-time video analysis assistant. Describe what you see in the video frames in a concise, informative way. Focus on the main objects, people, activities, and environment. Keep descriptions brief but detailed enough to be useful. Respond with just the description, no additional text."
                        }]
                    }
                }
            }
            
            await self.websocket.send(json.dumps(setup_message))
            print("Connected to Gemini Live API successfully!")
            return True
            
        except Exception as e:
            print(f"Error connecting to Gemini Live API: {e}")
            return False
    
    async def send_video_frame(self, frame):
        """Send a video frame to Gemini Live API"""
        if not self.websocket:
            return
        
        try:
            # Resize frame for better performance
            frame_resized = cv2.resize(frame, (640, 360))
            
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Create message for Gemini Live API
            message = {
                "realtimeInput": {
                    "mediaChunks": [{
                        "mimeType": "image/jpeg",
                        "data": frame_base64
                    }]
                }
            }
            
            await self.websocket.send(json.dumps(message))
            self.frame_count += 1
            
        except Exception as e:
            print(f"Error sending frame: {e}")
    
    async def listen_for_responses(self):
        """Listen for responses from Gemini Live API"""
        try:
            while self.running and self.websocket:
                response = await self.websocket.recv()
                response_data = json.loads(response)
                
                # Extract text description
                if "serverContent" in response_data:
                    if "text" in response_data["serverContent"]:
                        self.latest_description = response_data["serverContent"]["text"]
                        print(f"Gemini: {self.latest_description}")
                
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"Error receiving response: {e}")
    
    def capture_and_display(self):
        """Main video capture and display loop"""
        try:
            width, height, fps = self.initialize_camera()
            
            print("\nStarting video capture and Gemini analysis...")
            print("Press 'q' to quit")
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Send frame to Gemini if enough time has passed
                current_time = time.time()
                if current_time - self.last_frame_time >= self.frame_interval:
                    asyncio.run_coroutine_threadsafe(
                        self.send_video_frame(frame), 
                        asyncio.get_event_loop()
                    )
                    self.last_frame_time = current_time
                
                # Display frame with description overlay
                display_frame = frame.copy()
                
                # Add description text overlay with background
                description_lines = self.latest_description.split('\n')
                y_offset = 30
                
                for i, line in enumerate(description_lines[:5]):  # Show first 5 lines
                    if line.strip():
                        # Add background rectangle for better text visibility
                        text_size = cv2.getTextSize(line.strip(), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                        cv2.rectangle(display_frame, (5, y_offset - 25), (text_size[0] + 10, y_offset + 5), (0, 0, 0), -1)
                        cv2.putText(display_frame, line.strip(), (10, y_offset), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        y_offset += 30
                
                # Add status info
                status_text = f"Frames sent: {self.frame_count} | FPS: {fps}"
                cv2.putText(display_frame, status_text, (10, height - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow('Gemini Live Video Analysis', display_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break
                    
        except Exception as e:
            print(f"Error in video capture: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.running = False
        if self.cap:
            self.cap.release()
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.close(), 
                asyncio.get_event_loop()
            )
        cv2.destroyAllWindows()
        print("Cleanup completed")
    
    async def run(self):
        """Main async run method"""
        # Connect to Gemini
        if not await self.connect_to_gemini():
            return
        
        # Start response listener in background
        self.running = True
        response_task = asyncio.create_task(self.listen_for_responses())
        
        # Start video capture in separate thread
        video_thread = threading.Thread(target=self.capture_and_display)
        video_thread.start()
        
        try:
            # Wait for video thread to complete
            video_thread.join()
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.running = False
            response_task.cancel()
            self.cleanup()

def main():
    parser = argparse.ArgumentParser(description='Gemini Live Video Analysis (Correct Implementation)')
    parser.add_argument('--api-key', help='Google AI API key (overrides .env file)')
    parser.add_argument('--camera', type=int, help='Camera index (overrides .env file)')
    parser.add_argument('--interval', type=float, help='Frame send interval in seconds (overrides .env file)')
    
    args = parser.parse_args()
    
    # Use command line args or fall back to .env config
    api_key = args.api_key or GEMINI_API_KEY
    camera_index = args.camera if args.camera is not None else DEFAULT_CAMERA_INDEX
    frame_interval = args.interval if args.interval is not None else DEFAULT_FRAME_INTERVAL
    
    # Check if API key is set
    if api_key == "YOUR_API_KEY_HERE":
        print("❌ Please set your Gemini API key in the .env file or use --api-key")
        print("Create a .env file with: GEMINI_API_KEY=your_actual_api_key_here")
        print("Or get your API key from: https://aistudio.google.com/app/apikey")
        return
    
    # Create integration instance
    integration = GeminiLiveCorrect(api_key, camera_index)
    integration.frame_interval = frame_interval
    
    print("Gemini Live Video Analysis (Correct Implementation)")
    print("=" * 60)
    print(f"Camera: {camera_index}")
    print(f"Frame interval: {frame_interval}s")
    print("=" * 60)
    
    # Run the integration
    try:
        asyncio.run(integration.run())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

