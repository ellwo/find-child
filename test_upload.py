#!/usr/bin/env python3
"""
Test script to simulate ESP32-CAM uploads and test search API.
"""
import requests
import os
from datetime import datetime
from pathlib import Path

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://ai-mirrors.socialaipilot.com")
CAMERA_API_KEY = os.getenv("CAMERA_API_KEY", "changeme_camera_api_key")

# Test images directory
TEST_IMAGES_DIR = Path(__file__).parent / "tests-images"


def upload_image(
    image_path: Path, 
    camera_id: str, 
    camera_name: str = None,
    latitude: float = None,
    longitude: float = None,
    place_name: str = None,
    description: str = None
):
    """Upload an image simulating ESP32-CAM upload with location data."""
    url = f"{API_BASE_URL}/api/upload_camera_face"
    
    headers = {
        "X-API-KEY": CAMERA_API_KEY
    }
    
    # Prepare form data
    files = {
        "image": (image_path.name, open(image_path, "rb"), "image/png")
    }
    
    data = {
        "camera_id": camera_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if camera_name:
        data["camera_name"] = camera_name
    
    if latitude is not None:
        data["latitude"] = str(latitude)
    
    if longitude is not None:
        data["longitude"] = str(longitude)
    
    if place_name:
        data["place_name"] = place_name
    
    if description:
        data["description"] = description
    
    print(f"\n📤 Uploading {image_path.name} as {camera_id}...")
    print(f"   URL: {url}")
    print(f"   Camera ID: {camera_id}")
    if camera_name:
        print(f"   Camera Name: {camera_name}")
    if latitude is not None and longitude is not None:
        print(f"   Location: ({latitude}, {longitude})")
    if place_name:
        print(f"   Place: {place_name}")
    if description:
        print(f"   Description: {description}")
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Image ID: {result.get('id')}")
        print(f"   Image URL: {result.get('image_url')}")
        print(f"   CompreFace Face ID: {result.get('compreface_face_id', 'None')}")
        print(f"   Timestamp: {result.get('timestamp')}")
        if result.get('latitude') is not None:
            print(f"   Latitude: {result.get('latitude')}")
        if result.get('longitude') is not None:
            print(f"   Longitude: {result.get('longitude')}")
        if result.get('place_name'):
            print(f"   Place Name: {result.get('place_name')}")
        if result.get('description'):
            print(f"   Description: {result.get('description')}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None
    finally:
        files["image"][1].close()


def search_by_image(query_image_path: Path, threshold: float = 0.7, limit: int = 50):
    """Search for similar faces using a query image."""
    url = f"{API_BASE_URL}/api/search_by_image"
    
    files = {
        "image": (query_image_path.name, open(query_image_path, "rb"), "image/png")
    }
    
    data = {
        "threshold": threshold,
        "limit": limit
    }
    
    print(f"\n🔍 Searching for faces similar to {query_image_path.name}...")
    print(f"   URL: {url}")
    print(f"   Threshold: {threshold}")
    print(f"   Limit: {limit}")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Search successful!")
        print(f"   Total matches: {result.get('total', 0)}")
        
        results = result.get("results", [])
        if results:
            print(f"\n   Top matches:")
            for i, match in enumerate(results[:5], 1):
                print(f"   {i}. Similarity: {match.get('similarity', 0):.4f}")
                print(f"      Camera: {match.get('camera_id')} ({match.get('camera_name', 'N/A')})")
                print(f"      Timestamp: {match.get('timestamp')}")
                print(f"      Image URL: {match.get('image_url')}")
        else:
            print("   No matches found.")
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Search failed: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None
    finally:
        files["image"][1].close()


def check_health():
    """Check API health."""
    url = f"{API_BASE_URL}/health"
    print(f"\n🏥 Checking API health...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        result = response.json()
        print(f"✅ API is healthy!")
        print(f"   Status: {result.get('status')}")
        print(f"   Database: {result.get('database')}")
        print(f"   CompreFace: {result.get('compreface')}")
        if result.get('stats'):
            print(f"   Stats: {result.get('stats')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("🧪 Testing Face Recognition API")
    print("=" * 60)
    
    # Check health first
    if not check_health():
        print("\n⚠️  API is not healthy. Please check if services are running.")
        print("   Run: docker-compose up")
        return
    
    # Test images to upload with location data
    test_images = [
        {
            "path": "tests-images/2.png",
            "camera_id": "test_cam_01",
            "camera_name": "Test Camera 01",
            "latitude": 24.7136,
            "longitude": 46.6753,
            "place_name": "Riyadh Park Mall",
            "description": "Main entrance camera - Test upload"
        },
        {
            "path": "tests-images/3.png",
            "camera_id": "test_cam_02",
            "camera_name": "Test Camera 02",
            "latitude": 24.7136,
            "longitude": 46.6753,
            "place_name": "Riyadh Park Mall",
            "description": "Secondary camera - Test upload"
        },
    ]
    
    print("\n" + "=" * 60)
    print("📤 STEP 1: Uploading test images (simulating ESP32-CAM)")
    print("=" * 60)
    
    uploaded_images = []
    for img_config in test_images:
        image_path = Path(__file__).parent / img_config["path"]
        if not image_path.exists():
            print(f"⚠️  Image not found: {image_path}")
            continue
        
        result = upload_image(
            image_path=image_path,
            camera_id=img_config["camera_id"],
            camera_name=img_config.get("camera_name"),
            latitude=img_config.get("latitude"),
            longitude=img_config.get("longitude"),
            place_name=img_config.get("place_name"),
            description=img_config.get("description")
        )
        if result:
            uploaded_images.append(result)
    
    if not uploaded_images:
        print("\n❌ No images were uploaded successfully.")
        return
    
    print(f"\n✅ Successfully uploaded {len(uploaded_images)} image(s)")
    
    print("\n" + "=" * 60)
    print("✨ Upload testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

