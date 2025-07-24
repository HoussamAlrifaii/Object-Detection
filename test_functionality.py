#!/usr/bin/env python3
"""
Test script to validate the object detection app functionality
"""
import os
import requests
import cv2
import numpy as np
from ultralytics import YOLO

def test_model_loading():
    """Test if YOLO model loads correctly"""
    print("🧪 Testing YOLO model loading...")
    try:
        model = YOLO("yolov8s.pt")
        print("✅ YOLO model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to load YOLO model: {e}")
        return False

def create_test_image():
    """Create a simple test image"""
    print("🖼️ Creating test image...")
    # Create a simple test image with some shapes
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    
    # Add some colored rectangles (objects to detect)
    cv2.rectangle(img, (50, 50), (150, 150), (255, 0, 0), -1)  # Blue rectangle
    cv2.rectangle(img, (200, 200), (350, 300), (0, 255, 0), -1)  # Green rectangle
    cv2.circle(img, (450, 100), 50, (0, 0, 255), -1)  # Red circle
    
    test_image_path = "test_image.jpg"
    cv2.imwrite(test_image_path, img)
    print(f"✅ Test image created: {test_image_path}")
    return test_image_path

def test_prediction():
    """Test the prediction function"""
    print("🔍 Testing prediction function...")
    
    if not test_model_loading():
        return False
        
    test_image = create_test_image()
    
    try:
        model = YOLO("yolov8s.pt")
        results = model(test_image, save=False)
        
        for r in results:
            im_array = r.plot(line_width=2, font_size=1.0)
            output_path = "test_output.jpg"
            success = cv2.imwrite(output_path, im_array)
            
            if success and os.path.exists(output_path):
                print(f"✅ Prediction test successful: {output_path}")
                return True
            else:
                print("❌ Failed to save prediction output")
                return False
                
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")
        return False

def test_flask_app():
    """Test if Flask app starts without errors"""
    print("🌐 Testing Flask app import...")
    try:
        import app
        print("✅ Flask app imports successfully")
        return True
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False

def main():
    print("🚀 Starting Object Detection App Tests\n")
    
    tests = [
        ("Model Loading", test_model_loading),
        ("Prediction Function", test_prediction),
        ("Flask App Import", test_flask_app)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        result = test_func()
        results.append((test_name, result))
    
    print(f"\n{'='*50}")
    print("TEST RESULTS SUMMARY")
    print('='*50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! The app should work correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
    
    # Cleanup test files
    for file in ["test_image.jpg", "test_output.jpg"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"🧹 Cleaned up: {file}")

if __name__ == "__main__":
    main()
