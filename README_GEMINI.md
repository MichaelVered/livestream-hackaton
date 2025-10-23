# Gemini Live Video Analysis

This application captures video from your macOS camera and streams it to Google's Gemini Live API for real-time scene analysis and text descriptions.

## Features

- 🎥 **Real-time Video Capture**: Captures video from macOS camera using OpenCV
- 🤖 **AI Analysis**: Streams video frames to Gemini Live API for analysis
- 📝 **Live Text Descriptions**: Displays real-time text descriptions of what Gemini sees
- ⚡ **WebSocket Streaming**: Uses WebSocket for low-latency real-time communication
- 🎛️ **Configurable**: Adjustable frame rate, camera settings, and analysis intervals

## Setup

### 1. Install Dependencies

```bash
# Activate your virtual environment
source /Users/michaelzimmerman/projects/.venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### 3. Configure API Key

Edit `config.py` and replace `YOUR_API_KEY_HERE` with your actual API key:

```python
GEMINI_API_KEY = "your_actual_api_key_here"
```

## Usage

### Quick Test

First, test the Gemini API connection:

```bash
python gemini_simple_test.py
```

### Full Video Analysis

Run the complete video analysis system:

```bash
python gemini_live_integration.py --api-key YOUR_API_KEY
```

### Command Line Options

```bash
python gemini_live_integration.py --help
```

Options:
- `--api-key`: Your Gemini API key (required)
- `--camera`: Camera index (default: 0)
- `--interval`: Frame send interval in seconds (default: 0.5)

### Example Usage

```bash
# Use default camera with 1-second intervals
python gemini_live_integration.py --api-key YOUR_API_KEY --interval 1.0

# Use camera 1 with 0.3-second intervals
python gemini_live_integration.py --api-key YOUR_API_KEY --camera 1 --interval 0.3
```

## How It Works

1. **Camera Initialization**: Opens the macOS camera and configures video settings
2. **WebSocket Connection**: Establishes connection to Gemini Live API
3. **Frame Capture**: Captures video frames at specified intervals
4. **Image Encoding**: Converts frames to JPEG and encodes as base64
5. **API Streaming**: Sends encoded frames to Gemini Live API via WebSocket
6. **Response Processing**: Receives and displays text descriptions from Gemini
7. **Live Display**: Shows video feed with overlaid text descriptions

## Controls

- **'q'** or **ESC**: Quit the application
- The application runs continuously until you quit

## Configuration

Edit `config.py` to customize:

- **API Key**: Your Gemini API key
- **Camera Settings**: Default camera index, resolution, FPS
- **Frame Interval**: How often to send frames to Gemini
- **Display Settings**: Font size, text overlay settings

## Troubleshooting

### Camera Issues
- Ensure camera permissions are granted in System Preferences
- Try different camera indices (0, 1, 2, etc.)
- Check that no other applications are using the camera

### API Issues
- Verify your API key is correct and active
- Check your internet connection
- Ensure you have sufficient API quota

### Performance Issues
- Increase the frame interval (e.g., `--interval 1.0`) to reduce API calls
- Lower the video resolution in `config.py`
- Check your internet connection speed

## File Structure

```
hackaton/
├── gemini_live_integration.py    # Main application
├── gemini_simple_test.py         # API connection test
├── video_capture.py              # Basic video capture
├── video_capture_fixed.py        # Fixed video capture
├── config.py                     # Configuration settings
├── requirements.txt              # Python dependencies
└── recordings/                   # Video recording output
```

## API Limits

- Gemini Live API has rate limits and usage quotas
- Monitor your usage in Google AI Studio
- Consider adjusting frame intervals to stay within limits

## Next Steps

This is Step 2 of the complete application. Future enhancements could include:

- Recording analyzed video with text overlays
- Custom analysis prompts
- Multiple camera support
- Audio integration
- Real-time object detection
- Custom UI for better text display

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your API key and permissions
3. Test with the simple test script first
4. Check the console output for error messages

