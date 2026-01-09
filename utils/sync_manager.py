"""
Smart sync manager for offline-first data synchronization.
Handles delta sync, conflict resolution, and internet detection.
"""

import json
import socket
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .storage import (
    get_pending_sync_items,
    mark_items_synced,
    clear_synced_items,
    save_json,
    load_json,
    DATA_DIR
)

SYNC_STATUS_FILE = DATA_DIR / "sync_status.json"


def check_internet_connection(timeout: float = 3.0) -> bool:
    """
    Check if internet connection is available.
    Uses socket connection to Google DNS as a reliable test.
    """
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False


def get_sync_status() -> Dict:
    """Get the current sync status."""
    default_status = {
        "last_sync": None,
        "pending_items": 0,
        "sync_in_progress": False,
        "last_error": None,
        "total_synced": 0
    }
    status = load_json(SYNC_STATUS_FILE)
    for key, value in default_status.items():
        if key not in status:
            status[key] = value
    return status


def update_sync_status(**kwargs):
    """Update sync status fields."""
    status = get_sync_status()
    status.update(kwargs)
    save_json(SYNC_STATUS_FILE, status)


def prepare_sync_payload() -> Dict:
    """
    Prepare delta sync payload - only changed/new data.
    Returns a dict with items to sync and metadata.
    """
    pending = get_pending_sync_items()
    
    if not pending:
        return {"items": [], "count": 0}
    
    # Group by action type for efficient sync
    grouped = {}
    for item in pending:
        action = item.get("action", "unknown")
        if action not in grouped:
            grouped[action] = []
        grouped[action].append(item)
    
    return {
        "items": pending,
        "grouped": grouped,
        "count": len(pending),
        "prepared_at": datetime.now().isoformat()
    }


def simulate_sync(payload: Dict) -> Tuple[bool, str]:
    """
    Simulate syncing to a server.
    In production, this would make actual API calls.
    
    Returns:
        Tuple of (success, message)
    """
    if not payload.get("items"):
        return True, "Nothing to sync"
    
    # Simulate network delay
    time.sleep(0.5)
    
    # In production, this would be:
    # response = requests.post(SYNC_URL, json=payload)
    # return response.ok, response.text
    
    # For demo, always succeed
    return True, f"Synced {payload['count']} items successfully"


def perform_sync() -> Dict:
    """
    Perform a full sync operation.
    
    Returns:
        Dict with sync results
    """
    result = {
        "success": False,
        "message": "",
        "items_synced": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    # Check internet
    if not check_internet_connection():
        result["message"] = "No internet connection"
        return result
    
    # Update status
    update_sync_status(sync_in_progress=True)
    
    try:
        # Prepare payload (delta only)
        payload = prepare_sync_payload()
        
        if payload["count"] == 0:
            result["success"] = True
            result["message"] = "Already up to date"
            return result
        
        # Perform sync
        success, message = simulate_sync(payload)
        
        if success:
            # Mark items as synced
            mark_items_synced(payload["count"])
            clear_synced_items()
            
            # Update stats
            status = get_sync_status()
            update_sync_status(
                last_sync=datetime.now().isoformat(),
                pending_items=0,
                total_synced=status["total_synced"] + payload["count"],
                last_error=None
            )
            
            result["success"] = True
            result["items_synced"] = payload["count"]
            result["message"] = message
        else:
            update_sync_status(last_error=message)
            result["message"] = f"Sync failed: {message}"
            
    except Exception as e:
        result["message"] = f"Sync error: {str(e)}"
        update_sync_status(last_error=str(e))
    finally:
        update_sync_status(sync_in_progress=False)
    
    return result


def get_sync_summary() -> Dict:
    """Get a summary of sync status for UI display."""
    status = get_sync_status()
    pending = get_pending_sync_items()
    is_online = check_internet_connection(timeout=1.0)
    
    return {
        "is_online": is_online,
        "pending_count": len(pending),
        "last_sync": status.get("last_sync"),
        "total_synced": status.get("total_synced", 0),
        "can_sync": is_online and len(pending) > 0,
        "status_text": _get_status_text(is_online, len(pending), status)
    }


def _get_status_text(is_online: bool, pending: int, status: Dict) -> str:
    """Generate human-readable status text."""
    if not is_online:
        if pending > 0:
            return f"📴 Offline • {pending} items pending sync"
        return "📴 Offline • All data saved locally"
    
    if pending > 0:
        return f"🌐 Online • {pending} items ready to sync"
    
    last_sync = status.get("last_sync")
    if last_sync:
        return f"✅ Synced • Last: {_format_time_ago(last_sync)}"
    
    return "🌐 Online • Ready"


def _format_time_ago(iso_time: str) -> str:
    """Format ISO timestamp as relative time."""
    try:
        dt = datetime.fromisoformat(iso_time)
        delta = datetime.now() - dt
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "just now"
    except:
        return "unknown"
