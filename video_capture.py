#!/usr/bin/env python3
"""
Video Capture Application for macOS Camera
Captures video from the default camera and records it to a file.
"""

import cv2
import numpy as np
import os
from datetime import datetime
import argparse

class VideoCapture:
    def __init__(self, camera_index=0, output_dir="recordings"):
        """
        Initialize video capture
        
        Args:
            camera_index (int): Camera index (0 for default camera)
            output_dir (str): Directory to save recorded videos
        """
        self.camera_index = camera_index
        self.output_dir = output_dir
        self.cap = None
        self.writer = None
        self.recording = False
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def initialize_camera(self):
        """Initialize the camera capture"""
        print(f"Initializing camera {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise Exception(f"Error: Could not open camera {self.camera_index}")
        
        # Set camera properties for better quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Get actual camera properties
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        print(f"Camera initialized successfully!")
        print(f"Resolution: {width}x{height}")
        print(f"FPS: {fps}")
        
        return width, height, fps
    
    def start_recording(self, filename=None):
        """Start recording video to file"""
        if self.recording:
            print("Already recording!")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_capture_{timestamp}.mp4"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Get camera properties
        width, height, fps = self.initialize_camera()
        
        # Define codec and create VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
        
        if not self.writer.isOpened():
            raise Exception(f"Error: Could not create video file {filepath}")
        
        self.recording = True
        print(f"Started recording to: {filepath}")
        print("Press 'q' to quit, 's' to stop recording")
        
        return filepath
    
    def capture_frame(self):
        """Capture a single frame from camera"""
        if self.cap is None:
            raise Exception("Camera not initialized!")
        
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Error: Could not read frame from camera")
        
        return frame
    
    def record_frame(self, frame):
        """Record a frame to the video file"""
        if self.writer and self.recording:
            self.writer.write(frame)
    
    def stop_recording(self):
        """Stop recording and cleanup"""
        if self.recording:
            self.recording = False
            if self.writer:
                self.writer.release()
                self.writer = None
                print("Recording stopped and saved!")
        else:
            print("No active recording to stop")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_recording()
        if self.cap:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
        print("Cleanup completed")

def main():
    parser = argparse.ArgumentParser(description='Capture video from macOS camera')
    parser.add_argument('--camera', type=int, default=0, help='Camera index (default: 0)')
    parser.add_argument('--output', type=str, default='recordings', help='Output directory (default: recordings)')
    parser.add_argument('--filename', type=str, help='Output filename (optional)')
    
    args = parser.parse_args()
    
    # Create video capture instance
    video_capture = VideoCapture(camera_index=args.camera, output_dir=args.output)
    
    try:
        # Start recording
        output_file = video_capture.start_recording(args.filename)
        
        print(f"\nRecording started! Output file: {output_file}")
        print("Controls:")
        print("  'q' - Quit application")
        print("  's' - Stop recording (but continue preview)")
        print("  'r' - Start new recording")
        print("  'ESC' - Quit application")
        
        while True:
            # Capture frame
            frame = video_capture.capture_frame()
            
            # Record frame if recording
            video_capture.record_frame(frame)
            
            # Display frame with recording status
            status_text = "RECORDING" if video_capture.recording else "PREVIEW"
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Show frame
            cv2.imshow('Video Capture - Press q to quit', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' or ESC
                break
            elif key == ord('s'):  # Stop recording
                video_capture.stop_recording()
            elif key == ord('r'):  # Start new recording
                if not video_capture.recording:
                    video_capture.start_recording()
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        video_capture.cleanup()

if __name__ == "__main__":
    main()
