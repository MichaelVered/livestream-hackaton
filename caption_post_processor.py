#!/usr/bin/env python3
"""
Caption Post-Processor for Gemini Live API
Bundles captions into time windows and summarizes them using LLM
"""

import cv2
import base64
import json
import threading
import time
from datetime import datetime, timedelta
import argparse
import os
from typing import List, Dict, Any
import google.generativeai as genai
from config import GEMINI_API_KEY, DEFAULT_CAMERA_INDEX, DEFAULT_FRAME_INTERVAL

class CaptionEntry:
    """Represents a single caption with timestamp"""
    def __init__(self, text: str, timestamp: float):
        self.text = text.strip()
        self.timestamp = timestamp
        self.datetime = datetime.fromtimestamp(timestamp)
    
    def __str__(self):
        return f"[{self.datetime.strftime('%H:%M:%S')}] {self.text}"

class CaptionWindow:
    """Represents a time window of captions"""
    def __init__(self, start_time: float, window_duration: float):
        self.start_time = start_time
        self.end_time = start_time + window_duration
        self.captions: List[CaptionEntry] = []
        self.summary = ""
        self.summarized = False
    
    def add_caption(self, caption: CaptionEntry):
        """Add a caption to this window if it falls within the time range"""
        if self.start_time <= caption.timestamp < self.end_time:
            self.captions.append(caption)
            return True
        return False
    
    def is_complete(self, current_time: float) -> bool:
        """Check if this window is complete (past its end time)"""
        return current_time >= self.end_time
    
    def get_captions_text(self) -> str:
        """Get all captions as a single text string"""
        return "\n".join([str(caption) for caption in self.captions])
    
    def get_timestamp_range(self) -> str:
        """Get human-readable timestamp range for this window"""
        start_dt = datetime.fromtimestamp(self.start_time)
        end_dt = datetime.fromtimestamp(self.end_time)
        return f"{start_dt.strftime('%H:%M:%S')} - {end_dt.strftime('%H:%M:%S')}"

