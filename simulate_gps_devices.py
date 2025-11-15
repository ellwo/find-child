#!/usr/bin/env python3
"""
GPS Device Simulator - Simulates GPS tracker devices sending location updates via WebSocket

This script simulates two GPS trackers (GPS_TRACKER_001 and GPS_TRACKER_002) moving along routes
and sending location updates via WebSocket.

Usage:
    python simulate_gps_devices.py
    python simulate_gps_devices.py --api-url http://localhost:8000
"""

import os
import sys
import json
import asyncio
import websockets
from datetime import datetime
from typing import List, Tuple
import argparse

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WS_BASE_URL = API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")

# GPS Trackers
TRACKERS = [
    {
        "device_id": "GPS_TRACKER_001",
        "name": "Bus 1 GPS Tracker",
        "route": [
            (24.7154, 46.6840),  # Start: Home location
            (24.7140, 46.6820),
            (24.7120, 46.6800),
            (24.7100, 46.6780),
            (24.7136, 46.6753),  # End: School location
        ]
    },
    {
        "device_id": "GPS_TRACKER_002",
        "name": "Bus 2 GPS Tracker",
        "route": [
            (24.7200, 46.6900),  # Start: Home location
            (24.7180, 46.6880),
            (24.7160, 46.6860),
            (24.7140, 46.6840),
            (24.7136, 46.6753),  # End: School location
        ]
    }
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


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ{Colors.ENDC} {message}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {message}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗{Colors.ENDC} {message}")


def interpolate_points(start: Tuple[float, float], end: Tuple[float, float], num_points: int) -> List[Tuple[float, float]]:
    """Interpolate points between start and end."""
    points = []
    for i in range(num_points + 1):
        ratio = i / num_points
        lat = start[0] + (end[0] - start[0]) * ratio
        lon = start[1] + (end[1] - start[1]) * ratio
        points.append((lat, lon))
    return points


async def simulate_tracker(tracker_config: dict, delay: float = 2.0):
    """Simulate a GPS tracker device sending location updates."""
    device_id = tracker_config["device_id"]
    name = tracker_config["name"]
    route = tracker_config["route"]
    
    print_info(f"Starting simulation for {name} ({device_id})")
    
    ws_url = f"{WS_BASE_URL}/ws/device/gps/{device_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print_success(f"Connected to WebSocket for {device_id}")
            
            # Expand route with interpolated points
            full_route = []
            for i in range(len(route) - 1):
                segment_points = interpolate_points(route[i], route[i + 1], num_points=5)
                if i > 0:
                    # Skip first point to avoid duplicates
                    full_route.extend(segment_points[1:])
                else:
                    full_route.extend(segment_points)
            
            # Send location updates along the route
            for idx, (lat, lon) in enumerate(full_route):
                location_update = {
                    "type": "location_update",
                    "latitude": lat,
                    "longitude": lon,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send(json.dumps(location_update))
                print_success(f"{device_id}: Sent location update {idx + 1}/{len(full_route)} - ({lat:.6f}, {lon:.6f})")
                
                # Wait before next update
                await asyncio.sleep(delay)
            
            # Reverse route (return trip)
            print_info(f"{device_id}: Starting return trip...")
            for idx, (lat, lon) in enumerate(reversed(full_route)):
                location_update = {
                    "type": "location_update",
                    "latitude": lat,
                    "longitude": lon,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send(json.dumps(location_update))
                print_success(f"{device_id}: Return trip - update {idx + 1}/{len(full_route)} - ({lat:.6f}, {lon:.6f})")
                
                await asyncio.sleep(delay)
            
            print_success(f"{device_id}: Route simulation completed")
            
    except websockets.exceptions.ConnectionClosed:
        print_error(f"{device_id}: WebSocket connection closed")
    except Exception as e:
        print_error(f"{device_id}: Error - {str(e)}")
        import traceback
        traceback.print_exc()


async def simulate_all_trackers(delay: float = 2.0, continuous: bool = False):
    """Simulate all GPS trackers."""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("GPS Device Simulator")
    print("=" * 70)
    print(f"{Colors.ENDC}")
    print_info(f"WebSocket URL: {WS_BASE_URL}")
    print_info(f"Update delay: {delay} seconds")
    print_info(f"Continuous mode: {continuous}")
    print()
    
    if continuous:
        print_info("Running in continuous mode (will loop forever, press Ctrl+C to stop)")
        print()
        
        try:
            while True:
                tasks = [
                    simulate_tracker(tracker, delay)
                    for tracker in TRACKERS
                ]
                await asyncio.gather(*tasks)
                print_info("Route cycle completed, starting again...")
                await asyncio.sleep(5)  # Wait before next cycle
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Simulation stopped by user{Colors.ENDC}")
    else:
        # Run once
        tasks = [
            simulate_tracker(tracker, delay)
            for tracker in TRACKERS
        ]
        await asyncio.gather(*tasks)
        print_success("All simulations completed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Simulate GPS tracker devices sending location updates via WebSocket"
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_BASE_URL", "http://localhost:8000"),
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between location updates in seconds (default: 2.0)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run in continuous mode (loop forever)"
    )
    
    args = parser.parse_args()
    
    # Update global config
    global API_BASE_URL, WS_BASE_URL
    API_BASE_URL = args.api_url
    WS_BASE_URL = API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
    
    # Run simulation
    try:
        asyncio.run(simulate_all_trackers(delay=args.delay, continuous=args.continuous))
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Simulation interrupted{Colors.ENDC}")
        sys.exit(0)


if __name__ == "__main__":
    main()

