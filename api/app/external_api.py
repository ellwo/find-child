"""
External API notification utilities.
"""
import os
import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from app import models, crud
from app.db import SessionLocal
from app.utils import get_image_url

load_dotenv()

EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "")
EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY", "")


def notify_external_api(
    report: models.MissingReport,
    captured_image: models.CapturedImage,
    similarity_score: float,
    match_id: int
) -> bool:
    """
    Notify external API about a match.
    
    Args:
        report: The missing report that was matched
        captured_image: The captured image that matched
        similarity_score: The similarity score
        match_id: The report match ID
    
    Returns:
        True if notification was successful, False otherwise
    """
    if not EXTERNAL_API_URL:
        print("Warning: EXTERNAL_API_URL not configured, skipping external API notification")
        return False
    
    try:
        # Prepare the payload
        payload = {
            "report": {
                "report_number": report.report_number,
                "reporter": {
                    "name": report.reporter_name,
                    "email": report.reporter_email,
                    "phone": report.reporter_phone
                },
                "child": {
                    "name": report.child_name,
                    "photo_url": get_image_url(report.child_photo_path)
                }
            },
            "match": {
                "similarity": similarity_score,
                "matched_at": datetime.utcnow().isoformat()
            },
            "camera": {
                "camera_id": captured_image.camera_id,
                "camera_name": captured_image.camera_name,
                "timestamp": captured_image.timestamp.isoformat(),
                "latitude": captured_image.latitude,
                "longitude": captured_image.longitude,
                "place_name": captured_image.place_name,
                "description": captured_image.description
            },
            "image_url": get_image_url(captured_image.file_path)
        }
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json"
        }
        
        if EXTERNAL_API_KEY:
            headers["Authorization"] = f"Bearer {EXTERNAL_API_KEY}"
            # Or if they use API key header:
            # headers["X-API-KEY"] = EXTERNAL_API_KEY
        
        # Make the request
        response = requests.post(
            EXTERNAL_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # Check response
        if response.status_code in [200, 201, 202]:
            # Update match record
            db = SessionLocal()
            try:
                crud.update_report_match_notification(db, match_id, external_api_called=True)
                print(f"Successfully notified external API for match {match_id}")
                return True
            except Exception as e:
                print(f"Error updating match notification status: {str(e)}")
            finally:
                db.close()
            return True
        else:
            print(f"External API returned status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling external API: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error in notify_external_api: {str(e)}")
        return False


