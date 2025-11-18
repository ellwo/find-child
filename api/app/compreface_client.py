"""
CompreFace API client using the official CompreFace Python SDK.
"""
import os
import time
import tempfile
from typing import List, Dict
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from PIL import Image
from compreface import CompreFace
from compreface.service import RecognitionService, VerificationService, DetectionService

load_dotenv()

COMPREFACE_URL = os.getenv("COMPREFACE_URL", "http://compreface-api:8080")
# Separate API keys for different services
COMPREFACE_VERIFICATION_KEY = os.getenv("COMPREFACE_VERIFICATION_KEY", "")
COMPREFACE_RECOGNITION_KEY = os.getenv("COMPREFACE_RECOGNITION_KEY", "")
COMPREFACE_DETECTION_KEY = os.getenv("COMPREFACE_DETECTION_KEY", "")
COMPREFACE_SUBJECT = os.getenv("COMPREFACE_SUBJECT", "faces")

# Initialize CompreFace SDK
# Parse URL to get domain and port
# CompreFace SDK expects domain (with protocol, without port) and port separately
parsed_url = urlparse(COMPREFACE_URL)
compreface_domain = f"{parsed_url.scheme}://{parsed_url.hostname}" if parsed_url.hostname else "http://compreface-api"
compreface_port = str(parsed_url.port) if parsed_url.port else ("443" if parsed_url.scheme == "https" else "8080")

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


def index_face(file_path: str, retries: int = 3) -> str:
    """
    Index a face image in CompreFace using the official SDK.
    
    Args:
        file_path: Path to the image file to index
        retries: Number of retry attempts on transient failures
    
    Returns:
        compreface_face_id: The image_id returned by CompreFace
    
    Raises:
        Exception: If indexing fails after retries
    """
    recognition = _get_recognition_service()
    face_collection = recognition.get_face_collection()
    
    for attempt in range(retries):
        try:
            # Add face to collection using SDK
            result = face_collection.add(image_path=file_path, subject=COMPREFACE_SUBJECT)
            
            # SDK returns a dict with image_id
            image_id = result.get("image_id")
            if image_id:
                return str(image_id)
            else:
                raise ValueError(f"Unexpected CompreFace SDK response format: {result}")
                
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


def detect_face(file_path: str) -> bool:
    """
    Detect if an image contains at least one face using CompreFace Detection Service.
    
    Args:
        file_path: Path to the image file to check
    
    Returns:
        True if at least one face is detected, False otherwise
    
    Raises:
        Exception: If detection fails
    """
    detection = _get_detection_service()
    
    try:
        # Use SDK detect method
        result = detection.detect(image_path=file_path)
        
        # SDK returns: {"result": [{"box": {...}, "landmarks": {...}, ...}, ...]}
        # or {"result": []} if no faces detected
        results = result.get("result", [])
        if not results and isinstance(result, list):
            results = result
        
        # Check if any faces were detected
        return len(results) > 0
        
    except Exception as e:
        raise Exception(f"Failed to detect face: {str(e)}")


def detect_all_faces(file_path: str) -> List[Dict]:
    """
    Detect all faces in an image and return their coordinates.
    
    Args:
        file_path: Path to the image file to check
    
    Returns:
        List of dicts, each containing:
        - "box": {"x_min": int, "y_min": int, "x_max": int, "y_max": int}
        - "confidence": float (if available)
    
    Raises:
        Exception: If detection fails
    """
    detection = _get_detection_service()
    
    try:
        # Use SDK detect method
        result = detection.detect(image_path=file_path)
        
        # SDK returns: {"result": [{"box": {...}, "landmarks": {...}, ...}, ...]}
        # or {"result": []} if no faces detected
        results = result.get("result", [])
        if not results and isinstance(result, list):
            results = result
        
        # Extract face coordinates
        faces = []
        for face_data in results:
            box = face_data.get("box", {})
            if not box:
                continue
            
            # CompreFace may return coordinates in different formats:
            # Format 1: x_min, y_min, x_max, y_max
            # Format 2: x, y, width, height
            x_min = None
            y_min = None
            x_max = None
            y_max = None
            
            if "x_min" in box and "y_min" in box and "x_max" in box and "y_max" in box:
                # Format 1: Direct coordinates
                x_min = int(box.get("x_min", 0))
                y_min = int(box.get("y_min", 0))
                x_max = int(box.get("x_max", 0))
                y_max = int(box.get("y_max", 0))
            elif "x" in box and "y" in box and "width" in box and "height" in box:
                # Format 2: x, y, width, height
                x = int(box.get("x", 0))
                y = int(box.get("y", 0))
                width = int(box.get("width", 0))
                height = int(box.get("height", 0))
                x_min = x
                y_min = y
                x_max = x + width
                y_max = y + height
            else:
                # Try to extract from any available format
                print(f"Warning: Unknown box format: {box}")
                continue
            
            if x_min is not None and y_min is not None and x_max is not None and y_max is not None:
                faces.append({
                    "box": {
                        "x_min": x_min,
                        "y_min": y_min,
                        "x_max": x_max,
                        "y_max": y_max
                    },
                    "confidence": float(box.get("probability", 0.0)) if "probability" in box else None
                })
        
        return faces
        
    except Exception as e:
        raise Exception(f"Failed to detect faces: {str(e)}")


def extract_faces_from_image(image_path: str, faces: List[Dict], output_dir: str = None) -> List[str]:
    """
    Extract individual faces from an image based on detected face coordinates.
    
    Args:
        image_path: Path to the original image
        faces: List of face dictionaries with "box" coordinates
        output_dir: Directory to save extracted faces (default: temp directory)
    
    Returns:
        List of paths to extracted face images
    
    Raises:
        Exception: If extraction fails
    """
    if not faces:
        return []
    
    try:
        # Open the original image
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # Create output directory if not provided
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        extracted_faces = []
        
        for idx, face in enumerate(faces):
            box = face.get("box", {})
            x_min = max(0, box.get("x_min", 0))
            y_min = max(0, box.get("y_min", 0))
            x_max = min(img_width, box.get("x_max", img_width))
            y_max = min(img_height, box.get("y_max", img_height))
            
            # Ensure valid coordinates
            if x_max <= x_min or y_max <= y_min:
                print(f"Warning: Invalid face coordinates for face {idx}, skipping...")
                continue
            
            # Add padding (10% of face size)
            width = x_max - x_min
            height = y_max - y_min
            padding_x = int(width * 0.1)
            padding_y = int(height * 0.1)
            
            x_min = max(0, x_min - padding_x)
            y_min = max(0, y_min - padding_y)
            x_max = min(img_width, x_max + padding_x)
            y_max = min(img_height, y_max + padding_y)
            
            # Crop the face
            face_img = img.crop((x_min, y_min, x_max, y_max))
            
            # Save the cropped face
            base_name = Path(image_path).stem
            output_path = os.path.join(output_dir, f"{base_name}_face_{idx}.jpg")
            face_img.save(output_path, "JPEG", quality=95)
            
            extracted_faces.append(output_path)
            print(f"Extracted face {idx} to {output_path}")
        
        return extracted_faces
        
    except Exception as e:
        raise Exception(f"Failed to extract faces from image: {str(e)}")

