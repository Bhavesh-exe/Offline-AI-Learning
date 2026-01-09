"""
Study Tools Component.
Provides summaries, concept maps, and text-to-speech features.
"""

import streamlit as st
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import get_all_lessons, get_lesson
from ai.summarizer import summarizer


def render_study_tools():
    """Render the main study tools interface."""
    st.markdown("### 🛠️ Study Tools")
    st.markdown("Enhance your learning with AI-powered study aids!")
    
    # Tool selection tabs
    tab1, tab2, tab3 = st.tabs(["📝 Summary", "🗺️ Concept Map", "🔊 Audio"])
    
    with tab1:
        render_summary_tool()
    
    with tab2:
        render_concept_map()
    
    with tab3:
        render_audio_tool()


def render_summary_tool():
    """Render the summary generation tool."""
    st.markdown("#### Generate Key Points Summary")
    
    lessons = get_all_lessons()
    
    if not lessons:
        st.warning("No lessons available.")
        return
    
    # Lesson selection
    lesson_options = {
        lesson.get("title", lesson.get("id", "Unknown")): lesson.get("id", lesson.get("file", ""))
        for lesson in lessons
    }
    
    selected_title = st.selectbox(
        "Select a lesson:",
        options=list(lesson_options.keys()),
        key="summary_lesson_select"
    )
    
    selected_id = lesson_options.get(selected_title, "")
    
    # Summary options
    num_points = st.slider(
        "Number of key points:",
        min_value=3,
        max_value=10,
        value=5,
        key="summary_num_points"
    )
    
    if st.button("📝 Generate Summary", type="primary", use_container_width=True):
        lesson = get_lesson(selected_id)
        
        if lesson:
            with st.spinner("Analyzing lesson content..."):
                key_points = summarizer.extract_key_points(lesson, max_points=num_points)
                
                st.markdown("#### 📌 Key Points")
                for i, point in enumerate(key_points, 1):
                    st.success(f"{i}. {point}")
                
                # Generate outline
                outline = summarizer.generate_topic_outline(lesson)
                
                st.markdown("#### 📑 Topic Outline")
                for topic in outline.get("topics", []):
                    st.markdown(f"**{topic.get('name', '')}**")
                    for concept in topic.get("key_concepts", []):
                        st.markdown(f"  • {concept}")


def render_concept_map():
    """Render the concept map generator."""
    st.markdown("#### Visual Concept Map")
    
    lessons = get_all_lessons()
    
    if not lessons:
        st.warning("No lessons available.")
        return
    
    # Lesson selection
    lesson_options = {
        lesson.get("title", lesson.get("id", "Unknown")): lesson.get("id", lesson.get("file", ""))
        for lesson in lessons
    }
    
    selected_title = st.selectbox(
        "Select a lesson:",
        options=list(lesson_options.keys()),
        key="concept_map_lesson_select"
    )
    
    selected_id = lesson_options.get(selected_title, "")
    
    if st.button("🗺️ Generate Concept Map", type="primary", use_container_width=True):
        lesson = get_lesson(selected_id)
        
        if lesson:
            with st.spinner("Creating concept map..."):
                # Generate mermaid diagram
                mermaid_code = generate_mermaid_map(lesson)
                
                st.markdown("#### Concept Map")
                st.markdown(f"""
```mermaid
{mermaid_code}
```
""")
                
                # Also show as text hierarchy for fallback
                st.markdown("#### Topic Hierarchy")
                render_text_hierarchy(lesson)


def generate_mermaid_map(lesson: Dict) -> str:
    """Generate a Mermaid flowchart from lesson content."""
    title = lesson.get("title", "Topic").replace(" ", "_").replace("'", "")
    
    lines = [f"graph TD"]
    lines.append(f'    A["{lesson.get("title", "Topic")}"]')
    
    content = lesson.get("content", {})
    sections = content.get("sections", [])
    
    for i, section in enumerate(sections):
        section_title = section.get("title", f"Section {i+1}")
        node_id = f"B{i}"
        # Clean title for mermaid
        clean_title = section_title.replace('"', "'").replace("(", "[").replace(")", "]")
        lines.append(f'    A --> {node_id}["{clean_title}"]')
        
        # Add key concepts as sub-nodes
        key_concepts = extract_section_concepts(section.get("content", ""))
        for j, concept in enumerate(key_concepts[:3]):  # Limit to 3 per section
            concept_id = f"C{i}_{j}"
            clean_concept = concept.replace('"', "'").replace("(", "[").replace(")", "]")
            lines.append(f'    {node_id} --> {concept_id}["{clean_concept}"]')
    
    return "\n".join(lines)


