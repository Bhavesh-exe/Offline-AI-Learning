"""
Local storage utilities for offline data persistence.
Uses JSON files for lightweight storage without database dependencies.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Base data directory
DATA_DIR = Path(__file__).parent.parent / "data"
PROGRESS_FILE = DATA_DIR / "progress.json"
SYNC_QUEUE_FILE = DATA_DIR / "sync_queue.json"
LESSONS_DIR = DATA_DIR / "lessons"


def ensure_data_dirs():
    """Ensure all data directories exist."""
    DATA_DIR.mkdir(exist_ok=True)
    LESSONS_DIR.mkdir(exist_ok=True)


def load_json(filepath: Path) -> Dict:
    """Load JSON file, return empty dict if not exists."""
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def save_json(filepath: Path, data: Dict):
    """Save data to JSON file."""
    ensure_data_dirs()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


# ============ Progress Management ============

def get_progress() -> Dict:
    """Get all progress data."""
    default_progress = {
        "lessons_completed": [],
        "quiz_scores": [],
        "time_spent": {},
        "bookmarks": [],
        "achievements": [],
        "last_updated": None
    }
    progress = load_json(PROGRESS_FILE)
    # Merge with defaults to ensure all keys exist
    for key, value in default_progress.items():
        if key not in progress:
            progress[key] = value
    return progress


def save_progress(progress: Dict):
    """Save progress data."""
    progress["last_updated"] = datetime.now().isoformat()
    save_json(PROGRESS_FILE, progress)


def mark_lesson_complete(lesson_id: str):
    """Mark a lesson as completed."""
    progress = get_progress()
    if lesson_id not in progress["lessons_completed"]:
        progress["lessons_completed"].append(lesson_id)
        save_progress(progress)
        add_to_sync_queue("lesson_complete", {"lesson_id": lesson_id})


def record_quiz_score(quiz_data: Dict):
    """Record a quiz score."""
    progress = get_progress()
    quiz_data["timestamp"] = datetime.now().isoformat()
    progress["quiz_scores"].append(quiz_data)
    save_progress(progress)
    add_to_sync_queue("quiz_score", quiz_data)


def update_time_spent(lesson_id: str, seconds: int):
    """Update time spent on a lesson."""
    progress = get_progress()
    current = progress["time_spent"].get(lesson_id, 0)
    progress["time_spent"][lesson_id] = current + seconds
    save_progress(progress)


def add_bookmark(lesson_id: str, position: str):
    """Add a bookmark to a lesson."""
    progress = get_progress()
    bookmark = {
        "lesson_id": lesson_id,
        "position": position,
        "created_at": datetime.now().isoformat()
    }
    progress["bookmarks"].append(bookmark)
    save_progress(progress)


def unlock_achievement(achievement_id: str, title: str):
    """Unlock an achievement."""
    progress = get_progress()
    if achievement_id not in [a["id"] for a in progress["achievements"]]:
        progress["achievements"].append({
            "id": achievement_id,
            "title": title,
            "unlocked_at": datetime.now().isoformat()
        })
        save_progress(progress)


# ============ Lesson Management ============

def get_all_lessons() -> List[Dict]:
    """Get all available lessons."""
    ensure_data_dirs()
    lessons = []
    for file in LESSONS_DIR.glob("*.json"):
        lesson = load_json(file)
        if lesson:
            lesson["file"] = file.stem
            lessons.append(lesson)
    # Sort by order field if present
    lessons.sort(key=lambda x: x.get("order", 999))
    return lessons


def get_lesson(lesson_id: str) -> Optional[Dict]:
    """Get a specific lesson by ID."""
    filepath = LESSONS_DIR / f"{lesson_id}.json"
    return load_json(filepath) if filepath.exists() else None


# ============ Sync Queue Management ============

def add_to_sync_queue(action: str, data: Dict):
    """Add an item to the sync queue for later upload."""
    queue = load_json(SYNC_QUEUE_FILE)
    if "items" not in queue:
        queue["items"] = []
    
    queue["items"].append({
        "action": action,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "synced": False
    })
    save_json(SYNC_QUEUE_FILE, queue)


def get_pending_sync_items() -> List[Dict]:
    """Get items that need to be synced."""
    queue = load_json(SYNC_QUEUE_FILE)
    return [item for item in queue.get("items", []) if not item.get("synced")]


def mark_items_synced(count: int):
    """Mark the first N pending items as synced."""
    queue = load_json(SYNC_QUEUE_FILE)
    synced = 0
    for item in queue.get("items", []):
        if not item.get("synced") and synced < count:
            item["synced"] = True
            synced += 1
    save_json(SYNC_QUEUE_FILE, queue)


def clear_synced_items():
    """Remove synced items from the queue."""
    queue = load_json(SYNC_QUEUE_FILE)
    queue["items"] = [item for item in queue.get("items", []) if not item.get("synced")]
    save_json(SYNC_QUEUE_FILE, queue)


# ============ Statistics ============

def get_statistics() -> Dict:
    """Get learning statistics."""
    progress = get_progress()
    lessons = get_all_lessons()
    
    total_lessons = len(lessons)
    completed_lessons = len(progress["lessons_completed"])
    
    quiz_scores = progress["quiz_scores"]
    avg_score = 0
    if quiz_scores:
        avg_score = sum(q.get("score", 0) for q in quiz_scores) / len(quiz_scores)
    
    total_time = sum(progress["time_spent"].values())
    
    return {
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "completion_rate": (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
        "total_quizzes": len(quiz_scores),
        "average_score": round(avg_score, 1),
        "total_time_minutes": round(total_time / 60, 1),
        "achievements_count": len(progress["achievements"]),
        "bookmarks_count": len(progress["bookmarks"])
    }
