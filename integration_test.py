#!/usr/bin/env python3
"""
Integration Test Script for Parental Child Tracking System

This script simulates the complete system workflow:
1. Admin login and setup
2. Create system settings
3. Create GPS trackers
4. Create cameras
5. Create buses and associate with trackers/cameras
6. Create parent accounts
7. Create students with face images
8. Simulate GPS location updates
9. Simulate camera face uploads
10. Test WebSocket connections
11. Test parent dashboard APIs
12. Test attendance recording

Usage:
    python tests/integration_test.py
"""

import os
import sys
import json
import time
import requests
import websockets
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from io import BytesIO
from PIL import Image

# Add api directory to path for importing app modules
api_path = Path(__file__).parent / "api"
if api_path.exists():
    sys.path.insert(0, str(api_path))
else:
    # Fallback: try parent directory
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
CAMERA_API_KEY = os.getenv("CAMERA_API_KEY", "changeme_camera_api_key")
GPS_DEVICE_API_KEY = os.getenv("GPS_DEVICE_API_KEY", "changeme_gps_api_key")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@school.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Test data
TEST_SCHOOL_LOCATION = {
    "name": "Test School",
    "address": "123 School Street, Riyadh",
    "latitude": 24.7136,
    "longitude": 46.6753
}

TEST_GPS_TRACKERS = [
    {"device_id": "GPS_TRACKER_001", "name": "Bus 1 GPS Tracker"},
    {"device_id": "GPS_TRACKER_002", "name": "Bus 2 GPS Tracker"},
]

TEST_CAMERAS = [
    {"camera_id": "CAM_001", "name": "Bus 1 Camera"},
    {"camera_id": "CAM_002", "name": "Bus 2 Camera"},
]

TEST_BUSES = [
    {
        "bus_number": "Bus 1",
        "driver_name": "Ahmed Ali",
        "driver_phone": "+966501234567",
        "morning_start": "06:00",
        "morning_end": "11:00",
        "afternoon_start": "12:30",
        "afternoon_end": "16:00",
    },
    {
        "bus_number": "Bus 2",
        "driver_name": "Mohammed Hassan",
        "driver_phone": "+966507654321",
        "morning_start": "06:00",
        "morning_end": "11:00",
        "afternoon_start": "12:30",
        "afternoon_end": "16:00",
    },
]

TEST_PARENTS = [
    {
        "username": "parent1",
        "email": "parent1@example.com",
        "phone": "+966501111111",
        "password": "parent123",
        "full_name": "Parent One"
    },
    {
        "username": "parent2",
        "email": "parent2@example.com",
        "phone": "+966502222222",
        "password": "parent123",
        "full_name": "Parent Two"
    },
]

TEST_STUDENTS = [
    {
        "name": "Khalid",
        "age": 10,
        "gender": "male",
        "home_address": "حي قصر الرياض",
        "home_latitude": 24.7154,
        "home_longitude": 46.6840,
        "parent_index": 0,  # Parent 1 (same parent as Omar)
        "bus_index": 0,  # Bus 1
        "pickup_order": 1,  # First pickup for Bus 1
    },
    {
        "name": "Sara",
        "age": 8,
        "gender": "female",
        "home_address": "حي النرجس",
        "home_latitude": 24.7200,
        "home_longitude": 46.6900,
        "parent_index": 1,  # Parent 2
        "bus_index": 1,  # Bus 2
        "pickup_order": 1,  # First pickup for Bus 2
    },
    {
        "name": "Omar",
        "age": 12,
        "gender": "male",
        "home_address": "حي العليا",
        "home_latitude": 24.7100,
        "home_longitude": 46.6800,
        "parent_index": 0,  # Parent 1 (same parent as Khalid - brothers)
        "bus_index": 0,  # Bus 1 (same bus as Khalid)
        "pickup_order": 2,  # Second pickup for Bus 1 (after Khalid)
    },
]


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_step(step: int, message: str):
    """Print a test step."""
    print(f"\n{Colors.HEADER}[Step {step}]{Colors.ENDC} {Colors.BOLD}{message}{Colors.ENDC}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {message}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗{Colors.ENDC} {message}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ{Colors.ENDC} {message}")


