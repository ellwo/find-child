#!/usr/bin/env python3
"""
Test script to simulate ESP32-CAM uploads and test attendance recording.
"""
import requests
import os
import time
from datetime import datetime
from pathlib import Path

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
CAMERA_API_KEY = os.getenv("CAMERA_API_KEY", "changeme_camera_api_key")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@school.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Test images directory
TEST_IMAGES_DIR = Path(__file__).parent / "tests-images"

# Test student info
TEST_STUDENT_ID = 2  # خالد
TEST_CAMERA_ID = "CAM_001"


def upload_image(image_path: Path, camera_id: str, camera_name: str = None):
    """Upload an image simulating ESP32-CAM upload."""
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
    
    print(f"\n📤 Uploading {image_path.name} as {camera_id}...")
    print(f"   URL: {url}")
    print(f"   Camera ID: {camera_id}")
    print(f"   Camera Name: {camera_name}")
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Image ID: {result.get('id')}")
        print(f"   Image URL: {result.get('image_url')}")
        print(f"   CompreFace Face ID: {result.get('compreface_face_id', 'None')}")
        print(f"   Timestamp: {result.get('timestamp')}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload failed: {str(e)}")
        if hasattr(e.response, 'text'):
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


def get_admin_token():
    """Get admin authentication token."""
    url = f"{API_BASE_URL}/api/auth/login"
    print(f"\n🔐 Getting admin token...")
    
    try:
        response = requests.post(
            url,
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=5
        )
        response.raise_for_status()
        result = response.json()
        token = result.get("access_token")
        if token:
            print(f"✅ Admin token obtained")
            return token
        else:
            print(f"❌ No token in response")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get admin token: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return None


def check_attendance(student_id: int, admin_token: str):
    """Check attendance records for a student."""
    url = f"{API_BASE_URL}/api/admin/students/{student_id}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"\n📋 Checking attendance for student ID {student_id}...")
    
    try:
        # Get student info
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        student = response.json()
        
        print(f"✅ Student found: {student.get('name')}")
        print(f"   Bus ID: {student.get('bus_id')}")
        print(f"   Face Image: {student.get('face_image_path', 'None')}")
        print(f"   CompreFace ID: {student.get('compreface_face_id', 'None')}")
        
        # Get attendance history
        attendance_url = f"{API_BASE_URL}/api/parent/students/{student_id}/attendance/history"
        # We need parent token, but let's try admin endpoint if available
        # Or we can check via admin dashboard
        
        # Try to get last attendance via admin API
        # For now, let's just check if student has face_image_path and compreface_face_id
        if student.get('face_image_path') and student.get('compreface_face_id'):
            print(f"✅ Student has face image registered")
            return True
        else:
            print(f"⚠️  Student missing face image or CompreFace ID")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to check attendance: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return False


def main():
    print("=" * 70)
    print("🧪 Testing Face Recognition & Attendance Recording")
    print("=" * 70)
    
    # Check health first
    if not check_health():
        print("\n⚠️  API is not healthy. Please check if services are running.")
        print("   Run: docker-compose up")
        return
    
    # Get admin token
    admin_token = get_admin_token()
    if not admin_token:
        print("\n⚠️  Cannot proceed without admin token.")
        return
    
    # Check student setup first
    print("\n" + "=" * 70)
    print("📋 STEP 0: Checking student setup")
    print("=" * 70)
    student_ready = check_attendance(TEST_STUDENT_ID, admin_token)
    
    if not student_ready:
        print("\n⚠️  Student is not properly set up. Please ensure:")
        print("   1. Student has a face image uploaded")
        print("   2. Student is assigned to Bus ID 1")
        print("   3. Bus ID 1 has Camera ID CAM_001")
        return
    
    # Test images to upload
    test_images = [
        ("tests-images/2.png", TEST_CAMERA_ID, "Bus 1 Camera"),
    ]
    
    print("\n" + "=" * 70)
    print("📤 STEP 1: Uploading test images (simulating ESP32-CAM)")
    print("=" * 70)
    print(f"   Camera ID: {TEST_CAMERA_ID}")
    print(f"   Expected Student: خالد (ID: {TEST_STUDENT_ID})")
    
    uploaded_images = []
    for image_rel_path, camera_id, camera_name in test_images:
        image_path = Path(__file__).parent / image_rel_path
        if not image_path.exists():
            print(f"\n⚠️  Image not found: {image_path}")
            continue
        
        result = upload_image(image_path, camera_id, camera_name)
        if result:
            uploaded_images.append(result)
            print(f"   ⏳ Waiting 2 seconds for processing...")
            time.sleep(2)  # Wait for face detection and recognition
    
    if not uploaded_images:
        print("\n❌ No images were uploaded successfully.")
        return
    
    print(f"\n✅ Successfully uploaded {len(uploaded_images)} image(s)")
    
    # Check attendance after uploads
    print("\n" + "=" * 70)
    print("✅ STEP 2: Checking attendance records")
    print("=" * 70)
    
    # Get student info again to see if attendance was recorded
    url = f"{API_BASE_URL}/api/admin/students/{TEST_STUDENT_ID}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        student = response.json()
        
        print(f"\n📊 Student Info:")
        print(f"   Name: {student.get('name')}")
        print(f"   Bus ID: {student.get('bus_id')}")
        
        # Check attendance via admin API - try different endpoints
        attendance_url = f"{API_BASE_URL}/api/admin/reports/attendance"
        params = {"student_id": TEST_STUDENT_ID}
        
        try:
            att_response = requests.get(attendance_url, headers=headers, params=params, timeout=5)
            if att_response.status_code == 200:
                attendance_data = att_response.json()
                # The endpoint returns a list directly
                if isinstance(attendance_data, list):
                    attendances = attendance_data
                else:
                    attendances = attendance_data.get("attendances", [])
                
                if attendances:
                    print(f"\n✅ Attendance records found: {len(attendances)}")
                    print(f"\n   Latest attendance:")
                    latest = attendances[0]
                    print(f"   - Detected at: {latest.get('detected_at')}")
                    print(f"   - Similarity: {latest.get('similarity_score', 0):.4f}")
                    print(f"   - GPS: ({latest.get('gps_latitude')}, {latest.get('gps_longitude')})")
                    print(f"   - Image: {latest.get('detected_image_path', 'N/A')}")
                    print(f"   - Student ID: {latest.get('student_id')}")
                    print(f"   - Bus ID: {latest.get('bus_id')}")
                else:
                    print(f"\n⚠️  No attendance records found yet.")
                    print(f"   This might mean:")
                    print(f"   1. Face recognition didn't match the student")
                    print(f"   2. Similarity score was below threshold (0.7)")
                    print(f"   3. Processing is still in progress")
                    print(f"   4. Camera is not properly linked to the bus")
            else:
                print(f"\n⚠️  Could not fetch attendance (status: {att_response.status_code})")
        except Exception as e:
            print(f"   ⚠️  Could not check attendance records: {str(e)}")
            print(f"\n💡 Check the API logs above to see if attendance was recorded.")
            print(f"   If you see 'Record attendance' messages, it means the system")
            print(f"   successfully identified the student and recorded attendance.")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to check student: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✨ Testing complete!")
    print("=" * 70)
    print("\n📝 Next steps:")
    print("   1. Check API logs for attendance recording messages")
    print("   2. Check database for new attendance records")
    print("   3. Use parent dashboard to view attendance history")


if __name__ == "__main__":
    main()

