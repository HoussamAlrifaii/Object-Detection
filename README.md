# AI Object Detection Studio

A modern Flask web application for object detection with a beautiful, professional interface. Features both a simple mock detection version and a full-featured version with database integration and hosted model support.

## Features

### Simple App (simple_app.py)
- **Modern UI**: Beautiful gradient interface with FontAwesome icons
- **Drag & Drop Upload**: Intuitive file upload with visual feedback
- **Mock Detection**: Simulated object detection with bounding boxes
- **Responsive Design**: Works perfectly on desktop and mobile
- **Demo Mode**: Built-in demo with sample detection
- **Statistics**: Processing stats and system information
- **No Dependencies**: Minimal requirements, works out of the box

### Full App (app.py)
- **Real Object Detection**: YOLOv8 or hosted model integration
- **Database Integration**: SQLAlchemy with processing history
- **API Endpoints**: RESTful API for statistics and job management
- **Dashboard**: Administrative interface for monitoring
- **Job Tracking**: Complete processing history with status
- **Hosted Models**: Support for remote inference APIs

## Quick Start

### Option 1: Simple App (Recommended for Demo)

1. **Clone the repository**:
```bash
git clone https://github.com/HoussamAlrifaii/Object-Detection.git
cd Object-Detection
```

2. **Install basic dependencies**:
```bash
pip install flask pillow werkzeug
```

3. **Run the simple app**:
```bash
python3 simple_app.py
```

4. **Open your browser**:
```
http://localhost:5000
```

### Option 2: Full App with Auto-Setup

1. **Clone and navigate**:
```bash
git clone https://github.com/HoussamAlrifaii/Object-Detection.git
cd Object-Detection
```

2. **Run auto-setup script**:
```bash
python3 start_app.py
```

This will automatically:
- Check and install all dependencies
- Set up the database
- Download required models
- Start the Flask server

### Option 3: Manual Full Setup

1. **Install all dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the full app**:
```bash
python3 app.py
```

## File Structure

```
Object-Detection/
├── simple_app.py           # Simple mock detection app
├── app.py                  # Full-featured app with real detection
├── start_app.py            # Auto-setup and launch script
├── database.py             # Database models and utilities
├── hosted_model.py         # Remote model service integration
├── test_functionality.py   # Testing suite
├── requirements.txt        # Python dependencies
├── uploads/               # Uploaded files directory
├── outputs/               # Processed images directory
└── README.md              # This file
```

## Dependencies

### Simple App
- Flask
- Pillow (PIL)
- Werkzeug

### Full App
- All simple app dependencies plus:
- SQLAlchemy
- Flask-Migrate
- OpenCV (cv2)
- Ultralytics YOLOv8
- Requests (for hosted models)

## Usage Instructions

### Simple App Interface
1. **Upload Image**: Drag and drop or click to select an image file
2. **Detect Objects**: Click the "Detect Objects" button
3. **View Results**: See detection results with bounding boxes
4. **Try Demo**: Use the built-in demo with sample detection
5. **Check Stats**: View processing statistics
6. **System Test**: Verify all components are working

### Full App Interface
- All simple app features plus:
- **Database Dashboard**: View processing history
- **API Access**: RESTful endpoints for integration
- **Job Tracking**: Monitor processing status
- **Model Management**: Switch between local and hosted models

## Supported File Formats

- **Images**: JPG, JPEG, PNG, GIF
- **Maximum Size**: 10MB per upload
- **Processing**: Automatic image optimization and bounding box drawing

## Testing

Run the comprehensive test suite:
```bash
python3 test_functionality.py
```

Tests include:
- Model loading verification
- Prediction function testing
- Flask app import testing
- Database connectivity (full app)
- File upload validation

## Configuration

### Environment Variables
- `FLASK_ENV`: Set to 'development' for debug mode
- `DATABASE_URL`: Custom database connection string
- `HUGGINGFACE_API_KEY`: For hosted model integration

### Customization
- **Colors**: Modify CSS gradient and color schemes
- **Detection Logic**: Update mock detection rules in simple_app.py
- **Model Selection**: Change YOLO model in app.py
- **UI Elements**: Customize FontAwesome icons and layout

## Troubleshooting

### Common Issues

1. **Port already in use**:
```bash
# Kill process using port 5000
sudo lsof -t -i tcp:5000 | xargs kill -9
```

2. **Missing dependencies**:
```bash
# Use the auto-setup script
python3 start_app.py
```

3. **Image upload fails**:
- Check file format (JPG, PNG, GIF only)
- Verify file size (under 10MB)
- Ensure uploads/ directory exists

4. **Database errors** (full app):
```bash
# Reset database
rm -f object_detection.db
python3 app.py
```

5. **Model loading issues**:
- Ensure internet connection for model download
- Check available disk space
- Verify Python version compatibility

### Getting Help

- Check the terminal output for detailed error messages
- Run the test suite to identify specific issues
- Review the troubleshooting section above
- Check GitHub issues for known problems

## Development

### Adding New Features
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add comments for complex logic
- Test all changes before committing

## Version History

### v3.0 (Latest)
- Added simple_app.py with modern UI
- Removed all emojis for professional appearance
- Enhanced error handling and validation
- Improved responsive design
- Added comprehensive testing suite

### v2.0
- Database integration with SQLAlchemy
- Hosted model support
- API endpoints for statistics
- Dashboard interface
- Job tracking system

### v1.0
- Basic Flask application
- YOLOv8 integration
- File upload functionality
- Simple detection interface

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests for any improvements.

## License

This project is open source and available under the MIT License.
