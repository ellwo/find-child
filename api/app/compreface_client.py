"""
CompreFace API client using the official CompreFace Python SDK.
"""
import os
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv
from compreface import CompreFace
from compreface.service import RecognitionService, VerificationService

load_dotenv()

COMPREFACE_URL = os.getenv("COMPREFACE_URL", "http://compreface-api:3000")
# Separate API keys for different services
COMPREFACE_VERIFICATION_KEY = os.getenv("COMPREFACE_VERIFICATION_KEY", "")
COMPREFACE_RECOGNITION_KEY = os.getenv("COMPREFACE_RECOGNITION_KEY", "")
COMPREFACE_DETECTION_KEY = os.getenv("COMPREFACE_DETECTION_KEY", "")
# Get subject and ensure it's not empty
COMPREFACE_SUBJECT = os.getenv("COMPREFACE_SUBJECT", "faces").strip()
if not COMPREFACE_SUBJECT:
    COMPREFACE_SUBJECT = "faces"  # Default fallback

# Initialize CompreFace SDK
# Parse URL to get domain and port
# CompreFace SDK expects domain (with protocol, without port) and port separately
parsed_url = urlparse(COMPREFACE_URL)
compreface_domain = f"{parsed_url.scheme}://{parsed_url.hostname}" if parsed_url.hostname else "http://compreface-api"
compreface_port = str(parsed_url.port) if parsed_url.port else ("443" if parsed_url.scheme == "https" else "3000")

# Initialize CompreFace instance
_compreface_instance = None
_recognition_service = None
_verification_service = None
_detection_service = None


def _get_compreface_instance():
    """Get or create CompreFace instance."""
    global _compreface_instance
    if _compreface_instance is None:
        _compreface_instance = CompreFace(compreface_domain, compreface_port)
    return _compreface_instance


def _get_recognition_service():
    """Get or create recognition service."""
    global _recognition_service
    if _recognition_service is None:
        if not COMPREFACE_RECOGNITION_KEY:
            raise ValueError("COMPREFACE_RECOGNITION_KEY not configured")
        compreface = _get_compreface_instance()
        _recognition_service = compreface.init_face_recognition(COMPREFACE_RECOGNITION_KEY)
    return _recognition_service


def _get_verification_service():
    """Get or create verification service."""
    global _verification_service
    if _verification_service is None:
        if not COMPREFACE_VERIFICATION_KEY:
            raise ValueError("COMPREFACE_VERIFICATION_KEY not configured")
        compreface = _get_compreface_instance()
        _verification_service = compreface.init_face_verification(COMPREFACE_VERIFICATION_KEY)
    return _verification_service


def _get_detection_service():
    """Get or create detection service."""
    global _detection_service
    if _detection_service is None:
        if not COMPREFACE_DETECTION_KEY:
            raise ValueError("COMPREFACE_DETECTION_KEY not configured")
        compreface = _get_compreface_instance()
        _detection_service = compreface.init_face_detection(COMPREFACE_DETECTION_KEY)
    return _detection_service


def index_face(file_path: str, subject: Optional[str] = None, retries: int = 3) -> str:
    """
    Index a face image in CompreFace using the official SDK.
    
    Args:
        file_path: Path to the image file to index
        subject: Subject name (optional, defaults to COMPREFACE_SUBJECT)
        retries: Number of retry attempts on transient failures
    
    Returns:
        compreface_face_id: The image_id returned by CompreFace
    
    Raises:
        Exception: If indexing fails after retries
    """
    recognition = _get_recognition_service()
    face_collection = recognition.get_face_collection()
    
    # Use provided subject or fallback to global COMPREFACE_SUBJECT
    subject_name = (subject or COMPREFACE_SUBJECT).strip()
    if not subject_name:
        subject_name = "faces"  # Final fallback
    
    for attempt in range(retries):
        try:
            # Add face to collection using SDK
            result = face_collection.add(image_path=file_path, subject=subject_name)
            
            # SDK returns a dict with image_id
            image_id = result.get("image_id")
            if image_id:
                return str(image_id)
            else:
                # Check if there's an error message
                error_message = result.get("message", "")
                error_code = result.get("code", "")
                if error_message or error_code:
                    raise ValueError(f"CompreFace error (code {error_code}): {error_message}")
                raise ValueError(f"Unexpected CompreFace SDK response format: {result}")
                
        except ValueError as e:
            # Don't retry on ValueError (configuration errors)
            raise Exception(f"Failed to index face: {str(e)}")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
            raise Exception(f"Failed to index face after {retries} attempts: {str(e)}")
    
    raise Exception("Failed to index face: max retries exceeded")


