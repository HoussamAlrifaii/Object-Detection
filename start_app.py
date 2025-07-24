#!/usr/bin/env python3
"""
Enhanced startup script for the Object Detection Flask App
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'flask', 'opencv-python', 'ultralytics', 
        'filterpy', 'werkzeug', 'numpy', 'scipy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, check=True)
            print("✅ All packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please install manually.")
            return False
    else:
        print("✅ All dependencies are installed!")
    
    return True

def check_model():
    """Check if YOLO model is available"""
    print("\n🤖 Checking YOLO model...")
    
    if os.path.exists("yolov8s.pt"):
        print("✅ YOLO model found!")
        return True
    else:
        print("⚠️ YOLO model not found. It will be downloaded automatically on first use.")
        return True

def check_directories():
    """Ensure required directories exist"""
    print("\n📁 Checking directories...")
    
    directories = ['uploads', 'outputs', 'output_images', 'templates', 'static']
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ {directory}/")
        else:
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created {directory}/")
    
    return True

def start_app():
    """Start the Flask application"""
    print("\n🚀 Starting Object Detection App...")
    print("="*50)
    print("🌐 The app will be available at: http://127.0.0.1:5000")
    print("📤 Upload images (jpg, jpeg, png) or videos (mp4, avi, mov, mkv)")
    print("🔍 The app will detect objects and return processed results")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*50)
    
    try:
        # Import and run the app
        from app import app
        app.run(debug=True, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Object Detection App stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting app: {e}")
        sys.exit(1)

def main():
    print("🎯 Object Detection App Launcher")
    print("="*50)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ app.py not found. Please run this script from the Object-Detection directory.")
        sys.exit(1)
    
    # Run all checks
    if not check_dependencies():
        sys.exit(1)
    
    if not check_model():
        sys.exit(1)
    
    if not check_directories():
        sys.exit(1)
    
    print("\n✅ All checks passed!")
    time.sleep(1)
    
    # Start the application
    start_app()

if __name__ == "__main__":
    main()
