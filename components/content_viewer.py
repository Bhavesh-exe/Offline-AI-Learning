"""
Content Viewer Component for displaying lessons.
Handles lesson rendering, navigation, and bookmarking.
"""

import streamlit as st
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import (
    get_all_lessons,
    get_lesson,
    get_progress,
    mark_lesson_complete,
    add_bookmark,
    update_time_spent
)


def render_lesson_list():
    """Render the list of available lessons."""
    lessons = get_all_lessons()
    progress = get_progress()
    completed = set(progress.get("lessons_completed", []))
    
    st.markdown("### 📚 Available Lessons")
    
    if not lessons:
        st.warning("No lessons available yet. Add lesson files to data/lessons/")
        return None
    
    # Create lesson cards
    selected_lesson = None
    
    for lesson in lessons:
        lesson_id = lesson.get("id", lesson.get("file", ""))
        title = lesson.get("title", "Untitled")
        difficulty = lesson.get("difficulty", "intermediate")
        time_mins = lesson.get("estimated_time_minutes", 15)
        is_completed = lesson_id in completed
        
        # Difficulty badge color
        diff_colors = {
            "beginner": "🟢",
            "intermediate": "🟡",
            "advanced": "🔴"
        }
        diff_emoji = diff_colors.get(difficulty, "🟡")
        
        # Completion badge
        status_emoji = "✅" if is_completed else "📖"
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if st.button(
                f"{status_emoji} {title}",
                key=f"lesson_{lesson_id}",
                use_container_width=True
            ):
                selected_lesson = lesson_id
        
        with col2:
            st.caption(f"{diff_emoji} {time_mins}min")
    
    return selected_lesson


def render_lesson_content(lesson_id: str):
    """Render the full content of a lesson."""
    lesson = get_lesson(lesson_id)
    
    if not lesson:
        st.error(f"Lesson '{lesson_id}' not found")
        return
    
    # Header
    st.markdown(f"# {lesson.get('title', 'Untitled')}")
    
    # Metadata bar
    cols = st.columns(4)
    with cols[0]:
        st.metric("Subject", lesson.get("subject", "General"))
    with cols[1]:
        st.metric("Difficulty", lesson.get("difficulty", "Medium").title())
    with cols[2]:
        st.metric("Duration", f"{lesson.get('estimated_time_minutes', 15)} min")
    with cols[3]:
        progress = get_progress()
        is_completed = lesson_id in progress.get("lessons_completed", [])
        st.metric("Status", "✅ Done" if is_completed else "📖 In Progress")
    
    st.divider()
    
    # Learning objectives
    objectives = lesson.get("learning_objectives", [])
    if objectives:
        with st.expander("🎯 Learning Objectives", expanded=True):
            for obj in objectives:
                st.markdown(f"• {obj}")
    
    st.divider()
    
    # Main content sections
    content = lesson.get("content", {})
    sections = content.get("sections", [])
    
    for i, section in enumerate(sections):
        section_title = section.get("title", f"Section {i+1}")
        section_type = section.get("type", "text")
        section_content = section.get("content", "")
        
        st.markdown(f"### {section_title}")
        
        if section_type == "formula":
            # Render formulas in a special box
            st.code(section_content, language=None)
        else:
            # Render regular text with markdown support
            st.markdown(section_content)
        
        st.write("")  # Spacing
    
    st.divider()
    
    # Key Points Summary
    key_points = lesson.get("key_points", [])
    if key_points:
        st.markdown("### 📌 Key Points to Remember")
        for point in key_points:
            st.success(f"✓ {point}")
    
    # Action buttons
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Mark as Complete", use_container_width=True):
            mark_lesson_complete(lesson_id)
            st.success("Lesson marked as complete!")
            st.rerun()
    
    with col2:
        if st.button("🔖 Bookmark", use_container_width=True):
            add_bookmark(lesson_id, "start")
            st.success("Bookmark added!")
    
    with col3:
        if st.button("📝 Take Quiz", use_container_width=True):
            st.session_state.quiz_lesson = lesson_id
            st.session_state.page = "quiz"
            st.rerun()


def render_lesson_with_tts(lesson_id: str):
    """Render lesson with text-to-speech controls."""
    lesson = get_lesson(lesson_id)
    
    if not lesson:
        st.error(f"Lesson '{lesson_id}' not found")
        return
    
    # TTS Controls in sidebar
    with st.sidebar:
        st.markdown("### 🔊 Read Aloud")
        
        if st.button("🔊 Read Lesson", use_container_width=True):
            try:
                from ai.tts_engine import tts_engine
                
                # Combine all text content
                full_text = f"Lesson: {lesson.get('title', '')}. "
                
                content = lesson.get("content", {})
                for section in content.get("sections", []):
                    full_text += f"{section.get('title', '')}. "
                    full_text += section.get("content", "") + " "
                
                # Speak in background
                tts_engine.speak(full_text[:2000])  # Limit to 2000 chars
                st.success("Speaking...")
            except Exception as e:
                st.error(f"TTS not available: {e}")
        
        if st.button("⏹️ Stop", use_container_width=True):
            try:
                from ai.tts_engine import tts_engine
                tts_engine.stop()
            except Exception:
                pass
    
    # Render the lesson content
    render_lesson_content(lesson_id)


def get_lesson_text_for_tts(lesson_id: str) -> str:
    """Extract text from lesson for TTS."""
    lesson = get_lesson(lesson_id)
    if not lesson:
        return ""
    
    text_parts = [lesson.get("title", "")]
    
    content = lesson.get("content", {})
    for section in content.get("sections", []):
        text_parts.append(section.get("title", ""))
        text_parts.append(section.get("content", ""))
    
    return " ".join(text_parts)