def search_face(query_file_path: str, limit: int = 50) -> List[Dict[str, float]]:
    """
    Search for similar faces in CompreFace using the official SDK.
    
    Args:
        query_file_path: Path to the query image file
        limit: Maximum number of results to return
    
    Returns:
        List of dicts with "face_id" and "score" keys, sorted by score descending
    
    Raises:
        Exception: If search fails
    """
    recognition = _get_recognition_service()
    
    try:
        # Use SDK recognize method
        result = recognition.recognize(image_path=query_file_path)
        
        # SDK returns: {"result": [{"image_id": "...", "similarity": 0.95, "subject": "...", ...}, ...]}
        results = result.get("result", [])
        if not results and isinstance(result, list):
            results = result
        
        # Extract image_id and similarity score
        search_results = []
        for item in results:
            # CompreFace SDK returns image_id and similarity
            image_id = item.get("image_id")
            similarity = item.get("similarity", 0.0)
            
            if image_id:
                search_results.append({
                    "face_id": str(image_id),
                    "score": float(similarity)
                })
        
        # Sort by score descending (already sorted by CompreFace, but ensure)
        search_results.sort(key=lambda x: x["score"], reverse=True)
        return search_results[:limit]
        
    except Exception as e:
        raise Exception(f"Failed to search faces: {str(e)}")


def compare_faces(face1_path: str, face2_path: str) -> float:
    """
    Compare two face images directly using the official SDK (fallback method).
    
    Args:
        face1_path: Path to first face image (source - should contain one face)
        face2_path: Path to second face image (target - can contain multiple faces)
    
    Returns:
        Similarity score (0.0 to 1.0) - returns the highest similarity match
    
    Raises:
        Exception: If comparison fails
    """
    verification = _get_verification_service()
    
    try:
        # Use SDK verify method
        result = verification.verify(source_image_path=face1_path, target_image_path=face2_path)
        
        # SDK returns: {"result": [{"face_matches": [{"similarity": 0.95, ...}, ...], ...}, ...]}
        results = result.get("result", [])
        if not results:
            return 0.0
        
        # Get the highest similarity from all matches
        max_similarity = 0.0
        for item in results:
            face_matches = item.get("face_matches", [])
            for match in face_matches:
                similarity = match.get("similarity", 0.0)
                if similarity > max_similarity:
                    max_similarity = similarity
        
        return float(max_similarity)
        
    except Exception as e:
        raise Exception(f"Failed to compare faces: {str(e)}")


def detect_face(image_path: str) -> bool:
    """
    Detect if an image contains a face using CompreFace Detection Service.
    
    Args:
        image_path: Path to the image file to check
    
    Returns:
        True if face is detected, False otherwise
    
    Raises:
        Exception: If detection fails
    """
    detection = _get_detection_service()
    
    try:
        # Use SDK detect method
        result = detection.detect(image_path=image_path)
        
        # SDK returns: {"result": [{"box": {...}, "subjects": [...], ...}, ...]}
        # If result contains faces, return True
        results = result.get("result", [])
        if not results and isinstance(result, list):
            results = result
        
        # Check if any faces were detected
        return len(results) > 0
        
    except Exception as e:
        # If detection fails, we assume no face (safer than assuming face exists)
        print(f"Warning: Face detection failed: {str(e)}")
        return False

