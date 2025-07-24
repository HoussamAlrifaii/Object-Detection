from flask import Flask, request, render_template, send_file, send_from_directory, Response, abort, jsonify
import os
from werkzeug.utils import secure_filename
import subprocess
import mimetypes
import cv2
from ultralytics import YOLO
import re
import logging
import time
from datetime import datetime

# Database imports
from database import create_database_config, init_database, get_database_stats
from models import db, ProcessingJob, Detection, SystemStats, ObjectClass

app = Flask(__name__)

# Configure database
db_instance, migrate = create_database_config(app)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
PREDICTED_IMAGES_FOLDER = 'output_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PREDICTED_IMAGES_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize hosted model service
try:
    from hosted_model import HostedObjectDetector
    model = HostedObjectDetector()
    logger.info("✅ Hosted model service initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize hosted model: {e}")
    model = None

def run_prediction(image_path, output_name, job_id=None):
    if model is None:
        logger.error("❌ Hosted model service not loaded")
        return None, None
        
    if not os.path.exists(image_path):
        logger.error(f"❌ File not found: {image_path}")
        return None, None

    try:
        logger.info(f"🔍 Running hosted prediction on: {image_path}")
        start_time = time.time()
        
        # Use the hosted model service
        detection_results = model.detect_objects(image_path)
        
        if detection_results is None:
            logger.error("❌ Hosted prediction returned no results")
            return None, None
        
        # Draw detection boxes on the image
        output_path = os.path.join(PREDICTED_IMAGES_FOLDER, output_name)
        success = model.draw_detections(image_path, detection_results['detections'], output_path)
        
        if not success:
            logger.error(f"❌ Failed to draw detections on image: {output_path}")
            return None, None
        
        # Save detection data to the database
        if job_id:
            with app.app_context():
                for det in detection_results['detections']:
                    detection = Detection(
                        job_id=job_id,
                        class_name=det['class_name'],
                        confidence=det['confidence'],
                        bbox_x1=det['bbox']['x1'],
                        bbox_y1=det['bbox']['y1'],
                        bbox_x2=det['bbox']['x2'],
                        bbox_y2=det['bbox']['y2']
                    )
                    db.session.add(detection)
                    
                    # Update object class stats
                    ObjectClass.update_class_stats(det['class_name'], det['confidence'])
                
                db.session.commit()
        
        processing_time = time.time() - start_time
        detection_results['processing_time'] = processing_time
        
        logger.info(f"✅ Hosted prediction saved to: {output_path} ({detection_results['total_detections']} objects detected)")
        
        return output_path, detection_results
            
    except Exception as e:
        logger.error(f"❌ Error during hosted prediction: {e}")
        if job_id:
            db.session.rollback()
        return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    """Show system status and model info"""
    model_status = "✅ Loaded" if model is not None else "❌ Failed to load"
    
    return f"""
    <h1>🎯 Object Detection System Status</h1>
    <p><strong>Model Status:</strong> {model_status}</p>
    <p><strong>Upload Folder:</strong> {UPLOAD_FOLDER}</p>
    <p><strong>Output Folder:</strong> {OUTPUT_FOLDER}</p>
    <p><strong>Allowed Extensions:</strong> {', '.join(ALLOWED_EXTENSIONS)}</p>
    <p><strong>System:</strong> Ready to process files!</p>
    <br>
    <a href="/demo">🎬 Try Demo</a> | 
    <a href="/dashboard">📈 Dashboard</a> | 
    <a href="/api/stats">📊 API Stats</a> | 
    <a href="/">← Back to Home</a>
    """

