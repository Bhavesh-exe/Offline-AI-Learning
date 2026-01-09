"""
Quiz Generator Component for Streamlit.
Handles quiz creation, display, and grading.
"""

import streamlit as st
from typing import Dict, List, Optional
import random
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.storage import (
    get_all_lessons,
    get_lesson,
    record_quiz_score,
    get_progress,
    unlock_achievement
)
from ai.question_generator import question_generator, grade_mcq


def render_quiz_selector():
    """Render the quiz topic selector."""
    st.markdown("### 📝 Practice Quiz")
    st.markdown("Test your knowledge with auto-generated questions!")
    
    lessons = get_all_lessons()
    
    if not lessons:
        st.warning("No lessons available for quiz generation.")
        return None
    
    # Lesson selection
    lesson_options = {
        lesson.get("title", lesson.get("id", "Unknown")): lesson.get("id", lesson.get("file", ""))
        for lesson in lessons
    }
    
    selected_title = st.selectbox(
        "Select a topic:",
        options=list(lesson_options.keys()),
        key="quiz_topic_select"
    )
    
    selected_id = lesson_options.get(selected_title, "")
    
    # Quiz settings
    col1, col2 = st.columns(2)
    
    with col1:
        num_questions = st.slider(
            "Number of questions:",
            min_value=3,
            max_value=10,
            value=5,
            key="quiz_num_questions"
        )
    
    with col2:
        difficulty = st.selectbox(
            "Difficulty:",
            options=["Easy", "Medium", "Hard"],
            index=1,
            key="quiz_difficulty"
        )
    
    # Generate quiz button
    if st.button("🚀 Start Quiz", use_container_width=True, type="primary"):
        return {
            "lesson_id": selected_id,
            "num_questions": num_questions,
            "difficulty": difficulty.lower()
        }
    
    return None


def generate_quiz(lesson_id: str, num_questions: int = 5, difficulty: str = "medium") -> List[Dict]:
    """Generate quiz questions for a lesson."""
    lesson = get_lesson(lesson_id)
    
    if not lesson:
        return []
    
    questions = question_generator.generate_from_lesson(
        lesson,
        num_questions=num_questions,
        difficulty=difficulty
    )
    
    return questions


def render_quiz(questions: List[Dict], lesson_id: str):
    """Render the quiz interface."""
    if not questions:
        st.error("No questions available for this quiz.")
        return
    
    # Initialize quiz state
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "quiz_results" not in st.session_state:
        st.session_state.quiz_results = None
    
    lesson = get_lesson(lesson_id)
    lesson_title = lesson.get("title", "Quiz") if lesson else "Quiz"
    
    st.markdown(f"## 📝 Quiz: {lesson_title}")
    st.markdown(f"**{len(questions)} questions** • Answer all questions and submit")
    
    st.divider()
    
    # Display questions
    for i, q in enumerate(questions):
        render_question(i, q)
    
    st.divider()
    
    # Submit button
    if not st.session_state.quiz_submitted:
        col1, col2 = st.columns([3, 1])
        with col1:
            answered = sum(1 for i in range(len(questions)) if f"q_{i}" in st.session_state.quiz_answers)
            st.progress(answered / len(questions), text=f"{answered}/{len(questions)} answered")
        with col2:
            if st.button("Submit Quiz", type="primary", use_container_width=True):
                submit_quiz(questions, lesson_id)
    else:
        # Show results
        render_results(questions, lesson_id)


