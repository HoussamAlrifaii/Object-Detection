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
pip install flask opencv-python ultralytics filterpy werkzeug
```

## Usage

1. Start the Flask server:
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

## License

This project is open source and available under the MIT License.