@app.route('/demo')
def demo():
    """Create and process a demo image to show the system works"""
    import numpy as np
    
    if model is None:
        return "<h1>❌ Model not loaded - cannot run demo</h1><br><a href='/'>Back to Home</a>"
    
    try:
        # Create a simple test image with shapes
        img = np.zeros((400, 600, 3), dtype=np.uint8)
        
        # Add some colored rectangles and shapes
        cv2.rectangle(img, (50, 50), (150, 150), (255, 100, 100), -1)  # Blue-ish rectangle
        cv2.rectangle(img, (200, 200), (350, 300), (100, 255, 100), -1)  # Green-ish rectangle
        cv2.circle(img, (450, 100), 50, (100, 100, 255), -1)  # Red-ish circle
        cv2.rectangle(img, (300, 50), (500, 120), (255, 255, 100), -1)  # Yellow rectangle
        
        # Save demo image
        demo_input_path = os.path.join(UPLOAD_FOLDER, 'demo_input.jpg')
        cv2.imwrite(demo_input_path, img)
        
        # Run prediction
        demo_output_filename = 'demo_output.jpg'
        output_path, detection_info = run_prediction(demo_input_path, demo_output_filename)
        
        if output_path:
            return f"""
            <h1>🎬 Object Detection Demo Results</h1>
            <h2>Original Image:</h2>
            <img src="/uploads/demo_input.jpg" style="max-width: 500px; border: 1px solid #ccc;">
            
            <h2>Detection Results:</h2>
            <img src="/predicted_images/demo_output.jpg" style="max-width: 500px; border: 1px solid #ccc;">
            
            <br><br>
            <p>✅ <strong>Demo completed successfully!</strong> The model is working properly.</p>
            <a href="/">← Back to Upload Your Own Files</a>
            """
        else:
            return "<h1>❌ Demo failed - model processing error</h1><br><a href='/'>Back to Home</a>"
            
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        return f"<h1>❌ Demo failed: {e}</h1><br><a href='/'>Back to Home</a>"

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        # If someone visits /upload directly, redirect them to the main page
        logger.info("🔄 GET request to /upload, redirecting to home")
        return render_template('index.html')
    
    # Handle POST request (actual file upload)
    logger.info("📤 Upload request received")
    
    if 'file' not in request.files:
        logger.error("❌ No file part in request")
        return render_template('index.html'), 400
        
    file = request.files['file']
    if file.filename == '':
        logger.error("❌ No file selected")
        return "No selected file", 400
        
    if not file or not allowed_file(file.filename):
        logger.error(f"❌ File type not allowed: {file.filename}")
        return "File type not allowed", 400
        
    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        logger.info(f"💾 File saved to: {input_path}")
        
        # Verify file was saved correctly
        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            logger.error(f"❌ File not saved properly: {input_path}")
            return "Error saving file", 500

        # Create database record for this processing job
        ext = filename.rsplit('.', 1)[1].lower()
        file_type = 'image' if ext in {'jpg', 'jpeg', 'png'} else 'video'
        file_size = os.path.getsize(input_path)
        
        # Create processing job record
        job = ProcessingJob(
            filename=filename,
            original_filename=file.filename,
            file_type=file_type,
            file_extension=ext,
            file_size=file_size,
            input_path=input_path,
            status='processing',
            started_at=datetime.utcnow()
        )
        db.session.add(job)
        db.session.commit()
        
        logger.info(f"🏷️ Created job #{job.id} for {filename}")
        
        if ext in {'jpg', 'jpeg', 'png'}:
            # Image detection
            logger.info(f"🖼️ Processing image: {filename}")
            output_filename = 'output_' + filename.rsplit('.', 1)[0] + '.jpg'
            output_path = os.path.join(PREDICTED_IMAGES_FOLDER, output_filename)
            
            # Update job with output details
            job.output_path = output_path
            job.output_filename = output_filename
            db.session.commit()
            
            # Run prediction with database integration
            result_path, detection_info = run_prediction(input_path, output_filename, job.id)
            
            if result_path is None:
                # Update job as failed
                job.status = 'failed'
                job.error_message = 'Model prediction failed'
                job.completed_at = datetime.utcnow()
                db.session.commit()
                
                logger.error("❌ Image prediction failed")
                return "Error processing image - model failed", 500
            
            # Update job as completed
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.processing_time = detection_info['processing_time']
            job.objects_detected = detection_info['total_detections']
            job.set_detection_results(detection_info['detections'])
            db.session.commit()
            
            # Update system statistics
            stats = SystemStats.get_or_create_stats()
            stats.update_stats(job)
            
            logger.info(f"✅ Image processed successfully: {output_filename} (Job #{job.id})")
            return render_template('result_image.html', 
                                 output_filename=output_filename, 
                                 input_filename=filename,
                                 job_id=job.id,
                                 detection_info=detection_info)
        else:
            # Video tracking
            logger.info(f"🎥 Processing video: {filename}")
            output_filename = 'output_' + filename.rsplit('.', 1)[0] + '.mp4'
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            try:
                result = subprocess.run(['python3', 'run_tracking.py', '--input', input_path, '--output', output_path], 
                                      check=True, capture_output=True, text=True)
                logger.info(f"✅ Video processed successfully: {output_filename}")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Video processing failed: {e.stderr}")
                return f"Error processing video: {e.stderr}", 500
            return render_template('result.html', output_filename=output_filename)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in upload: {e}")
        return f"Internal server error: {e}", 500

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

