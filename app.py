"""
AI Learning Platform - Main Application
Offline-capable educational app for rural students.

Features:
- Offline content access
- AI-powered quiz generation
- Study tools (summaries, concept maps, TTS)
- Progress tracking
- Smart sync

Run with: streamlit run app.py
"""

import streamlit as st
from pathlib import Path
import sys

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import components
from components.content_viewer import render_lesson_list, render_lesson_content
from components.quiz_generator import (
    render_quiz_selector, 
    generate_quiz, 
    render_quiz,
    render_quiz_history
)
from components.study_tools import render_study_tools
from components.progress_tracker import render_progress_dashboard, render_sync_status

# Import utilities
from utils.storage import ensure_data_dirs, get_statistics


def setup_page():
    """Configure Streamlit page settings and PWA meta tags."""
    st.set_page_config(
        page_title="AI Learning Platform",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "# AI Learning Platform\nOffline-capable education for everyone!"
        }
    )
    
    # Inject PWA meta tags and service worker registration
    pwa_html = """
    <head>
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#6c63ff">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="AI Learn">
        <link rel="apple-touch-icon" href="/static/icons/icon-192.png">
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    </head>
    
    <script>
        // Register Service Worker for offline capability
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {
                        console.log('SW registered:', registration.scope);
                    })
                    .catch(error => {
                        console.log('SW registration failed:', error);
                    });
            });
        }
        
        // Detect online/offline status
        function updateOnlineStatus() {
            const indicator = document.getElementById('offline-indicator');
            if (indicator) {
                if (navigator.onLine) {
                    indicator.style.display = 'none';
                } else {
                    indicator.style.display = 'block';
                }
            }
        }
        
        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        
        // PWA Install prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            // Show install button in UI if needed
        });
    </script>
    
    <div id="offline-indicator" style="display:none; position:fixed; top:0; left:0; right:0; 
         background:#ffc107; color:#333; padding:8px; text-align:center; font-weight:600; z-index:9999;">
        📴 You are offline - All features still work!
    </div>
    """
    st.markdown(pwa_html, unsafe_allow_html=True)
    
    # Load custom CSS
    css_path = Path(__file__).parent / "static" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        # App branding
        st.markdown("# 📚 AI Learn")
        st.markdown("*Offline Learning Platform*")
        
        st.divider()
        
        # Navigation buttons
        if st.button("📖 Lessons", use_container_width=True, 
                    type="primary" if st.session_state.get("page") == "lessons" else "secondary"):
            st.session_state.page = "lessons"
            st.session_state.current_lesson = None
            st.rerun()
        
        if st.button("📝 Quiz", use_container_width=True,
                    type="primary" if st.session_state.get("page") == "quiz" else "secondary"):
            st.session_state.page = "quiz"
            st.rerun()
        
        if st.button("🛠️ Study Tools", use_container_width=True,
                    type="primary" if st.session_state.get("page") == "tools" else "secondary"):
            st.session_state.page = "tools"
            st.rerun()
        
        if st.button("📊 Progress", use_container_width=True,
                    type="primary" if st.session_state.get("page") == "progress" else "secondary"):
            st.session_state.page = "progress"
            st.rerun()
        
        st.divider()
        
        # Quick stats
        stats = get_statistics()
        st.markdown("### 📈 Quick Stats")
        st.metric("Lessons Done", f"{stats['completed_lessons']}/{stats['total_lessons']}")
        st.metric("Avg Score", f"{stats['average_score']:.0f}%")
        
        st.divider()
        
        # Sync status
        render_sync_status()
        
        st.divider()
        
        # Footer
        st.caption("🌐 Works Offline!")
        st.caption("Made for Rural Students 💚")


def render_main_content():
    """Render the main content area based on current page."""
    page = st.session_state.get("page", "lessons")
    
    if page == "lessons":
        render_lessons_page()
    
    elif page == "quiz":
        render_quiz_page()
    
    elif page == "tools":
        render_study_tools()
    
    elif page == "progress":
        render_progress_dashboard()


def render_lessons_page():
    """Render the lessons page."""
    current_lesson = st.session_state.get("current_lesson")
    
    if current_lesson:
        # Show back button
        if st.button("← Back to Lessons"):
            st.session_state.current_lesson = None
            st.rerun()
        
        # Render lesson content
        render_lesson_content(current_lesson)
    else:
        # Show lesson list
        st.markdown("## 📖 Available Lessons")
        st.markdown("Select a lesson to start learning!")
        
        selected = render_lesson_list()
        
        if selected:
            st.session_state.current_lesson = selected
            st.rerun()


def render_quiz_page():
    """Render the quiz page."""
    # Check if we're in the middle of a quiz
    if "quiz_questions" in st.session_state and st.session_state.quiz_questions:
        lesson_id = st.session_state.get("quiz_lesson", "")
        render_quiz(st.session_state.quiz_questions, lesson_id)
    else:
        # Quiz selector
        quiz_config = render_quiz_selector()
        
        if quiz_config:
            # Generate quiz
            questions = generate_quiz(
                quiz_config["lesson_id"],
                quiz_config["num_questions"],
                quiz_config["difficulty"]
            )
            
            if questions:
                st.session_state.quiz_questions = questions
                st.session_state.quiz_lesson = quiz_config["lesson_id"]
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()
            else:
                st.error("Could not generate quiz. Please try another topic.")
        
        st.divider()
        
        # Show quiz history
        render_quiz_history()


def main():
    """Main application entry point."""
    # Ensure data directories exist
    ensure_data_dirs()
    
    # Setup page config and PWA
    setup_page()
    
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "lessons"
    
    # Render UI
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()