class CaptionPostProcessor:
    """Post-processes captions from Gemini API with time-based bundling and summarization"""
    
    def __init__(self, api_key: str, camera_index: int = 0, window_duration: float = 30.0):
        """
        Initialize the caption post-processor
        
        Args:
            api_key (str): Google AI API key
            camera_index (int): Camera index (0 for default camera)
            window_duration (float): Duration of each caption window in seconds
        """
        self.api_key = api_key
        self.camera_index = camera_index
        self.window_duration = window_duration
        
        # Video capture
        self.cap = None
        self.model = None
        self.running = False
        
        # Caption management
        self.current_window = None
        self.completed_windows = []
        self.latest_description = "Initializing..."
        
        # Frame management
        self.frame_count = 0
        self.last_frame_time = 0
        self.frame_interval = 0.5  # Send frame every 500ms
        
        # Initialize Gemini for both analysis and summarization
        self.initialize_gemini()
    
    def initialize_gemini(self):
        """Initialize Gemini API with correct model names (same as gemini_success.py)"""
        print("Initializing Gemini API...")
        genai.configure(api_key=self.api_key)
        
        # Use the correct model names from the available models list
        model_names = [
            "gemini-2.0-flash",
            "gemini-2.5-flash", 
            "gemini-2.0-flash-exp",
            "gemini-flash-latest",
            "gemini-pro-latest"
        ]
        
        for model_name in model_names:
            try:
                print(f"Trying model: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                
                # Test the model with a simple request
                test_response = self.model.generate_content("Hello")
                if test_response.text:
                    print(f"✅ Gemini API initialized successfully with {model_name}")
                    return True
                else:
                    print(f"❌ Model {model_name} responded but no text")
                    continue
                    
            except Exception as e:
                print(f"❌ Failed to initialize {model_name}: {e}")
                continue
        
        raise Exception("Could not initialize any Gemini model")
    
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
    
    def analyze_frame(self, frame):
        """Analyze a single frame using Gemini API (same as gemini_success.py)"""
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
    
    def complete_current_window(self):
        """Complete the current window and generate summary"""
        if self.current_window is None:
            return
        
        # Only summarize if there are captions
        if self.current_window.captions:
            self.summarize_window(self.current_window)
        else:
            self.current_window.summary = "No captions captured"
            self.current_window.summarized = True
        
        self.completed_windows.append(self.current_window)
    
    def check_window_completion(self):
        """Check if current window should be completed based on time"""
        if self.current_window is None:
            return
        
        current_time = time.time()
        
        if self.current_window.is_complete(current_time):
            self.complete_current_window()
            
            # Start new window
            self.current_window = CaptionWindow(self.current_window.end_time, self.window_duration)
    
    def summarize_window(self, window: CaptionWindow):
        """Summarize a completed caption window using LLM"""
        if not self.model or not window.captions:
            window.summary = "No captions to summarize"
            window.summarized = True
            return
        
        try:
            # Prepare the prompt for summarization
            captions_text = window.get_captions_text()
            prompt = f"""
Analyze the following video captions from a {self.window_duration}-second window and create a declarative summary focused on object movements.

For each object or person in the scene, identify:
1. Initial location/position
2. Movement trajectory (where it moved to)
3. Final location/position
4. Whether it remained stationary

Format the summary as:
"Object started at [initial_location], moved to [final_location]. Object2 began at [initial_location], remained stationary. Object3 started at [initial_location], moved to [intermediate_location], then to [final_location]."

Focus on:
- Object identification (Person, laptop, cup, papers, phone, etc.)
- Clear starting positions
- Movement paths and destinations
- Stationary objects that didn't move
- Spatial relationships and positions

Avoid:
- Colors, lighting, or visual details
- Emotional or subjective descriptions
- Background elements unless they moved
- Static environmental descriptions

Captions from {window.get_timestamp_range()}:
{captions_text}

Provide a declarative summary of object movements:
"""
            
            # Generate summary
            response = self.model.generate_content(prompt)
            window.summary = response.text.strip()
            window.summarized = True
            
            print(f"\n📊 WINDOW SUMMARY [{window.get_timestamp_range()}]:")
            print(f"{window.summary}")
            print(f"({len(window.captions)} captions processed)")
            print("-" * 80)
            
        except Exception as e:
            print(f"❌ Error summarizing window: {e}")
            window.summary = f"Summary error: {str(e)}"
            window.summarized = True
    
    def get_display_text(self) -> str:
        """Get text to display on the video frame"""
        lines = []
        
        # Current caption
        lines.append(f"Current: {self.latest_description}")
        
        # Current window info
        if self.current_window:
            lines.append(f"Window: {self.current_window.get_timestamp_range()}")
            lines.append(f"Captions in window: {len(self.current_window.captions)}")
        
        # Latest summary
        if self.completed_windows:
            latest_summary = self.completed_windows[-1]
            if latest_summary.summarized:
                lines.append(f"Latest Summary: {latest_summary.summary}")
        
        return "\n".join(lines)
    
    def capture_and_display(self):
        """Main video capture and display loop"""
        try:
            width, height, fps = self.initialize_camera()
            
            print(f"\nStarting video capture with {self.window_duration}s caption windows...")
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
                        timestamp = time.time()
                        
                        # Create caption entry and add directly to current window
                        caption = CaptionEntry(description, timestamp)
                        self.latest_description = description
                        
                        # Initialize first window if needed
                        if self.current_window is None:
                            self.current_window = CaptionWindow(timestamp, self.window_duration)
                        
                        # Add caption to current window
                        self.current_window.add_caption(caption)
                    
                    analysis_thread = threading.Thread(target=analyze)
                    analysis_thread.start()
                    self.last_frame_time = current_time
                    self.frame_count += 1
                
                # Check if current window should be completed (every frame)
                self.check_window_completion()
                
                # Display frame with information overlay
                display_frame = frame.copy()
                
                # Add text overlay with background
                display_text = self.get_display_text()
                description_lines = display_text.split('\n')
                y_offset = 30
                
                for i, line in enumerate(description_lines[:8]):  # Show first 8 lines
                    if line.strip():
                        # Add background rectangle for better text visibility
                        text_size = cv2.getTextSize(line.strip(), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        cv2.rectangle(display_frame, (5, y_offset - 20), (text_size[0] + 10, y_offset + 5), (0, 0, 0), -1)
                        cv2.putText(display_frame, line.strip(), (10, y_offset), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        y_offset += 25
                
                # Add status info
                status_text = f"Frames: {self.frame_count} | Windows: {len(self.completed_windows)} | FPS: {fps}"
                cv2.putText(display_frame, status_text, (10, height - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow('Caption Post-Processor', display_frame)
                
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
    
    def print_summary_report(self):
        """Print a summary report of all completed windows"""
        if not self.completed_windows:
            print("No completed windows to report")
            return
        
        print("\n" + "="*80)
        print("CAPTION SUMMARY REPORT")
        print("="*80)
        
        for i, window in enumerate(self.completed_windows, 1):
            print(f"\nWindow {i}: {window.get_timestamp_range()}")
            print(f"Captions: {len(window.captions)}")
            if window.summarized:
                print(f"Summary: {window.summary}")
            else:
                print("Summary: Not available")
            print("-" * 40)
    
    def run(self):
        """Main run method"""
        self.running = True
        self.capture_and_display()
        
        # Process any remaining captions
        self.process_captions()
        
        # Summarize current window if it has content
        if self.current_window and self.current_window.captions:
            self.summarize_window(self.current_window)
            self.completed_windows.append(self.current_window)
        
        # Print final report
        self.print_summary_report()

def main():
    parser = argparse.ArgumentParser(description='Caption Post-Processor for Gemini Live API')
    parser.add_argument('--api-key', help='Google AI API key (overrides .env file)')
    parser.add_argument('--camera', type=int, help='Camera index (overrides .env file)')
    parser.add_argument('--window-duration', type=float, default=30.0, 
                       help='Duration of each caption window in seconds (default: 30)')
    parser.add_argument('--interval', type=float, help='Frame send interval in seconds (overrides .env file)')
    
    args = parser.parse_args()
    
    # Use command line args or fall back to .env config
    api_key = args.api_key or GEMINI_API_KEY
    camera_index = args.camera if args.camera is not None else DEFAULT_CAMERA_INDEX
    frame_interval = args.interval if args.interval is not None else DEFAULT_FRAME_INTERVAL
    window_duration = args.window_duration
    
    # Check if API key is set
    if api_key == "YOUR_API_KEY_HERE":
        print("❌ Please set your Gemini API key in the .env file or use --api-key")
        print("Create a .env file with: GEMINI_API_KEY=your_actual_api_key_here")
        print("Or get your API key from: https://aistudio.google.com/app/apikey")
        return
    
    # Create post-processor instance
    processor = CaptionPostProcessor(api_key, camera_index, window_duration)
    processor.frame_interval = frame_interval
    
    print("Caption Post-Processor for Gemini Live API")
    print("=" * 60)
    print(f"Camera: {camera_index}")
    print(f"Window duration: {window_duration}s")
    print(f"Frame interval: {frame_interval}s")
    print("=" * 60)
    
    # Run the post-processor
    try:
        processor.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