def extract_section_concepts(text: str) -> List[str]:
    """Extract key concepts from section text."""
    import re
    
    concepts = []
    
    # Look for bold text
    bold_matches = re.findall(r'\*\*([^*]+)\*\*', text)
    concepts.extend(bold_matches[:5])
    
    # Look for formulas
    formula_matches = re.findall(r'(\w+)\s*=\s*([^.\n]+)', text)
    for var, formula in formula_matches[:3]:
        if len(var) <= 3:
            concepts.append(f"{var} = {formula.strip()[:20]}")
    
    return concepts[:5]


def render_text_hierarchy(lesson: Dict):
    """Render a text-based concept hierarchy."""
    title = lesson.get("title", "Topic")
    st.markdown(f"**{title}**")
    
    content = lesson.get("content", {})
    sections = content.get("sections", [])
    
    for section in sections:
        section_title = section.get("title", "Section")
        st.markdown(f"├── 📂 {section_title}")
        
        # Show key points
        key_points = lesson.get("key_points", [])
        for point in key_points[:2]:
            if section_title.lower() in point.lower():
                st.markdown(f"│   ├── 📄 {point[:50]}...")


def render_audio_tool():
    """Render the text-to-speech tool."""
    st.markdown("#### 🔊 Listen to Lessons")
    st.markdown("Convert lessons to audio for hands-free learning!")
    
    lessons = get_all_lessons()
    
    if not lessons:
        st.warning("No lessons available.")
        return
    
    # Lesson selection
    lesson_options = {
        lesson.get("title", lesson.get("id", "Unknown")): lesson.get("id", lesson.get("file", ""))
        for lesson in lessons
    }
    
    selected_title = st.selectbox(
        "Select a lesson:",
        options=list(lesson_options.keys()),
        key="audio_lesson_select"
    )
    
    selected_id = lesson_options.get(selected_title, "")
    
    # TTS Settings
    st.markdown("##### Voice Settings")
    col1, col2 = st.columns(2)
    
    with col1:
        speech_rate = st.slider(
            "Speed:",
            min_value=100,
            max_value=250,
            value=150,
            step=10,
            key="tts_rate"
        )
    
    with col2:
        volume = st.slider(
            "Volume:",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.1,
            key="tts_volume"
        )
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔊 Read Aloud", type="primary", use_container_width=True):
            lesson = get_lesson(selected_id)
            if lesson:
                read_lesson_aloud(lesson, speech_rate, volume)
    
    with col2:
        if st.button("⏹️ Stop", use_container_width=True):
            stop_speech()
    
    # Content preview
    lesson = get_lesson(selected_id)
    if lesson:
        with st.expander("📄 Preview Content"):
            text = extract_lesson_text(lesson)
            st.text_area("Text content:", value=text[:1000] + "..." if len(text) > 1000 else text, height=200, disabled=True)


def read_lesson_aloud(lesson: Dict, rate: int = 150, volume: float = 1.0):
    """Read a lesson using text-to-speech."""
    try:
        from ai.tts_engine import tts_engine
        
        # Configure TTS
        tts_engine.set_rate(rate)
        tts_engine.set_volume(volume)
        
        # Extract text
        text = extract_lesson_text(lesson)
        
        # Limit text length for performance
        if len(text) > 3000:
            text = text[:3000] + "... End of preview."
        
        # Speak
        tts_engine.speak(text)
        st.success("🔊 Playing audio... Click 'Stop' to cancel.")
        
    except ImportError:
        st.error("Text-to-speech is not available. Install pyttsx3: `pip install pyttsx3`")
    except Exception as e:
        st.error(f"TTS Error: {e}")


def stop_speech():
    """Stop any ongoing speech."""
    try:
        from ai.tts_engine import tts_engine
        tts_engine.stop()
        st.info("⏹️ Audio stopped.")
    except Exception:
        pass


def extract_lesson_text(lesson: Dict) -> str:
    """Extract readable text from a lesson."""
    parts = []
    
    # Title
    parts.append(f"Lesson: {lesson.get('title', 'Untitled')}")
    parts.append("")
    
    # Learning objectives
    objectives = lesson.get("learning_objectives", [])
    if objectives:
        parts.append("Learning Objectives:")
        for obj in objectives:
            parts.append(f"  - {obj}")
        parts.append("")
    
    # Content sections
    content = lesson.get("content", {})
    for section in content.get("sections", []):
        title = section.get("title", "")
        text = section.get("content", "")
        
        parts.append(f"{title}:")
        # Clean markdown formatting
        clean_text = text.replace("**", "").replace("*", "").replace("#", "")
        parts.append(clean_text)
        parts.append("")
    
    # Key points
    key_points = lesson.get("key_points", [])
    if key_points:
        parts.append("Key Points:")
        for point in key_points:
            parts.append(f"  - {point}")
    
    return "\n".join(parts)
