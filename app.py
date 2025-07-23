from flask import Flask, request, render_template, send_file, send_from_directory, Response, abort
import os
from werkzeug.utils import secure_filename
import subprocess
import mimetypes
import cv2
from ultralytics import YOLO
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
PREDICTED_IMAGES_FOLDER = 'output_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PREDICTED_IMAGES_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

model = YOLO("cityscapes_yolo/yolov8s_results/weights/last.pt")

def run_prediction(image_path, output_name):
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return None

    results = model(image_path, save=False)

    for i, r in enumerate(results):
        im_array = r.plot(line_width=1, font_size=0.7)  # Small text
        output_path = os.path.join(PREDICTED_IMAGES_FOLDER, output_name)
        cv2.imwrite(output_path, im_array)
        print(f"✅ Prediction saved to: {output_path}")
        return output_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        ext = filename.rsplit('.', 1)[1].lower()
        if ext in {'jpg', 'jpeg', 'png'}:
            # Image detection
            output_filename = 'output_' + filename.rsplit('.', 1)[0] + '.jpg'
            output_path = run_prediction(input_path, output_filename)
            if output_path is None:
                return "Error processing image", 500
            return render_template('result_image.html', output_filename=output_filename, input_filename=filename)
        else:
            # Video tracking
            output_filename = 'output_' + filename.rsplit('.', 1)[0] + '.mp4'
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            try:
                subprocess.run(['python', 'run_tracking.py', '--input', input_path, '--output', output_path], check=True)
            except subprocess.CalledProcessError as e:
                return f"Error processing file: {e}", 500
            return render_template('result.html', output_filename=output_filename)

    else:
        return "File type not allowed", 400

def get_range(request):
    range_header = request.headers.get('Range', None)
    if range_header:
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = range_match.group(2)
            if end and end.isdigit():
                end = int(end)
            else:
                end = None
            return start, end
    return None, None

@app.route('/static/outputs/<path:filename>')
def static_output_file(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        abort(404)

    file_size = os.path.getsize(file_path)
    start, end = get_range(request)

    if start is None:
        # No range header, send full content
        return send_from_directory(OUTPUT_FOLDER, filename)

    if end is None or end >= file_size:
        end = file_size - 1

    length = end - start + 1

    with open(file_path, 'rb') as f:
        f.seek(start)
        data = f.read(length)

    rv = Response(data, 206, mimetype=mimetypes.guess_type(file_path)[0], direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    return rv

@app.route('/predicted_images/<path:filename>')
def predicted_image_file(filename):
    return send_from_directory(PREDICTED_IMAGES_FOLDER, filename)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
