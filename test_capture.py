#!/usr/bin/env python3
"""
Quick test script for video capture
"""

import cv2
import os
import time
from video_capture import VideoCapture

def test_camera():
    """Test camera capture for 5 seconds"""
    print("Testing camera capture...")
    
    # Create video capture instance
    video_capture = VideoCapture()
    
    try:
        # Start recording
        output_file = video_capture.start_recording("test_video.mp4")
        print(f"Recording to: {output_file}")
        
        # Record for 5 seconds
        start_time = time.time()
        while time.time() - start_time < 5:
            frame = video_capture.capture_frame()
            video_capture.record_frame(frame)
            
            # Show frame
            cv2.imshow('Test - Camera Working', frame)
            cv2.waitKey(1)
        
        # Stop recording
        video_capture.stop_recording()
        
        # Give a moment for file to be properly written
        time.sleep(0.5)
        
        print("Test completed successfully!")
        
        # Check if file was created
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"Video file created: {output_file}")
            print(f"File size: {file_size} bytes")
            return True
        else:
            print("Error: Video file was not created")
            return False
            
    except Exception as e:
        print(f"Error during test: {e}")
        return False
    finally:
        video_capture.cleanup()

if __name__ == "__main__":
    success = test_camera()
    if success:
        print("\n✅ Camera test PASSED! Your camera is working correctly.")
    else:
        print("\n❌ Camera test FAILED! Check camera permissions and try again.")
