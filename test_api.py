#!/usr/bin/env python3
"""
Comprehensive test script for Smart Mirrors System.
Tests authentication, reports, camera uploads, and admin endpoints.
"""
import requests
import os
import time
from datetime import datetime
from pathlib import Path

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
CAMERA_API_KEY = os.getenv("CAMERA_API_KEY", "changeme_camera_api_key")
SYSTEM_USERNAME = os.getenv("SYSTEM_USER_USERNAME", "admin")
SYSTEM_PASSWORD = os.getenv("SYSTEM_USER_PASSWORD", "admin123")

# Test images directory
TEST_IMAGES_DIR = Path(__file__).parent / "tests-images"

# Global token for authenticated requests
auth_token = None


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_health():
    """Check API health."""
    url = f"{API_BASE_URL}/health"
    print("\n🏥 Checking API health...")
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        result = response.json()
        print(f"✅ API is healthy!")
        print(f"   Status: {result.get('status')}")
        print(f"   Database: {result.get('database')}")
        print(f"   CompreFace: {result.get('compreface')}")
        if result.get('stats'):
            stats = result.get('stats')
            print(f"   Total Images: {stats.get('total_images', 0)}")
            print(f"   Total Cameras: {stats.get('total_cameras', 0)}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


def login(username=None, password=None):
    """Login and get JWT token."""
    global auth_token
    url = f"{API_BASE_URL}/api/auth/login"
    
    username = username or SYSTEM_USERNAME
    password = password or SYSTEM_PASSWORD
    
    print(f"\n🔐 Logging in as {username}...")
    
    try:
        response = requests.post(
            url,
            data={"username": username, "password": password},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        auth_token = result.get("access_token")
        print(f"✅ Login successful!")
        print(f"   Token: {auth_token[:20]}...")
        return auth_token
    except requests.exceptions.RequestException as e:
        print(f"❌ Login failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def get_auth_headers():
    """Get headers with authentication token."""
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}


def create_missing_report(child_photo_path, reporter_name="Test Reporter", 
                         reporter_email="test@example.com", 
                         reporter_phone="+966501234567",
                         child_name="Test Child"):
    """Create a missing child report."""
    url = f"{API_BASE_URL}/api/reports/create"
    
    print(f"\n📝 Creating missing report...")
    print(f"   Reporter: {reporter_name}")
    print(f"   Child: {child_name}")
    
    if not child_photo_path.exists():
        print(f"❌ Image not found: {child_photo_path}")
        return None
    
    try:
        with open(child_photo_path, "rb") as f:
            files = {
                "child_photo": (child_photo_path.name, f, "image/png")
            }
            data = {
                "reporter_name": reporter_name,
                "reporter_email": reporter_email,
                "reporter_phone": reporter_phone,
                "child_name": child_name
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Report created successfully!")
            print(f"   Report Number: {result.get('report_number')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Report ID: {result.get('id')}")
            return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Report creation failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def track_report(phone, report_number):
    """Track a report by phone and report number."""
    url = f"{API_BASE_URL}/api/reports/track"
    
    print(f"\n🔍 Tracking report {report_number}...")
    
    try:
        response = requests.post(
            url,
            json={"phone": phone, "report_number": report_number},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Report found!")
        report = result.get("report", {})
        print(f"   Status: {report.get('status')}")
        print(f"   Child: {report.get('child_name')}")
        
        matches = result.get("matches", [])
        print(f"   Matches: {len(matches)}")
        for i, match in enumerate(matches[:3], 1):
            print(f"   Match {i}: Similarity {match.get('similarity_score', 0):.2%} at {match.get('matched_at')}")
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Track failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def upload_camera_image(image_path, camera_id, camera_name=None, 
                       latitude=None, longitude=None, 
                       place_name=None, description=None):
    """Upload an image from camera with location data."""
    url = f"{API_BASE_URL}/api/upload_camera_face"
    
    headers = {
        "X-API-KEY": CAMERA_API_KEY
    }
    
    print(f"\n📤 Uploading image from camera {camera_id}...")
    if latitude and longitude:
        print(f"   Location: {latitude}, {longitude}")
    if place_name:
        print(f"   Place: {place_name}")
    
    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return None
    
    try:
        with open(image_path, "rb") as f:
            files = {
                "image": (image_path.name, f, "image/png")
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
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Upload successful!")
            print(f"   Camera ID: {result.get('camera_id')}")
            print(f"   Timestamp: {result.get('timestamp')}")
            return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def get_all_reports(page=1, page_size=20, status_filter=None):
    """Get all reports (admin only)."""
    url = f"{API_BASE_URL}/api/admin/reports"
    
    print(f"\n📋 Getting all reports (page {page})...")
    
    params = {"page": page, "page_size": page_size}
    if status_filter:
        params["status_filter"] = status_filter
    
    try:
        response = requests.get(
            url,
            headers=get_auth_headers(),
            params=params,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Retrieved reports!")
        print(f"   Total: {result.get('total', 0)}")
        print(f"   Page: {result.get('page')}/{result.get('total_pages')}")
        
        items = result.get("items", [])
        for i, report in enumerate(items[:5], 1):
            print(f"   {i}. {report.get('report_number')} - {report.get('child_name')} ({report.get('status')})")
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Get reports failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def update_report_status(report_id, new_status):
    """Update report status (admin only)."""
    url = f"{API_BASE_URL}/api/admin/reports/{report_id}/status"
    
    print(f"\n🔄 Updating report {report_id} status to {new_status}...")
    
    try:
        response = requests.put(
            url,
            headers=get_auth_headers(),
            json={"status": new_status},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Status updated!")
        print(f"   Report: {result.get('report_number')}")
        print(f"   New Status: {result.get('status')}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Update failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def get_report_matches(report_id):
    """Get matches for a report (admin only)."""
    url = f"{API_BASE_URL}/api/admin/reports/{report_id}/matches"
    
    print(f"\n🔗 Getting matches for report {report_id}...")
    
    try:
        response = requests.get(
            url,
            headers=get_auth_headers(),
            timeout=10
        )
        response.raise_for_status()
        matches = response.json()
        
        print(f"✅ Found {len(matches)} match(es)")
        for i, match in enumerate(matches[:3], 1):
            print(f"   {i}. Similarity: {match.get('similarity_score', 0):.2%}")
            print(f"      Camera: {match.get('camera_id')}")
            print(f"      Matched at: {match.get('matched_at')}")
        
        return matches
    except requests.exceptions.RequestException as e:
        print(f"❌ Get matches failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def get_saved_images(page=1, page_size=10):
    """Get saved images (admin only)."""
    url = f"{API_BASE_URL}/api/saved_images"
    
    print(f"\n🖼️  Getting saved images (page {page})...")
    
    try:
        response = requests.get(
            url,
            headers=get_auth_headers(),
            params={"page": page, "page_size": page_size},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Retrieved images!")
        print(f"   Total: {result.get('total', 0)}")
        print(f"   Page: {result.get('page')}/{result.get('total_pages')}")
        
        items = result.get("items", [])
        for i, img in enumerate(items[:3], 1):
            print(f"   {i}. Camera: {img.get('camera_id')} at {img.get('timestamp')}")
        
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Get images failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def main():
    """Run comprehensive test scenario."""
    print_section("🧪 Smart Mirrors System - Comprehensive Test")
    
    # Step 1: Health Check
    print_section("STEP 1: Health Check")
    if not check_health():
        print("\n⚠️  API is not healthy. Please check if services are running.")
        print("   Run: docker-compose up")
        return
    
    # Step 2: Authentication
    print_section("STEP 2: Authentication")
    if not login():
        print("\n⚠️  Login failed. Cannot proceed with admin tests.")
        print("   Make sure default system user is created.")
        return
    
    # Step 3: Create Missing Report
    print_section("STEP 3: Create Missing Report")
    child_image = TEST_IMAGES_DIR / "2.png"
    if not child_image.exists():
        child_image = Path(__file__).parent / "tests-images" / "2.png"
    
    if not child_image.exists():
        print(f"⚠️  Child image not found. Skipping report creation.")
        report_data = None
    else:
        report_data = create_missing_report(
            child_image,
            reporter_name="أحمد محمد",
            reporter_email="ahmed@example.com",
            reporter_phone="+966501234567",
            child_name="محمد أحمد"
        )
    
    if not report_data:
        print("⚠️  Report creation failed. Some tests will be skipped.")
        report_number = None
        reporter_phone = None
    else:
        report_number = report_data.get("report_number")
        reporter_phone = "+966501234567"
        
        # Wait for face indexing
        print("\n⏳ Waiting 3 seconds for face indexing...")
        time.sleep(3)
    
    # Step 4: Track Report
    print_section("STEP 4: Track Report")
    if report_number and reporter_phone:
        track_report(reporter_phone, report_number)
    else:
        print("⚠️  Skipping track test (no report created)")
    
    # Step 5: Upload Camera Image with Location
    print_section("STEP 5: Upload Camera Image with Location")
    camera_image = TEST_IMAGES_DIR / "1.png"
    if not camera_image.exists():
        camera_image = Path(__file__).parent / "tests-images" / "1.png"
    
    if camera_image.exists():
        upload_camera_image(
            camera_image,
            camera_id="mall_cam_01",
            camera_name="Mall Entrance Camera",
            latitude=24.7136,
            longitude=46.6753,
            place_name="Riyadh Park Mall",
            description="Main entrance camera - North side"
        )
        
        # Wait for processing
        print("\n⏳ Waiting 5 seconds for image processing and comparison...")
        time.sleep(5)
    else:
        print("⚠️  Camera image not found. Skipping upload.")
    
    # Step 6: Admin - Get All Reports
    print_section("STEP 6: Admin - Get All Reports")
    reports_result = get_all_reports(page=1, page_size=10)
    
    # Step 7: Admin - Update Report Status
    print_section("STEP 7: Admin - Update Report Status")
    if report_data:
        report_id = report_data.get("id")
        # First update to in_progress
        update_report_status(report_id, "in_progress")
        time.sleep(1)
        # Then update to resolved
        update_report_status(report_id, "resolved")
    else:
        print("⚠️  Skipping status update (no report created)")
    
    # Step 8: Admin - Get Report Matches
    print_section("STEP 8: Admin - Get Report Matches")
    if report_data:
        report_id = report_data.get("id")
        get_report_matches(report_id)
    else:
        print("⚠️  Skipping matches (no report created)")
    
    # Step 9: Admin - Get Saved Images
    print_section("STEP 9: Admin - Get Saved Images")
    get_saved_images(page=1, page_size=5)
    
    # Step 10: Track Report Again (After Updates)
    print_section("STEP 10: Track Report Again (After Updates)")
    if report_number and reporter_phone:
        track_report(reporter_phone, report_number)
    else:
        print("⚠️  Skipping track test (no report created)")
    
    # Summary
    print_section("✨ Test Summary")
    print("✅ All test scenarios completed!")
    if report_number:
        print(f"📋 Test Report Number: {report_number}")
        print(f"   You can track this report using:")
        print(f"   Phone: {reporter_phone}")
        print(f"   Report Number: {report_number}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