def render_question(index: int, question: Dict):
    """Render a single question."""
    q_text = question.get("question", f"Question {index + 1}")
    q_type = question.get("type", "mcq")
    
    st.markdown(f"**Q{index + 1}.** {q_text}")
    
    if q_type == "mcq":
        options = question.get("options", [])
        
        # Radio buttons for options
        selected = st.radio(
            "Select your answer:",
            options=options,
            key=f"q_{index}_radio",
            index=None,
            label_visibility="collapsed"
        )
        
        if selected is not None:
            st.session_state.quiz_answers[f"q_{index}"] = options.index(selected)
        
        # Show feedback if submitted
        if st.session_state.quiz_submitted:
            correct_idx = question.get("correct", 0)
            user_answer = st.session_state.quiz_answers.get(f"q_{index}", -1)
            
            if user_answer == correct_idx:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Incorrect. Correct answer: {options[correct_idx]}")
            
            explanation = question.get("explanation", "")
            if explanation:
                st.info(f"💡 {explanation}")
    
    elif q_type == "fill_blank":
        answer = st.text_input(
            "Your answer:",
            key=f"q_{index}_text",
            label_visibility="collapsed"
        )
        if answer:
            st.session_state.quiz_answers[f"q_{index}"] = answer
    
    st.write("")  # Spacing


def submit_quiz(questions: List[Dict], lesson_id: str):
    """Submit the quiz and calculate results."""
    st.session_state.quiz_submitted = True
    
    correct_count = 0
    total = len(questions)
    
    for i, q in enumerate(questions):
        user_answer = st.session_state.quiz_answers.get(f"q_{i}", -1)
        correct_answer = q.get("correct", 0)
        
        if user_answer == correct_answer:
            correct_count += 1
    
    score = (correct_count / total) * 100 if total > 0 else 0
    
    # Save quiz result
    quiz_data = {
        "lesson_id": lesson_id,
        "score": score,
        "correct": correct_count,
        "total": total
    }
    record_quiz_score(quiz_data)
    
    st.session_state.quiz_results = quiz_data
    
    # Check for achievements
    if score == 100:
        unlock_achievement("perfect_score", "Perfect Score! 🏆")
    
    progress = get_progress()
    if len(progress.get("quiz_scores", [])) >= 5:
        unlock_achievement("quiz_master", "Quiz Master - 5 quizzes completed! 📚")
    
    st.rerun()


def render_results(questions: List[Dict], lesson_id: str):
    """Render quiz results."""
    results = st.session_state.quiz_results
    
    if not results:
        return
    
    score = results.get("score", 0)
    correct = results.get("correct", 0)
    total = results.get("total", 0)
    
    # Score display
    if score >= 80:
        st.balloons()
        st.success(f"🎉 Excellent! Score: {score:.0f}% ({correct}/{total} correct)")
    elif score >= 60:
        st.info(f"👍 Good job! Score: {score:.0f}% ({correct}/{total} correct)")
    else:
        st.warning(f"📚 Keep practicing! Score: {score:.0f}% ({correct}/{total} correct)")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Retake Quiz", use_container_width=True):
            reset_quiz()
            st.rerun()
    
    with col2:
        if st.button("📚 Review Lesson", use_container_width=True):
            st.session_state.current_lesson = lesson_id
            st.session_state.page = "lessons"
            reset_quiz()
            st.rerun()
    
    with col3:
        if st.button("🏠 Back to Topics", use_container_width=True):
            reset_quiz()
            st.session_state.quiz_lesson = None
            st.rerun()


def reset_quiz():
    """Reset quiz state for a new attempt."""
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_results = None


def render_quiz_history():
    """Render past quiz scores."""
    progress = get_progress()
    scores = progress.get("quiz_scores", [])
    
    if not scores:
        st.info("No quiz history yet. Take a quiz to see your scores here!")
        return
    
    st.markdown("### 📊 Quiz History")
    
    # Recent scores
    recent = sorted(scores, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
    
    for score_data in recent:
        lesson_id = score_data.get("lesson_id", "Unknown")
        lesson = get_lesson(lesson_id)
        lesson_title = lesson.get("title", lesson_id) if lesson else lesson_id
        
        score = score_data.get("score", 0)
        correct = score_data.get("correct", 0)
        total = score_data.get("total", 0)
        
        # Score indicator
        if score >= 80:
            emoji = "🟢"
        elif score >= 60:
            emoji = "🟡"
        else:
            emoji = "🔴"
        
        st.markdown(f"{emoji} **{lesson_title}**: {score:.0f}% ({correct}/{total})")
