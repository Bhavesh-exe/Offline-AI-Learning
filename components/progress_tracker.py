"""
Progress Tracker Component.
Displays learning statistics, achievements, and study history.
"""

import streamlit as st
from typing import Dict, List
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import get_progress, get_statistics, get_all_lessons


def render_progress_dashboard():
    """Render the main progress dashboard."""
    st.markdown("### 📊 Your Progress")
    
    stats = get_statistics()
    progress = get_progress()
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📚 Lessons Completed",
            f"{stats['completed_lessons']}/{stats['total_lessons']}",
            f"{stats['completion_rate']:.0f}%"
        )
    
    with col2:
        st.metric(
            "📝 Quizzes Taken",
            stats['total_quizzes'],
            None
        )
    
    with col3:
        st.metric(
            "🎯 Average Score",
            f"{stats['average_score']:.0f}%",
            None
        )
    
    with col4:
        st.metric(
            "⏱️ Time Studied",
            f"{stats['total_time_minutes']:.0f} min",
            None
        )
    
    st.divider()
    
    # Progress tabs
    tab1, tab2, tab3 = st.tabs(["📈 Overview", "🏆 Achievements", "📋 History"])
    
    with tab1:
        render_progress_overview(stats, progress)
    
    with tab2:
        render_achievements(progress)
    
    with tab3:
        render_study_history(progress)


def render_progress_overview(stats: Dict, progress: Dict):
    """Render the progress overview with charts."""
    
    # Completion progress bar
    st.markdown("#### 📚 Course Completion")
    completion = stats['completion_rate'] / 100
    st.progress(completion, text=f"{stats['completed_lessons']}/{stats['total_lessons']} lessons completed")
    
    st.write("")
    
    # Lesson completion status
    st.markdown("#### Lesson Status")
    
    lessons = get_all_lessons()
    completed_ids = set(progress.get("lessons_completed", []))
    
    for lesson in lessons:
        lesson_id = lesson.get("id", lesson.get("file", ""))
        title = lesson.get("title", "Untitled")
        is_completed = lesson_id in completed_ids
        
        if is_completed:
            st.markdown(f"✅ ~~{title}~~")
        else:
            st.markdown(f"⬜ {title}")
    
    st.write("")
    
    # Quiz performance
    quiz_scores = progress.get("quiz_scores", [])
    if quiz_scores:
        st.markdown("#### 📝 Recent Quiz Scores")
        
        # Show last 5 quizzes
        recent = sorted(quiz_scores, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]
        
        for score_data in recent:
            score = score_data.get("score", 0)
            lesson_id = score_data.get("lesson_id", "Unknown")
            
            # Find lesson title
            lesson_title = lesson_id
            for lesson in lessons:
                if lesson.get("id") == lesson_id:
                    lesson_title = lesson.get("title", lesson_id)
                    break
            
            # Color code by score
            if score >= 80:
                color = "🟢"
            elif score >= 60:
                color = "🟡"
            else:
                color = "🔴"
            
            st.markdown(f"{color} **{lesson_title}**: {score:.0f}%")


def render_achievements(progress: Dict):
    """Render the achievements section."""
    st.markdown("#### 🏆 Your Achievements")
    
    achievements = progress.get("achievements", [])
    
    # Define all possible achievements
    all_achievements = [
        {
            "id": "first_lesson",
            "title": "First Steps",
            "description": "Complete your first lesson",
            "icon": "🎓"
        },
        {
            "id": "perfect_score",
            "title": "Perfect Score",
            "description": "Get 100% on a quiz",
            "icon": "🏆"
        },
        {
            "id": "quiz_master",
            "title": "Quiz Master",
            "description": "Complete 5 quizzes",
            "icon": "📚"
        },
        {
            "id": "dedicated_learner",
            "title": "Dedicated Learner",
            "description": "Study for 30 minutes",
            "icon": "⏰"
        },
        {
            "id": "bookworm",
            "title": "Bookworm",
            "description": "Complete all lessons",
            "icon": "📖"
        },
        {
            "id": "streak_3",
            "title": "On a Roll",
            "description": "3 day study streak",
            "icon": "🔥"
        }
    ]
    
    unlocked_ids = {a["id"] for a in achievements}
    
    col1, col2 = st.columns(2)
    
    for i, achievement in enumerate(all_achievements):
        is_unlocked = achievement["id"] in unlocked_ids
        
        with col1 if i % 2 == 0 else col2:
            if is_unlocked:
                st.success(f"{achievement['icon']} **{achievement['title']}**\n\n{achievement['description']}")
            else:
                st.info(f"🔒 **{achievement['title']}**\n\n{achievement['description']}")
    
    # Achievement progress
    st.write("")
    unlocked_count = len(unlocked_ids)
    total_achievements = len(all_achievements)
    st.progress(unlocked_count / total_achievements, 
                text=f"{unlocked_count}/{total_achievements} achievements unlocked")


def render_study_history(progress: Dict):
    """Render the study history."""
    st.markdown("#### 📋 Study History")
    
    # Lessons completed
    completed = progress.get("lessons_completed", [])
    quiz_scores = progress.get("quiz_scores", [])
    
    if not completed and not quiz_scores:
        st.info("Start learning to build your study history!")
        return
    
    # Timeline of activities
    activities = []
    
    for lesson_id in completed:
        activities.append({
            "type": "lesson",
            "id": lesson_id,
            "timestamp": None  # We don't track lesson completion time yet
        })
    
    for score in quiz_scores:
        activities.append({
            "type": "quiz",
            "id": score.get("lesson_id", ""),
            "score": score.get("score", 0),
            "timestamp": score.get("timestamp", "")
        })
    
    # Sort by timestamp (newest first)
    activities = sorted(
        activities,
        key=lambda x: x.get("timestamp", "") or "",
        reverse=True
    )
    
    lessons = get_all_lessons()
    lesson_map = {l.get("id"): l.get("title", l.get("id")) for l in lessons}
    
    for activity in activities[:20]:  # Show last 20 activities
        lesson_title = lesson_map.get(activity["id"], activity["id"])
        
        if activity["type"] == "lesson":
            st.markdown(f"📗 Completed: **{lesson_title}**")
        else:
            score = activity.get("score", 0)
            emoji = "🏆" if score >= 80 else "📝"
            st.markdown(f"{emoji} Quiz: **{lesson_title}** - {score:.0f}%")


def render_sync_status():
    """Render the sync status indicator."""
    try:
        from utils.sync_manager import get_sync_summary
        
        summary = get_sync_summary()
        
        st.markdown("#### 🔄 Sync Status")
        
        status_text = summary.get("status_text", "Unknown")
        st.info(status_text)
        
        if summary.get("can_sync"):
            if st.button("🔄 Sync Now", use_container_width=True):
                from utils.sync_manager import perform_sync
                with st.spinner("Syncing..."):
                    result = perform_sync()
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
        
        # Show pending items
        pending = summary.get("pending_count", 0)
        if pending > 0:
            st.caption(f"📤 {pending} items waiting to sync")
        
        # Last sync time
        last_sync = summary.get("last_sync")
        if last_sync:
            st.caption(f"Last synced: {last_sync}")
            
    except ImportError:
        st.warning("Sync manager not available")
