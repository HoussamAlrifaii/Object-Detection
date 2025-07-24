# Object Detection System

A minimalist web application for real-time object detection and tracking using YOLOv8.

## Features

- **Image Detection**: Upload images to detect and classify objects with bounding boxes
- **Video Tracking**: Process videos with real-time object tracking and counting
- **Counting System**: Automatic counting of objects crossing designated lines
- **Multi-Class Support**: Detects various object types including vehicles, people, and traffic signs

## Requirements

- Python 3.8+
- Flask
- OpenCV (cv2)
- Ultralytics YOLOv8
- FilterPy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/HoussamAlrifaii/Object-Detection.git
cd Object-Detection
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start (Recommended)
```bash
python3 start_app.py
```
This script will automatically:
- Check and install missing dependencies
- Verify the YOLO model
- Create required directories
- Start the Flask server

### Manual Start
```bash
python3 app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Upload an image or video file through the web interface

4. View the detection results with bounding boxes and labels

## File Structure

```
Object-Detection/
│
├── app.py              # Main Flask application
├── run_tracking.py     # Video tracking module
├── templates/          # HTML templates
│   ├── index.html
│   ├── result.html
│   └── result_image.html
├── static/             # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── uploads/            # Uploaded files (created automatically)
├── outputs/            # Processed videos (created automatically)
└── output_images/      # Processed images (created automatically)
```

## Supported Formats

- **Images**: JPG, JPEG, PNG
- **Videos**: MP4, AVI, MOV, MKV

## Technical Details

- Uses YOLOv8 for object detection
- Implements Kalman filtering for smooth object tracking
- Browser-compatible video codec (H.264/AVC1)
- Responsive design with drag-and-drop file upload

## Troubleshooting

### Common Issues

1. **Model not loading**: The YOLO model (yolov8s.pt) will be downloaded automatically on first use. Ensure you have internet connection.

2. **Dependencies missing**: Use `python3 start_app.py` which automatically checks and installs missing packages.

3. **File upload fails**: Check that your file format is supported (JPG, JPEG, PNG for images; MP4, AVI, MOV, MKV for videos).

4. **Processing errors**: Check the terminal output for detailed error messages and logs.

### Testing

Run the test suite to verify everything is working:
```bash
python3 test_functionality.py
```

## Recent Fixes (v2.0)

- ✅ Fixed duplicate ALLOWED_EXTENSIONS definition
- ✅ Added comprehensive error handling and logging
- ✅ Improved model loading with proper error checking
- ✅ Enhanced file upload validation
- ✅ Added startup script with dependency checking
- ✅ Created test suite for validation
- ✅ Fixed line ending issues (Windows/Unix compatibility)

## License

This project is open source and available under the MIT License.