# Database API Routes
@app.route('/api/stats')
def api_stats():
    """Get comprehensive database statistics as JSON"""
    try:
        stats = get_database_stats()
        if stats:
            return jsonify(stats)
        else:
            return jsonify({'error': 'Failed to get statistics'}), 500
    except Exception as e:
        logger.error(f"❌ Error getting API stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs')
@app.route('/api/jobs/<int:limit>')
def api_jobs(limit=20):
    """Get recent processing jobs as JSON"""
    try:
        jobs = ProcessingJob.query.order_by(ProcessingJob.created_at.desc()).limit(limit).all()
        return jsonify([job.to_dict() for job in jobs])
    except Exception as e:
        logger.error(f"❌ Error getting jobs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/job/<int:job_id>')
def api_job_details(job_id):
    """Get detailed information about a specific job"""
    try:
        job = ProcessingJob.query.get_or_404(job_id)
        job_data = job.to_dict()
        
        # Add detection details
        detections = Detection.query.filter_by(job_id=job_id).all()
        job_data['detections_detail'] = [detection.to_dict() for detection in detections]
        
        return jsonify(job_data)
    except Exception as e:
        logger.error(f"❌ Error getting job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/classes')
def api_object_classes():
    """Get object class detection statistics"""
    try:
        classes = ObjectClass.query.order_by(ObjectClass.detection_count.desc()).all()
        return jsonify([obj_class.to_dict() for obj_class in classes])
    except Exception as e:
        logger.error(f"❌ Error getting object classes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Show a comprehensive dashboard with statistics"""
    try:
        stats = get_database_stats()
        if not stats:
            return "<h1>❌ Error loading dashboard data</h1><br><a href='/'>Back to Home</a>"
        
        # Generate HTML dashboard
        dashboard_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Object Detection Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
                .stat-item {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
                .recent-jobs {{ max-height: 400px; overflow-y: auto; }}
                .job-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
                .status-completed {{ color: #28a745; }}
                .status-failed {{ color: #dc3545; }}
                .status-processing {{ color: #ffc107; }}
                .nav {{ margin-bottom: 20px; }}
                .nav a {{ margin-right: 15px; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
                .nav a:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="nav">
                    <a href="/">🏠 Home</a>
                    <a href="/api/stats">📊 API Stats</a>
                    <a href="/api/jobs">📋 Jobs API</a>
                    <a href="/demo">🎬 Demo</a>
                </div>
                
                <h1>📈 Object Detection Dashboard</h1>
                
                <div class="card">
                    <h2>📊 System Statistics</h2>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-number">{stats['system_stats']['total_images_processed']}</div>
                            <div>Images Processed</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{stats['system_stats']['total_videos_processed']}</div>
                            <div>Videos Processed</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{stats['system_stats']['total_objects_detected']}</div>
                            <div>Objects Detected</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{stats['total_jobs']}</div>
                            <div>Total Jobs</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{stats['avg_processing_time']}s</div>
                            <div>Avg Processing Time</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{stats['system_stats']['failed_jobs']}</div>
                            <div>Failed Jobs</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📋 Recent Processing Jobs</h2>
                    <div class="recent-jobs">
        """
        
        for job in stats['recent_jobs'][:10]:
            status_class = f"status-{job['status']}"
            created_time = job['created_at'][:19] if job['created_at'] else 'Unknown'
            dashboard_html += f"""
                        <div class="job-item">
                            <strong>#{job['id']}</strong> - {job['original_filename']} 
                            <span class="{status_class}">({job['status']})</span><br>
                            <small>Type: {job['file_type']} | Objects: {job['objects_detected']} | Created: {created_time}</small>
                        </div>
            """
        
        dashboard_html += """
                    </div>
                </div>
                
                <div class="card">
                    <h2>🏷️ Top Detected Object Classes</h2>
        """
        
        for obj_class in stats['object_classes'][:10]:
            dashboard_html += f"""
                    <div style="padding: 8px; border-bottom: 1px solid #eee;">
                        <strong>{obj_class['class_name']}</strong>: {obj_class['detection_count']} detections 
                        (avg confidence: {obj_class['avg_confidence']})
                    </div>
            """
        
        dashboard_html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return dashboard_html
        
    except Exception as e:
        logger.error(f"❌ Error creating dashboard: {e}")
        return f"<h1>❌ Dashboard Error: {e}</h1><br><a href='/'>Back to Home</a>"

if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        init_database(app)
        logger.info("🗺️ Database initialized for Object Detection app")
    
    app.run(debug=True)
