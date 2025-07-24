#!/usr/bin/env python3
"""
Database configuration and utilities for Object Detection System
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, ProcessingJob, Detection, SystemStats, ObjectClass

def create_database_config(app):
    """Configure database for the Flask app"""
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_path = os.path.join(basedir, 'object_detection.db')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # Initialize database
    db.init_app(app)
    
    # Initialize migration support
    migrate = Migrate(app, db)
    
    return db, migrate

def init_database(app):
    """Initialize database tables and create initial data"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Create initial system stats if they don't exist
            stats = SystemStats.get_or_create_stats()
            
            print("✅ Database initialized successfully")
            print(f"📊 Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            return False

def get_database_stats():
    """Get comprehensive database statistics"""
    try:
        # Get system stats
        system_stats = SystemStats.get_or_create_stats()
        
        # Get recent jobs
        recent_jobs = ProcessingJob.query.order_by(ProcessingJob.created_at.desc()).limit(10).all()
        
        # Get object class stats
        object_classes = ObjectClass.query.order_by(ObjectClass.detection_count.desc()).all()
        
        # Get processing status counts
        status_counts = {}
        for status in ['pending', 'processing', 'completed', 'failed']:
            count = ProcessingJob.query.filter_by(status=status).count()
            status_counts[status] = count
        
        # Calculate average processing time
        completed_jobs = ProcessingJob.query.filter(
            ProcessingJob.status == 'completed',
            ProcessingJob.processing_time.isnot(None)
        ).all()
        
        avg_processing_time = 0
        if completed_jobs:
            total_time = sum(job.processing_time for job in completed_jobs)
            avg_processing_time = total_time / len(completed_jobs)
        
        return {
            'system_stats': system_stats.to_dict(),
            'recent_jobs': [job.to_dict() for job in recent_jobs],
            'object_classes': [obj_class.to_dict() for obj_class in object_classes],
            'status_counts': status_counts,
            'avg_processing_time': round(avg_processing_time, 2),
            'total_jobs': ProcessingJob.query.count()
        }
        
    except Exception as e:
        print(f"❌ Error getting database stats: {e}")
        return None

def cleanup_old_jobs(days_old=30):
    """Clean up old processing jobs and their associated data"""
    from datetime import datetime, timedelta
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find old jobs
        old_jobs = ProcessingJob.query.filter(
            ProcessingJob.created_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for job in old_jobs:
            # Delete associated detections (cascade should handle this)
            db.session.delete(job)
            deleted_count += 1
        
        db.session.commit()
        
        print(f"🧹 Cleaned up {deleted_count} old processing jobs")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Error cleaning up old jobs: {e}")
        db.session.rollback()
        return 0

def export_database_data(output_file=None):
    """Export database data to JSON format"""
    import json
    from datetime import datetime
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"object_detection_export_{timestamp}.json"
    
    try:
        # Get all data
        jobs = ProcessingJob.query.all()
        detections = Detection.query.all()
        system_stats = SystemStats.query.first()
        object_classes = ObjectClass.query.all()
        
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'processing_jobs': [job.to_dict() for job in jobs],
            'detections': [detection.to_dict() for detection in detections],
            'system_stats': system_stats.to_dict() if system_stats else None,
            'object_classes': [obj_class.to_dict() for obj_class in object_classes]
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"📤 Database exported to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error exporting database: {e}")
        return None

def reset_database(app):
    """Reset database - WARNING: This will delete all data"""
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            
            # Recreate all tables
            db.create_all()
            
            # Create initial system stats
            stats = SystemStats()
            db.session.add(stats)
            db.session.commit()
            
            print("⚠️ Database reset completed - all data deleted")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            return False

if __name__ == "__main__":
    # Test database functionality
    from flask import Flask
    
    app = Flask(__name__)
    db_instance, migrate = create_database_config(app)
    
    with app.app_context():
        init_database(app)
        stats = get_database_stats()
        if stats:
            print("📊 Database Stats:")
            print(f"   Total Jobs: {stats['total_jobs']}")
            print(f"   Images Processed: {stats['system_stats']['total_images_processed']}")
            print(f"   Videos Processed: {stats['system_stats']['total_videos_processed']}")
            print(f"   Objects Detected: {stats['system_stats']['total_objects_detected']}")
