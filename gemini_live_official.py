#!/usr/bin/env python3
"""
Official Gemini Live API Integration using google-generativeai library
Uses the official Google library for real-time video processing.
"""

import cv2
import base64
import json
import asyncio
import threading
import time
from datetime import datetime
import argparse
import os
import google.generativeai as genai
from config import GEMINI_API_KEY, DEFAULT_CAMERA_INDEX, DEFAULT_FRAME_INTERVAL

class GeminiLiveOfficial:
    def __init__(self, api_key, camera_index=0):
        """
        Initialize Gemini Live integration using official library
        
        Args:
            api_key (str): Google AI API key
            camera_index (int): Camera index (0 for default camera)
        """
        self.api_key = api_key
        self.camera_index = camera_index
        self.cap = None
        self.model = None
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
    
    def initialize_gemini(self):
        """Initialize Gemini API"""
        print("Initializing Gemini API...")
        genai.configure(api_key=self.api_key)
        
        # Try different model names
        model_names = [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-1.0-pro",
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro"
        ]
        
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"Gemini API initialized successfully with model: {model_name}")
                return True
            except Exception as e:
                print(f"Failed to initialize with {model_name}: {e}")
                continue
        
        raise Exception("Could not initialize any Gemini model")
    
    def analyze_frame(self, frame):
        """Analyze a single frame using Gemini API"""
        if not self.model:
            return "Gemini not initialized"
        
        try:
            # Resize frame for better performance
            frame_resized = cv2.resize(frame, (640, 360))
            
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
            image_data = buffer.tobytes()
            
            # Create image part for Gemini
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }
            
            # Create prompt
            prompt = "Describe what you see in this image in one concise sentence. Focus on the main objects, people, activities, and environment. Be brief but informative."
            
            # Generate content
            response = self.model.generate_content([prompt, image_part])
            
            if response.text:
                return response.text.strip()
            else:
                return "No description available"
                
        except Exception as e:
            print(f"Error analyzing frame: {e}")
            return f"Analysis error: {str(e)}"
    
    def capture_and_display(self):
        """Main video capture and display loop"""
        try:
            width, height, fps = self.initialize_camera()
            self.initialize_gemini()
            
            print("\nStarting video capture and Gemini analysis...")
            print("Press 'q' to quit")
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame from camera")
                    break
                
                # Analyze frame if enough time has passed
                current_time = time.time()
                if current_time - self.last_frame_time >= self.frame_interval:
                    # Run analysis in a separate thread to avoid blocking
                    def analyze():
                        description = self.analyze_frame(frame)
                        self.latest_description = description
                        print(f"Gemini: {description}")
                    
                    analysis_thread = threading.Thread(target=analyze)
                    analysis_thread.start()
                    self.last_frame_time = current_time
                    self.frame_count += 1
                
                # Display frame with description overlay
                display_frame = frame.copy()
                
                # Add description text overlay with background
                description_lines = self.latest_description.split('\n')
                y_offset = 30
                
                for line in description_lines[:5]:  # Show first 5 lines
                    if line.strip():
                        # Add background rectangle for better text visibility
                        text_size = cv2.getTextSize(line.strip(), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                        cv2.rectangle(display_frame, (5, y_offset - 25), (text_size[0] + 10, y_offset + 5), (0, 0, 0), -1)
                        cv2.putText(display_frame, line.strip(), (10, y_offset), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        y_offset += 30
                
                # Add status info
                status_text = f"Frames analyzed: {self.frame_count} | FPS: {fps}"
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
        cv2.destroyAllWindows()
        print("Cleanup completed")
    
    def run(self):
        """Main run method"""
        self.running = True
        self.capture_and_display()

def main():
    parser = argparse.ArgumentParser(description='Gemini Live Video Analysis (Official Library)')
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
    integration = GeminiLiveOfficial(api_key, camera_index)
    integration.frame_interval = frame_interval
    
    print("Gemini Live Video Analysis (Official Library)")
    print("=" * 50)
    print(f"Camera: {camera_index}")
    print(f"Frame interval: {frame_interval}s")
    print("=" * 50)
    
    # Run the integration
    try:
        integration.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