class IntegrationTest:
    """Integration test class."""
    
    def __init__(self):
        self.api_base = API_BASE_URL
        self.admin_token: Optional[str] = None
        self.parent_tokens: Dict[str, str] = {}
        self.created_ids: Dict[str, Any] = {
            "trackers": [],
            "cameras": [],
            "buses": [],
            "parents": [],
            "students": [],
        }
        
    def get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    def test_health_check(self):
        """Test health check endpoint."""
        print_step(1, "Testing Health Check")
        try:
            response = requests.get(f"{self.api_base}/health")
            if response.status_code == 200:
                print_success("Health check passed")
                print_info(f"Response: {response.json()}")
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Health check error: {str(e)}")
            return False
    
    def test_admin_login(self):
        """Test admin login."""
        print_step(2, "Admin Login")
        try:
            response = requests.post(
                f"{self.api_base}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                headers=self.get_headers()
            )
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                print_success("Admin login successful")
                print_info(f"Token: {self.admin_token[:20]}...")
                return True
            else:
                print_error(f"Admin login failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Admin login error: {str(e)}")
            return False
    
    def test_create_system_settings(self):
        """Create system settings."""
        print_step(3, "Creating System Settings")
        try:
            # Get current settings
            response = requests.get(
                f"{self.api_base}/api/admin/settings",
                headers=self.get_headers(self.admin_token)
            )
            
            if response.status_code == 200:
                settings = response.json()
                print_info("System settings already exist, updating...")
                # Update settings
                response = requests.put(
                    f"{self.api_base}/api/admin/settings",
                    json={
                        "school_name": TEST_SCHOOL_LOCATION["name"],
                        "school_address": TEST_SCHOOL_LOCATION["address"],
                        "school_latitude": TEST_SCHOOL_LOCATION["latitude"],
                        "school_longitude": TEST_SCHOOL_LOCATION["longitude"],
                        "default_activity_start_morning": "06:00",
                        "default_activity_end_morning": "10:00",
                        "default_activity_start_afternoon": "12:30",
                        "default_activity_end_afternoon": "15:00",
                        "attendance_interval_minutes": 5,
                        "websocket_enabled": True,
                    },
                    headers=self.get_headers(self.admin_token)
                )
            else:
                # Create new settings
                response = requests.post(
                    f"{self.api_base}/api/admin/settings",
                    json={
                        "school_name": TEST_SCHOOL_LOCATION["name"],
                        "school_address": TEST_SCHOOL_LOCATION["address"],
                        "school_latitude": TEST_SCHOOL_LOCATION["latitude"],
                        "school_longitude": TEST_SCHOOL_LOCATION["longitude"],
                        "default_activity_start_morning": "06:00",
                        "default_activity_end_morning": "10:00",
                        "default_activity_start_afternoon": "12:30",
                        "default_activity_end_afternoon": "15:00",
                        "attendance_interval_minutes": 5,
                        "websocket_enabled": True,
                    },
                    headers=self.get_headers(self.admin_token)
                )
            
            if response.status_code in [200, 201]:
                print_success("System settings created/updated")
                return True
            else:
                print_error(f"Failed to create settings: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Create settings error: {str(e)}")
            return False
    
    def test_create_gps_trackers(self):
        """Create GPS trackers."""
        print_step(4, "Creating GPS Trackers")
        try:
            for tracker_data in TEST_GPS_TRACKERS:
                response = requests.post(
                    f"{self.api_base}/api/admin/trackers",
                    json=tracker_data,
                    headers=self.get_headers(self.admin_token)
                )
                if response.status_code == 201:
                    tracker = response.json()
                    self.created_ids["trackers"].append(tracker)
                    print_success(f"Created tracker: {tracker_data['name']} (ID: {tracker['id']})")
                else:
                    print_error(f"Failed to create tracker {tracker_data['name']}: {response.status_code}")
                    print_error(f"Response: {response.text}")
            return len(self.created_ids["trackers"]) > 0
        except Exception as e:
            print_error(f"Create trackers error: {str(e)}")
            return False
    
    def test_create_cameras(self):
        """Create cameras before creating buses by uploading a dummy image."""
        print_step(5, "Creating Cameras")
        try:
            # Cameras are created automatically when they upload images via API
            # We'll upload a tiny dummy image to create each camera
            for camera_data in TEST_CAMERAS:
                # Create a tiny 1x1 pixel image
                img = Image.new('RGB', (1, 1), color=(0, 0, 0))
                img_bytes = BytesIO()
                img.save(img_bytes, format='JPEG')
                img_bytes.seek(0)
                
                # Upload via API to create the camera
                files = {
                    'image': ('dummy.jpg', img_bytes, 'image/jpeg')
                }
                data = {
                    'camera_id': camera_data["camera_id"],
                    'camera_name': camera_data["name"]
                }
                headers = {
                    'X-API-KEY': CAMERA_API_KEY
                }
                
                response = requests.post(
                    f"{self.api_base}/api/upload_camera_face",
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.created_ids["cameras"].append({
                        "code": camera_data["camera_id"],
                        "name": camera_data["name"],
                        "id": 0  # We don't have the ID from this response
                    })
                    print_success(f"Created camera: {camera_data['name']} (Code: {camera_data['camera_id']})")
                else:
                    print_error(f"Failed to create camera {camera_data['camera_id']}: {response.status_code}")
                    print_error(f"Response: {response.text}")
            
            # Verify cameras were created by checking the cameras endpoint
            response = requests.get(
                f"{self.api_base}/api/cameras",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                cameras = response.json()
                print_info(f"Total cameras registered: {len(cameras)}")
                return len(cameras) >= len(TEST_CAMERAS)
            else:
                print_error(f"Failed to verify cameras: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Create cameras error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_create_buses(self):
        """Create buses and associate with trackers and cameras."""
        print_step(6, "Creating Buses")
        try:
            for i, bus_data in enumerate(TEST_BUSES):
                # Get tracker and camera IDs
                tracker_id = self.created_ids["trackers"][i]["id"] if i < len(self.created_ids["trackers"]) else None
                camera_id = TEST_CAMERAS[i]["camera_id"] if i < len(TEST_CAMERAS) else None
                
                bus_payload = {
                    **bus_data,
                    "gps_tracker_id": tracker_id,
                    "camera_id": camera_id,
                }
                
                response = requests.post(
                    f"{self.api_base}/api/admin/buses",
                    json=bus_payload,
                    headers=self.get_headers(self.admin_token)
                )
                if response.status_code == 201:
                    bus = response.json()
                    self.created_ids["buses"].append(bus)
                    print_success(f"Created bus: {bus_data['bus_number']} (ID: {bus['id']})")
                    print_info(f"  - Tracker ID: {tracker_id}, Camera ID: {camera_id}")
                else:
                    print_error(f"Failed to create bus {bus_data['bus_number']}: {response.status_code}")
                    print_error(f"Response: {response.text}")
            return len(self.created_ids["buses"]) > 0
        except Exception as e:
            print_error(f"Create buses error: {str(e)}")
            return False
    
    def test_create_parents(self):
        """Create parent accounts."""
        print_step(7, "Creating Parent Accounts")
        try:
            for parent_data in TEST_PARENTS:
                response = requests.post(
                    f"{self.api_base}/api/admin/parents",
                    json=parent_data,
                    headers=self.get_headers(self.admin_token)
                )
                if response.status_code == 201:
                    parent = response.json()
                    self.created_ids["parents"].append(parent)
                    print_success(f"Created parent: {parent_data['full_name']} (ID: {parent['id']})")
                else:
                    print_error(f"Failed to create parent {parent_data['full_name']}: {response.status_code}")
                    print_error(f"Response: {response.text}")
            return len(self.created_ids["parents"]) > 0
        except Exception as e:
            print_error(f"Create parents error: {str(e)}")
            return False
    
    def create_test_face_image(self, student_name: str, student_index: int = 0) -> BytesIO:
        """Load a test face image from tests-images folder."""
        # Map student names to image files
        image_files = ["1.png", "2.png", "3.png", "4.png"]
        image_index = student_index % len(image_files)
        image_path = Path(__file__).parent / "tests-images" / image_files[image_index]
        
        if image_path.exists():
            # Read the image file
            with open(image_path, 'rb') as f:
                img_bytes = BytesIO(f.read())
            img_bytes.seek(0)
            return img_bytes
        else:
            # Fallback: create a simple colored image as a placeholder
            print_info(f"Image not found at {image_path}, using placeholder")
            img = Image.new('RGB', (200, 200), color=(73, 109, 137))
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            return img_bytes
    
    def test_create_students(self):
        """Create students with face images."""
        print_step(8, "Creating Students")
        try:
            for i, student_data in enumerate(TEST_STUDENTS):
                # Assign parent and bus based on student configuration
                parent_index = student_data.get("parent_index", i % len(self.created_ids["parents"]))
                bus_index = student_data.get("bus_index", i % len(self.created_ids["buses"]))
                
                parent_id = self.created_ids["parents"][parent_index]["id"] if parent_index < len(self.created_ids["parents"]) else self.created_ids["parents"][0]["id"]
                bus_id = self.created_ids["buses"][bus_index]["id"] if bus_index < len(self.created_ids["buses"]) and self.created_ids["buses"] else None
                
                # Create face image
                face_image = self.create_test_face_image(student_data["name"], i)
                
                # Prepare form data
                form_data = {
                    "name": student_data["name"],
                    "age": str(student_data["age"]),
                    "gender": student_data["gender"],
                    "parent_id": str(parent_id),
                    "bus_id": str(bus_id) if bus_id else "none",
                    "home_address": student_data["home_address"],
                    "home_latitude": str(student_data["home_latitude"]),
                    "home_longitude": str(student_data["home_longitude"]),
                }
                
                # Use PNG format for test images
                image_ext = "png" if i < 4 else "jpeg"
                image_mime = f"image/{image_ext}"
                files = {
                    "face_image": (f"{student_data['name']}_face.{image_ext}", face_image, image_mime)
                }
                
                response = requests.post(
                    f"{self.api_base}/api/admin/students",
                    data=form_data,
                    files=files,
                    headers={"Authorization": f"Bearer {self.admin_token}"}
                )
                
                if response.status_code == 201:
                    student = response.json()
                    self.created_ids["students"].append(student)
                    bus_number = f"Bus {bus_index + 1}" if bus_id else "None"
                    parent_name = TEST_PARENTS[parent_index]["full_name"] if parent_index < len(TEST_PARENTS) else "Unknown"
                    print_success(f"Created student: {student_data['name']} (ID: {student['id']})")
                    print_info(f"  - Parent: {parent_name} (ID: {parent_id}), Bus: {bus_number} (ID: {bus_id})")
                    if student_data.get("pickup_order"):
                        print_info(f"  - Pickup order: {student_data['pickup_order']}")
                else:
                    print_error(f"Failed to create student {student_data['name']}: {response.status_code}")
                    print_error(f"Response: {response.text}")
            return len(self.created_ids["students"]) > 0
        except Exception as e:
            print_error(f"Create students error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_gps_updates(self):
        """Simulate realistic GPS location updates for buses - morning (entry) and afternoon (exit) trips."""
        print_step(9, "Simulating GPS Location Updates")
        try:
            school_lat = TEST_SCHOOL_LOCATION["latitude"]
            school_lon = TEST_SCHOOL_LOCATION["longitude"]
            
            # Morning trip (ENTRY) - starts at 07:00
            morning_start = datetime.now(timezone.utc).replace(hour=7, minute=0, second=0, microsecond=0)
            
            # Afternoon trip (EXIT) - starts at 15:00
            afternoon_start = datetime.now(timezone.utc).replace(hour=15, minute=0, second=0, microsecond=0)
            
            for i, tracker in enumerate(self.created_ids["trackers"]):
                # Get all students assigned to this bus
                bus_students = [
                    (idx, student) for idx, student in enumerate(TEST_STUDENTS)
                    if student.get("bus_index", idx % len(self.created_ids["buses"])) == i
                ]
                
                # Sort students by pickup order
                bus_students.sort(key=lambda x: x[1].get("pickup_order", 1))
                
                if not bus_students:
                    print_info(f"No students assigned to bus {i+1}, skipping GPS updates")
                    continue
                
                # Print route summary
                student_names = [s[1]["name"] for s in bus_students]
                route_str = " → ".join([f"{name}'s home" for name in student_names] + ["School"])
                print_info(f"Bus {i+1} route: {route_str}")
                
                # MORNING TRIP (ENTRY) - Pick up students and go to school
                print_info(f"\n=== Bus {i+1} - Morning Trip (ENTRY) ===")
                current_time = morning_start
                
                # Start from first student's home
                current_lat = bus_students[0][1]["home_latitude"]
                current_lon = bus_students[0][1]["home_longitude"]
                
                # Send initial position (at first student's home)
                response = requests.post(
                    f"{self.api_base}/api/device/gps/update",
                    json={
                        "device_id": tracker["device_id"],
                        "latitude": current_lat,
                        "longitude": current_lon,
                        "timestamp": current_time.isoformat()
                    },
                    headers={
                        "X-API-KEY": GPS_DEVICE_API_KEY,
                        "Content-Type": "application/json"
                    }
                )
                if response.status_code == 200:
                    print_success(f"Bus {i+1} at {bus_students[0][1]['name']}'s home")
                    time.sleep(0.3)
                
                # Move to each subsequent student's home
                for student_idx, (orig_idx, student) in enumerate(bus_students[1:], start=1):
                    target_lat = student["home_latitude"]
                    target_lon = student["home_longitude"]
                    
                    # Create intermediate points between current position and next student's home
                    num_points = 4
                    for j in range(1, num_points + 1):
                        ratio = j / num_points
                        lat = current_lat + (target_lat - current_lat) * ratio
                        lon = current_lon + (target_lon - current_lon) * ratio
                        current_time += timedelta(seconds=30)  # 30 seconds between points
                        
                        response = requests.post(
                            f"{self.api_base}/api/device/gps/update",
                            json={
                                "device_id": tracker["device_id"],
                                "latitude": lat,
                                "longitude": lon,
                                "timestamp": current_time.isoformat()
                            },
                            headers={
                                "X-API-KEY": GPS_DEVICE_API_KEY,
                                "Content-Type": "application/json"
                            }
                        )
                        if response.status_code == 200:
                            print_success(f"Bus {i+1} moving to {student['name']}'s home ({j}/{num_points})")
                            time.sleep(0.3)
                    
                    # Arrive at student's home
                    current_lat = target_lat
                    current_lon = target_lon
                    current_time += timedelta(seconds=30)
                    response = requests.post(
                        f"{self.api_base}/api/device/gps/update",
                        json={
                            "device_id": tracker["device_id"],
                            "latitude": current_lat,
                            "longitude": current_lon,
                            "timestamp": current_time.isoformat()
                        },
                        headers={
                            "X-API-KEY": GPS_DEVICE_API_KEY,
                            "Content-Type": "application/json"
                        }
                    )
                    if response.status_code == 200:
                        print_success(f"Bus {i+1} arrived at {student['name']}'s home")
                        time.sleep(0.5)  # Wait at pickup location
                
                # Now move from last pickup to school
                num_points = 6
                for j in range(1, num_points + 1):
                    ratio = j / num_points
                    lat = current_lat + (school_lat - current_lat) * ratio
                    lon = current_lon + (school_lon - current_lon) * ratio
                    current_time += timedelta(seconds=45)  # 45 seconds between points
                    
                    response = requests.post(
                        f"{self.api_base}/api/device/gps/update",
                        json={
                            "device_id": tracker["device_id"],
                            "latitude": lat,
                            "longitude": lon,
                            "timestamp": current_time.isoformat()
                        },
                        headers={
                            "X-API-KEY": GPS_DEVICE_API_KEY,
                            "Content-Type": "application/json"
                        }
                    )
                    if response.status_code == 200:
                        print_success(f"Bus {i+1} heading to school ({j}/{num_points})")
                        time.sleep(0.3)
                
                # Arrive at school
                current_time += timedelta(seconds=45)
                response = requests.post(
                    f"{self.api_base}/api/device/gps/update",
                    json={
                        "device_id": tracker["device_id"],
                        "latitude": school_lat,
                        "longitude": school_lon,
                        "timestamp": current_time.isoformat()
                    },
                    headers={
                        "X-API-KEY": GPS_DEVICE_API_KEY,
                        "Content-Type": "application/json"
                    }
                )
                if response.status_code == 200:
                    print_success(f"Bus {i+1} arrived at school (morning trip)")
                    time.sleep(0.5)
                
                # AFTERNOON TRIP (EXIT) - Start from school, drop off students
                print_info(f"\n=== Bus {i+1} - Afternoon Trip (EXIT) ===")
                current_time = afternoon_start
                current_lat = school_lat
                current_lon = school_lon
                
                # Start from school
                response = requests.post(
                    f"{self.api_base}/api/device/gps/update",
                    json={
                        "device_id": tracker["device_id"],
                        "latitude": current_lat,
                        "longitude": current_lon,
                        "timestamp": current_time.isoformat()
                    },
                    headers={
                        "X-API-KEY": GPS_DEVICE_API_KEY,
                        "Content-Type": "application/json"
                    }
                )
                if response.status_code == 200:
                    print_success(f"Bus {i+1} leaving school")
                    time.sleep(0.3)
                
                # Drop off students in reverse order
                for student_idx, (orig_idx, student) in enumerate(reversed(bus_students), start=1):
                    target_lat = student["home_latitude"]
                    target_lon = student["home_longitude"]
                    
                    # Create intermediate points
                    num_points = 4
                    for j in range(1, num_points + 1):
                        ratio = j / num_points
                        lat = current_lat + (target_lat - current_lat) * ratio
                        lon = current_lon + (target_lon - current_lon) * ratio
                        current_time += timedelta(seconds=30)
                        
                        response = requests.post(
                            f"{self.api_base}/api/device/gps/update",
                            json={
                                "device_id": tracker["device_id"],
                                "latitude": lat,
                                "longitude": lon,
                                "timestamp": current_time.isoformat()
                            },
                            headers={
                                "X-API-KEY": GPS_DEVICE_API_KEY,
                                "Content-Type": "application/json"
                            }
                        )
                        if response.status_code == 200:
                            print_success(f"Bus {i+1} heading to {student['name']}'s home ({j}/{num_points})")
                            time.sleep(0.3)
                    
                    # Arrive at student's home
                    current_lat = target_lat
                    current_lon = target_lon
                    current_time += timedelta(seconds=30)
                    response = requests.post(
                        f"{self.api_base}/api/device/gps/update",
                        json={
                            "device_id": tracker["device_id"],
                            "latitude": current_lat,
                            "longitude": current_lon,
                            "timestamp": current_time.isoformat()
                        },
                        headers={
                            "X-API-KEY": GPS_DEVICE_API_KEY,
                            "Content-Type": "application/json"
                        }
                    )
                    if response.status_code == 200:
                        print_success(f"Bus {i+1} arrived at {student['name']}'s home (afternoon trip)")
                        time.sleep(0.5)
            
            return True
        except Exception as e:
            print_error(f"GPS updates error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_camera_uploads(self):
        """Simulate camera face uploads for students - entry (morning) and exit (afternoon) attendance."""
        print_step(10, "Simulating Camera Face Uploads")
        try:
            # Morning attendance (ENTRY) - around 07:00-08:00
            morning_time = datetime.now(timezone.utc).replace(hour=7, minute=30, second=0, microsecond=0)
            
            # Afternoon attendance (EXIT) - around 15:00-16:00
            afternoon_time = datetime.now(timezone.utc).replace(hour=15, minute=30, second=0, microsecond=0)
            
            # MORNING UPLOADS (ENTRY)
            print_info("\n=== Morning Attendance (ENTRY) ===")
            for i, student_data in enumerate(TEST_STUDENTS):
                if i >= len(self.created_ids["students"]):
                    continue
                
                student = self.created_ids["students"][i]
                bus_index = student_data.get("bus_index", i % len(TEST_CAMERAS))
                
                if bus_index >= len(TEST_CAMERAS):
                    print_error(f"No camera for bus {bus_index + 1}")
                    continue
                
                camera = TEST_CAMERAS[bus_index]
                
                # Create test image using the student's face image
                face_image = self.create_test_face_image(student_data["name"], i)
                
                # Upload face image (use PNG if original is PNG)
                image_ext = "png" if i < 4 else "jpeg"
                image_mime = f"image/{image_ext}"
                files = {
                    "image": (f"face_{student_data['name']}_entry.{image_ext}", face_image, image_mime)
                }
                # Use morning time for entry attendance
                upload_time = morning_time + timedelta(minutes=i * 2)  # Stagger uploads
                data = {
                    "camera_id": camera["camera_id"],
                    "camera_name": camera["name"],
                    "timestamp": upload_time.isoformat()
                }
                
                response = requests.post(
                    f"{self.api_base}/api/upload_camera_face",
                    data=data,
                    files=files,
                    headers={"X-API-KEY": CAMERA_API_KEY}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print_success(f"Entry attendance for {student_data['name']} from {camera['name']} successful")
                    print_info(f"  - Image URL: {result.get('image_url', 'N/A')}")
                    print_info(f"  - Time: {upload_time.strftime('%H:%M:%S')}")
                    time.sleep(1)  # Small delay between uploads
                else:
                    print_error(f"Face upload failed for {student_data['name']}: {response.status_code}")
                    print_error(f"Response: {response.text}")
            
            # Wait a bit before afternoon uploads
            time.sleep(2)
            
            # AFTERNOON UPLOADS (EXIT)
            print_info("\n=== Afternoon Attendance (EXIT) ===")
            for i, student_data in enumerate(TEST_STUDENTS):
                if i >= len(self.created_ids["students"]):
                    continue
                
                student = self.created_ids["students"][i]
                bus_index = student_data.get("bus_index", i % len(TEST_CAMERAS))
                
                if bus_index >= len(TEST_CAMERAS):
                    continue
                
                camera = TEST_CAMERAS[bus_index]
                
                # Create test image using the student's face image
                face_image = self.create_test_face_image(student_data["name"], i)
                
                # Upload face image
                image_ext = "png" if i < 4 else "jpeg"
                image_mime = f"image/{image_ext}"
                files = {
                    "image": (f"face_{student_data['name']}_exit.{image_ext}", face_image, image_mime)
                }
                # Use afternoon time for exit attendance
                upload_time = afternoon_time + timedelta(minutes=i * 2)  # Stagger uploads
                data = {
                    "camera_id": camera["camera_id"],
                    "camera_name": camera["name"],
                    "timestamp": upload_time.isoformat()
                }
                
                response = requests.post(
                    f"{self.api_base}/api/upload_camera_face",
                    data=data,
                    files=files,
                    headers={"X-API-KEY": CAMERA_API_KEY}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print_success(f"Exit attendance for {student_data['name']} from {camera['name']} successful")
                    print_info(f"  - Image URL: {result.get('image_url', 'N/A')}")
                    print_info(f"  - Time: {upload_time.strftime('%H:%M:%S')}")
                    time.sleep(1)  # Small delay between uploads
                else:
                    print_error(f"Face upload failed for {student_data['name']}: {response.status_code}")
                    print_error(f"Response: {response.text}")
            
            return True
        except Exception as e:
            print_error(f"Camera uploads error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_parent_login(self):
        """Test parent login."""
        print_step(11, "Testing Parent Login")
        try:
            for parent_data in TEST_PARENTS:
                # Try login with email
                response = requests.post(
                    f"{self.api_base}/api/auth/login",
                    json={"email": parent_data["email"], "password": parent_data["password"]},
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    data = response.json()
                    self.parent_tokens[parent_data["email"]] = data["access_token"]
                    print_success(f"Parent login successful: {parent_data['email']}")
                else:
                    print_error(f"Parent login failed: {response.status_code}")
                    print_error(f"Response: {response.text}")
            return len(self.parent_tokens) > 0
        except Exception as e:
            print_error(f"Parent login error: {str(e)}")
            return False
    
    def test_parent_apis(self):
        """Test parent dashboard APIs."""
        print_step(12, "Testing Parent APIs")
        try:
            if not self.parent_tokens:
                print_error("No parent tokens available")
                return False
            
            parent_email = list(self.parent_tokens.keys())[0]
            parent_token = self.parent_tokens[parent_email]
            
            # Get my students
            response = requests.get(
                f"{self.api_base}/api/parent/students",
                headers=self.get_headers(parent_token)
            )
            if response.status_code == 200:
                students = response.json()
                print_success(f"Got {len(students)} students for parent")
                
                # Test last attendance for first student
                if students:
                    student_id = students[0]["id"]
                    response = requests.get(
                        f"{self.api_base}/api/parent/students/{student_id}/last-attendance",
                        headers=self.get_headers(parent_token)
                    )
                    if response.status_code == 200:
                        attendance = response.json()
                        print_success(f"Got last attendance for student {student_id}")
                    else:
                        print_info(f"No attendance found for student {student_id}")
                    
                    # Test bus location
                    response = requests.get(
                        f"{self.api_base}/api/parent/students/{student_id}/bus-location",
                        headers=self.get_headers(parent_token)
                    )
                    if response.status_code == 200:
                        location = response.json()
                        print_success(f"Got bus location for student {student_id}")
                    else:
                        print_info(f"No bus location found for student {student_id}")
            
            return True
        except Exception as e:
            print_error(f"Parent APIs error: {str(e)}")
            return False
    
    async def test_websocket_admin(self):
        """Test admin WebSocket connection."""
        print_step(13, "Testing Admin WebSocket")
        try:
            ws_url = self.api_base.replace("http://", "ws://").replace("https://", "wss://")
            # Add token to WebSocket URL if needed
            token = self.admin_token if self.admin_token else ""
            ws_endpoint = f"{ws_url}/ws/admin/buses"
            
            async with websockets.connect(ws_endpoint) as websocket:
                # Wait for initial data
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print_success("Admin WebSocket connected")
                    print_info(f"Received initial data: {len(data.get('buses', []))} buses")
                    return True
                except asyncio.TimeoutError:
                    print_info("No initial message received (this is OK if no buses)")
                    return True
        except Exception as e:
            print_error(f"Admin WebSocket error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    async def test_websocket_parent(self):
        """Test parent WebSocket connection."""
        print_step(14, "Testing Parent WebSocket")
        try:
            if not self.created_ids["students"]:
                print_error("No students available for WebSocket test")
                return False
            
            student_id = self.created_ids["students"][0]["id"]
            ws_url = self.api_base.replace("http://", "ws://").replace("https://", "wss://")
            
            async with websockets.connect(f"{ws_url}/ws/parent/{student_id}") as websocket:
                # Wait for initial data
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print_success("Parent WebSocket connected")
                    print_info(f"Received initial data for student {student_id}")
                    if data.get("type") == "student_bus_location":
                        print_info(f"  - Bus location: {data.get('latitude')}, {data.get('longitude')}")
                    
                    # Send ping to keep connection alive
                    await websocket.send("ping")
                    pong = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    if pong == "pong":
                        print_success("WebSocket ping/pong working")
                    
                    return True
                except asyncio.TimeoutError:
                    print_info("No initial message received (this is OK if no bus location)")
                    return True
        except Exception as e:
            print_error(f"Parent WebSocket error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_websocket_device(self):
        """Test GPS device WebSocket connection."""
        print_step(15, "Testing GPS Device WebSocket")
        try:
            if not self.created_ids["trackers"]:
                print_error("No trackers available for WebSocket test")
                return False
            
            tracker = self.created_ids["trackers"][0]
            tracker_id = tracker["device_id"]
            ws_url = self.api_base.replace("http://", "ws://").replace("https://", "wss://")
            
            async with websockets.connect(f"{ws_url}/ws/device/gps/{tracker_id}") as websocket:
                print_success("GPS Device WebSocket connected")
                
                # Send a location update
                location_update = {
                    "type": "location_update",
                    "latitude": 24.7136,
                    "longitude": 46.6753,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send(json.dumps(location_update))
                print_success("Sent location update via WebSocket")
                
                # Wait a bit for processing
                await asyncio.sleep(1)
                return True
        except Exception as e:
            print_error(f"GPS Device WebSocket error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_dashboard_stats(self):
        """Test admin dashboard statistics."""
        print_step(16, "Testing Dashboard Statistics")
        try:
            response = requests.get(
                f"{self.api_base}/api/admin/dashboard/stats",
                headers=self.get_headers(self.admin_token)
            )
            if response.status_code == 200:
                stats = response.json()
                print_success("Dashboard stats retrieved")
                print_info(f"  - Total buses: {stats.get('total_buses', 0)}")
                print_info(f"  - Total students: {stats.get('total_students', 0)}")
                print_info(f"  - Total parents: {stats.get('total_parents', 0)}")
                print_info(f"  - Total trackers: {stats.get('total_trackers', 0)}")
                print_info(f"  - Active buses: {stats.get('active_buses', 0)}")
                return True
            else:
                print_error(f"Failed to get dashboard stats: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            print_error(f"Dashboard stats error: {str(e)}")
            return False
    
    def test_attendance_history(self):
        """Test attendance history retrieval."""
        print_step(17, "Testing Attendance History")
        try:
            if not self.created_ids["students"]:
                print_error("No students available for attendance test")
                return False
            
            student_id = self.created_ids["students"][0]["id"]
            parent_email = list(self.parent_tokens.keys())[0] if self.parent_tokens else None
            
            if not parent_email:
                print_error("No parent token available")
                return False
            
            parent_token = self.parent_tokens[parent_email]
            
            # Get attendance history
            response = requests.get(
                f"{self.api_base}/api/parent/students/{student_id}/attendance/history",
                headers=self.get_headers(parent_token),
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                history = response.json()
                print_success(f"Retrieved attendance history ({len(history)} records)")
                if history:
                    latest = history[0]
                    print_info(f"  - Latest attendance: {latest.get('detected_at', 'N/A')}")
                    print_info(f"  - Similarity: {latest.get('similarity_score', 'N/A')}")
                return True
            else:
                print_info(f"No attendance history found (status: {response.status_code})")
                return True  # This is OK if no attendance yet
        except Exception as e:
            print_error(f"Attendance history error: {str(e)}")
            return False
    
    def test_route_history(self):
        """Test route history retrieval."""
        print_step(18, "Testing Route History")
        try:
            if not self.created_ids["students"]:
                print_error("No students available for route test")
                return False
            
            student_id = self.created_ids["students"][0]["id"]
            parent_email = list(self.parent_tokens.keys())[0] if self.parent_tokens else None
            
            if not parent_email:
                print_error("No parent token available")
                return False
            
            parent_token = self.parent_tokens[parent_email]
            
            # Get route history for today
            today = datetime.now(timezone.utc).date().isoformat()
            response = requests.get(
                f"{self.api_base}/api/parent/students/{student_id}/route/history",
                headers=self.get_headers(parent_token),
                params={"date": today}
            )
            
            if response.status_code == 200:
                route_data = response.json()
                route_points = route_data.get("route_points", [])
                print_success(f"Retrieved route history ({len(route_points)} points)")
                if route_points:
                    print_info(f"  - First point: {route_points[0].get('latitude')}, {route_points[0].get('longitude')}")
                    print_info(f"  - Last point: {route_points[-1].get('latitude')}, {route_points[-1].get('longitude')}")
                return True
            else:
                print_info(f"No route history found (status: {response.status_code})")
                return True  # This is OK if no route yet
        except Exception as e:
            print_error(f"Route history error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all integration tests."""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}Integration Test Suite - Parental Child Tracking System{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")
        
        results = {}
        
        # Synchronous tests
        results["health_check"] = self.test_health_check()
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            print_error("Cannot continue without admin login")
            return results
        
        results["system_settings"] = self.test_create_system_settings()
        results["gps_trackers"] = self.test_create_gps_trackers()
        results["cameras"] = self.test_create_cameras()
        results["buses"] = self.test_create_buses()
        results["parents"] = self.test_create_parents()
        results["students"] = self.test_create_students()
        results["gps_updates"] = self.test_gps_updates()
        results["camera_uploads"] = self.test_camera_uploads()
        results["parent_login"] = self.test_parent_login()
        results["parent_apis"] = self.test_parent_apis()
        results["dashboard_stats"] = self.test_dashboard_stats()
        results["attendance_history"] = self.test_attendance_history()
        results["route_history"] = self.test_route_history()
        
        # Async tests
        async def run_async_tests():
            results["websocket_admin"] = await self.test_websocket_admin()
            results["websocket_parent"] = await self.test_websocket_parent()
            results["websocket_device"] = await self.test_websocket_device()
        
        # Run async tests
        asyncio.run(run_async_tests())
        
        # Print summary
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}Test Summary{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if result else f"{Colors.FAIL}FAIL{Colors.ENDC}"
            print(f"  {status} - {test_name}")
        
        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}\n")
        
        if passed == total:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✓ All tests passed!{Colors.ENDC}\n")
        else:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠ Some tests failed{Colors.ENDC}\n")
        
        return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Integration test for Parental Child Tracking System")
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_BASE_URL", "http://localhost:8000"),
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--camera-api-key",
        default=os.getenv("CAMERA_API_KEY", "changeme_camera_api_key"),
        help="Camera API key"
    )
    parser.add_argument(
        "--gps-api-key",
        default=os.getenv("GPS_DEVICE_API_KEY", "changeme_gps_api_key"),
        help="GPS device API key"
    )
    parser.add_argument(
        "--admin-email",
        default=os.getenv("ADMIN_EMAIL", "admin@school.com"),
        help="Admin email"
    )
    parser.add_argument(
        "--admin-password",
        default=os.getenv("ADMIN_PASSWORD", "admin123"),
        help="Admin password"
    )
    parser.add_argument(
        "--skip-websocket",
        action="store_true",
        help="Skip WebSocket tests"
    )
    
    args = parser.parse_args()
    
    # Update global config
    global API_BASE_URL, CAMERA_API_KEY, GPS_DEVICE_API_KEY, ADMIN_EMAIL, ADMIN_PASSWORD
    API_BASE_URL = args.api_url
    CAMERA_API_KEY = args.camera_api_key
    GPS_DEVICE_API_KEY = args.gps_api_key
    ADMIN_EMAIL = args.admin_email
    ADMIN_PASSWORD = args.admin_password
    
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("Parental Child Tracking System - Integration Test")
    print("=" * 70)
    print(f"{Colors.ENDC}")
    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Admin Email: {ADMIN_EMAIL}")
    print()
    print(f"{Colors.OKCYAN}{Colors.BOLD}Test Scenario:{Colors.ENDC}")
    print(f"  • {Colors.BOLD}Khalid{Colors.ENDC} & {Colors.BOLD}Omar{Colors.ENDC} - Brothers (same parent) - {Colors.BOLD}Bus 1{Colors.ENDC}")
    print(f"    Route: Khalid's home → Omar's home → School")
    print(f"  • {Colors.BOLD}Sara{Colors.ENDC} - {Colors.BOLD}Bus 2{Colors.ENDC}")
    print(f"    Route: Sara's home → School")
    print()
    
    # Create test instance
    test = IntegrationTest()
    
    # Run synchronous tests
    results = []
    
    results.append(("Health Check", test.test_health_check()))
    if not results[-1][1]:
        print_error("Health check failed. Please ensure the API is running.")
        sys.exit(1)
    
    results.append(("Admin Login", test.test_admin_login()))
    if not results[-1][1]:
        print_error("Admin login failed. Please check credentials.")
        sys.exit(1)
    
    results.append(("System Settings", test.test_create_system_settings()))
    results.append(("GPS Trackers", test.test_create_gps_trackers()))
    results.append(("Cameras", test.test_create_cameras()))
    results.append(("Buses", test.test_create_buses()))
    results.append(("Parents", test.test_create_parents()))
    results.append(("Students", test.test_create_students()))
    results.append(("GPS Updates", test.test_gps_updates()))
    results.append(("Camera Uploads", test.test_camera_uploads()))
    results.append(("Parent Login", test.test_parent_login()))
    results.append(("Parent APIs", test.test_parent_apis()))
    results.append(("Dashboard Stats", test.test_dashboard_stats()))
    results.append(("Attendance History", test.test_attendance_history()))
    results.append(("Route History", test.test_route_history()))
    
    # Run async WebSocket tests
    if not args.skip_websocket:
        async def run_async_tests():
            ws_results = []
            ws_results.append(("Admin WebSocket", await test.test_websocket_admin()))
            ws_results.append(("Parent WebSocket", await test.test_websocket_parent()))
            ws_results.append(("Device WebSocket", await test.test_websocket_device()))
            return ws_results
        
        print(f"\n{Colors.HEADER}[Async Tests]{Colors.ENDC}")
        ws_results = asyncio.run(run_async_tests())
        results.extend(ws_results)
    else:
        print_info("Skipping WebSocket tests (--skip-websocket)")
    
    # Print summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"{Colors.ENDC}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.OKGREEN}✓ PASS{Colors.ENDC}" if result else f"{Colors.FAIL}✗ FAIL{Colors.ENDC}"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"{Colors.OKGREEN}{Colors.BOLD}All tests passed!{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}Some tests failed.{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()         