"""
GPS service - GPS calculations and utilities.
"""
from typing import Optional, Tuple, List
from datetime import datetime
from geopy.distance import geodesic
from sqlalchemy.orm import Session
from app import models, crud


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two GPS coordinates in meters."""
    point1 = (lat1, lng1)
    point2 = (lat2, lng2)
    distance = geodesic(point1, point2).meters
    return distance


def is_near_school(
    latitude: float,
    longitude: float,
    school_latitude: float,
    school_longitude: float,
    radius_meters: float = 100.0
) -> bool:
    """Check if GPS coordinates are near school."""
    if not school_latitude or not school_longitude:
        return False
    
    distance = calculate_distance(latitude, longitude, school_latitude, school_longitude)
    return distance <= radius_meters


def get_route_path(
    db: Session,
    tracker_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[Tuple[float, float, datetime]]:
    """Get route path (list of lat, lng, timestamp tuples) for a tracker."""
    gps_logs = crud.get_gps_logs_by_tracker(db, tracker_id, start_time, end_time)
    return [(log.latitude, log.longitude, log.timestamp) for log in gps_logs]


def get_bus_route_path(
    db: Session,
    bus_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[Tuple[float, float, datetime]]:
    """Get route path for a bus."""
    gps_logs = crud.get_gps_logs_by_bus(db, bus_id, start_time, end_time)
    return [(log.latitude, log.longitude, log.timestamp) for log in gps_logs]


def is_active_time(bus: models.Bus) -> bool:
    """
    Check if current time is within bus active hours.
    
    NOTE: This function is for informational purposes only.
    Real-time tracking availability is controlled by websocket_enabled in system settings.
    Bus activity times (morning_start, morning_end, etc.) are just informational data
    and do not affect real-time tracking functionality.
    """
    if not bus:
        return False
    
    now = datetime.utcnow().time()
    
    # Check morning time
    if bus.morning_start and bus.morning_end:
        try:
            morning_start = datetime.strptime(bus.morning_start, "%H:%M").time()
            morning_end = datetime.strptime(bus.morning_end, "%H:%M").time()
            if morning_start <= now <= morning_end:
                return True
        except (ValueError, AttributeError):
            pass
    
    # Check afternoon time
    if bus.afternoon_start and bus.afternoon_end:
        try:
            afternoon_start = datetime.strptime(bus.afternoon_start, "%H:%M").time()
            afternoon_end = datetime.strptime(bus.afternoon_end, "%H:%M").time()
            if afternoon_start <= now <= afternoon_end:
                return True
        except (ValueError, AttributeError):
            pass
    
    return False


