"""
Celery worker entry point.
Run with: celery -A app.worker_main.celery_app worker --loglevel=info
"""
from app.workers.image_processor import celery_app

if __name__ == '__main__':
    celery_app.start()

