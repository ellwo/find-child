"""
WebSocket endpoints for real-time updates.
"""
import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import get_db, SessionLocal
from app import models, crud
from app.services import gps_service


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        # Store connections by type and identifier
        self.admin_buses_connections: Set[WebSocket] = set()
        self.parent_connections: Dict[int, Set[WebSocket]] = {}  # student_id -> connections
        self.device_connections: Dict[str, Set[WebSocket]] = {}  # tracker_id -> connections
    
    async def connect_admin_buses(self, websocket: WebSocket):
        """Connect admin to buses tracking."""
        await websocket.accept()
        self.admin_buses_connections.add(websocket)
    
    async def disconnect_admin_buses(self, websocket: WebSocket):
        """Disconnect admin from buses tracking."""
        self.admin_buses_connections.discard(websocket)
    
    async def connect_parent(self, websocket: WebSocket, student_id: int):
        """Connect parent to student tracking."""
        await websocket.accept()
        if student_id not in self.parent_connections:
            self.parent_connections[student_id] = set()
        self.parent_connections[student_id].add(websocket)
    
    async def disconnect_parent(self, websocket: WebSocket, student_id: int):
        """Disconnect parent from student tracking."""
        if student_id in self.parent_connections:
            self.parent_connections[student_id].discard(websocket)
            if not self.parent_connections[student_id]:
                del self.parent_connections[student_id]
    
    async def connect_device(self, websocket: WebSocket, tracker_id: str):
        """Connect GPS device."""
        await websocket.accept()
        if tracker_id not in self.device_connections:
            self.device_connections[tracker_id] = set()
        self.device_connections[tracker_id].add(websocket)
    
    async def disconnect_device(self, websocket: WebSocket, tracker_id: str):
        """Disconnect GPS device."""
        if tracker_id in self.device_connections:
            self.device_connections[tracker_id].discard(websocket)
            if not self.device_connections[tracker_id]:
                del self.device_connections[tracker_id]
    
    async def broadcast_bus_location(self, bus_id: int, latitude: float, longitude: float, timestamp: datetime):
        """Broadcast bus location to admin connections."""
        message = {
            "type": "bus_location",
            "bus_id": bus_id,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": timestamp.isoformat()
        }
        disconnected = set()
        for connection in self.admin_buses_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)
        for conn in disconnected:
            self.admin_buses_connections.discard(conn)
    
    async def broadcast_student_location(self, student_id: int, bus_id: int, latitude: float, longitude: float, timestamp: datetime):
        """Broadcast student's bus location to parent connections."""
        message = {
            "type": "student_bus_location",
            "student_id": student_id,
            "bus_id": bus_id,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": timestamp.isoformat()
        }
        if student_id in self.parent_connections:
            disconnected = set()
            for connection in self.parent_connections[student_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            for conn in disconnected:
                self.parent_connections[student_id].discard(conn)
    
    async def broadcast_attendance(self, student_id: int, attendance_data: dict):
        """Broadcast attendance update to parent connections."""
        message = {
            "type": "attendance",
            "student_id": student_id,
            "data": attendance_data
        }
        if student_id in self.parent_connections:
            disconnected = set()
            for connection in self.parent_connections[student_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            for conn in disconnected:
                self.parent_connections[student_id].discard(conn)


# Global connection manager
manager = ConnectionManager()


async def websocket_admin_buses(websocket: WebSocket):
    """WebSocket endpoint for admin to track all buses."""
    await websocket.accept()
    db = SessionLocal()
    try:
        # Send initial bus locations
        buses = db.query(models.Bus).filter(models.Bus.is_active == True).all()
        for bus in buses:
            if bus.gps_tracker_id:
                tracker = crud.get_gps_tracker_by_id(db, bus.gps_tracker_id)
                if tracker and tracker.last_latitude and tracker.last_longitude:
                    await websocket.send_json({
                        "type": "bus_location",
                        "bus_id": bus.id,
                        "bus_number": bus.bus_number,
                        "latitude": tracker.last_latitude,
                        "longitude": tracker.last_longitude,
                        "timestamp": tracker.last_update_timestamp.isoformat() if tracker.last_update_timestamp else None
                    })
        
        await manager.connect_admin_buses(websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle ping/pong or other messages if needed
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect_admin_buses(websocket)
    finally:
        db.close()


async def websocket_parent_student(websocket: WebSocket, student_id: int):
    """WebSocket endpoint for parent to track a specific student's bus."""
    await websocket.accept()
    db = SessionLocal()
    try:
        # Verify student exists
        student = crud.get_student_by_id(db, student_id)
        if not student:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        await manager.connect_parent(websocket, student_id)
        
        # Send initial bus location if available
        if student.bus_id:
            bus = crud.get_bus_by_id(db, student.bus_id)
            if bus and bus.gps_tracker_id:
                tracker = crud.get_gps_tracker_by_id(db, bus.gps_tracker_id)
                if tracker and tracker.last_latitude and tracker.last_longitude:
                    await websocket.send_json({
                        "type": "student_bus_location",
                        "student_id": student_id,
                        "bus_id": bus.id,
                        "latitude": tracker.last_latitude,
                        "longitude": tracker.last_longitude,
                        "timestamp": tracker.last_update_timestamp.isoformat() if tracker.last_update_timestamp else None
                    })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect_parent(websocket, student_id)
    finally:
        db.close()


async def websocket_device_gps(websocket: WebSocket, tracker_id: str):
    """WebSocket endpoint for GPS device to send location updates."""
    await websocket.accept()
    db = SessionLocal()
    try:
        # Verify tracker exists
        tracker = crud.get_gps_tracker_by_device_id(db, tracker_id)
        if not tracker:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        await manager.connect_device(websocket, tracker_id)
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "location_update":
                latitude = data.get("latitude")
                longitude = data.get("longitude")
                timestamp_str = data.get("timestamp")
                timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
                
                # Update tracker location
                crud.update_gps_tracker_location(db, tracker_id, latitude, longitude, timestamp)
                
                # Get bus associated with tracker
                bus = db.query(models.Bus).filter(models.Bus.gps_tracker_id == tracker.id).first()
                
                # Check if near school
                settings = crud.get_system_settings(db)
                is_near = False
                if settings and settings.school_latitude and settings.school_longitude:
                    is_near = gps_service.is_near_school(
                        latitude, longitude,
                        settings.school_latitude, settings.school_longitude
                    )
                
                # Create GPS log
                crud.create_gps_log(
                    db, tracker.id, latitude, longitude, timestamp,
                    bus_id=bus.id if bus else None, is_near_school=is_near
                )
                
                # Broadcast to admin and parents
                if bus:
                    await manager.broadcast_bus_location(bus.id, latitude, longitude, timestamp)
                    # Broadcast to parents of students on this bus
                    students = crud.get_students_by_bus(db, bus.id)
                    for student in students:
                        await manager.broadcast_student_location(
                            student.id, bus.id, latitude, longitude, timestamp
                        )
                
                await websocket.send_json({"status": "received"})
    except WebSocketDisconnect:
        await manager.disconnect_device(websocket, tracker_id)
    finally:
        db.close()


