"""
AI-powered question generator using rule-based NLP.
Generates MCQs and fill-in-the-blank questions from lesson content.
Lightweight design - works completely offline without heavy ML models.
"""

import re
import random
from typing import Dict, List, Optional, Tuple
import json


class QuestionGenerator:
    """Generate quiz questions from lesson content."""
    
    def __init__(self):
        # Question templates for different types
        self.mcq_templates = [
            "What is {concept}?",
            "Which of the following is true about {concept}?",
            "What is the {property} of {concept}?",
            "What happens when {condition}?",
            "Which statement best describes {concept}?",
        ]
        
        self.fill_blank_templates = [
            "{sentence_with_blank}",
            "The {property} of {concept} is _____.",
            "{concept} is measured in _____.",
        ]
        
        # Key phrases that often contain important concepts
        self.concept_markers = [
            "is defined as", "is called", "refers to", "means",
            "is the", "are the", "formula:", "unit:", "example:"
        ]
        
        # Units and their associated concepts (for generating distractors)
        self.common_units = {
            "m/s": ["km/h", "cm/s", "m/s²"],
            "m/s²": ["m/s", "km/h²", "cm/s²"],
            "Newton": ["Joule", "Watt", "Pascal"],
            "Joule": ["Newton", "Watt", "Pascal"],
            "Watt": ["Joule", "Newton", "Ampere"],
            "Hz": ["dB", "m/s", "Pa"],
            "kg": ["N", "g", "lb"],
        }
    
    def generate_from_lesson(
        self,
        lesson: Dict,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """
        Generate questions from a lesson.
        
        Args:
            lesson: Lesson dictionary with content
            num_questions: Number of questions to generate
            difficulty: easy, medium, or hard
        
        Returns:
            List of question dictionaries
        """
        questions = []
        
        # First, include pre-made questions from the lesson
        if "quiz_questions" in lesson:
            questions.extend(lesson["quiz_questions"][:num_questions])
        
        # If we need more questions, generate them
        if len(questions) < num_questions:
            generated = self._generate_from_content(
                lesson.get("content", {}),
                lesson.get("key_points", []),
                num_questions - len(questions),
                difficulty
            )
            questions.extend(generated)
        
        # Shuffle to mix pre-made and generated
        random.shuffle(questions)
        
        return questions[:num_questions]
    
    def _generate_from_content(
        self,
        content: Dict,
        key_points: List[str],
        num_needed: int,
        difficulty: str
    ) -> List[Dict]:
        """Generate questions from content sections and key points."""
        generated = []
        
        # Extract facts from key points
        for point in key_points:
            if len(generated) >= num_needed:
                break
            
            question = self._create_mcq_from_fact(point, difficulty)
            if question:
                generated.append(question)
        
        # Extract from content sections
        sections = content.get("sections", [])
        for section in sections:
            if len(generated) >= num_needed:
                break
            
            text = section.get("content", "")
            questions = self._extract_questions_from_text(text, difficulty)
            generated.extend(questions)
        
        return generated[:num_needed]
    
    def _create_mcq_from_fact(self, fact: str, difficulty: str) -> Optional[Dict]:
        """Create an MCQ from a factual statement."""
        # Look for patterns like "X is Y" or "X = Y"
        patterns = [
            r"(.+?)\s+is\s+(.+)",
            r"(.+?)\s*=\s*(.+)",
            r"(.+?)\s+equals\s+(.+)",
        ]
        
        for pattern in patterns:
            match = re.match(pattern, fact, re.IGNORECASE)
            if match:
                subject = match.group(1).strip()
                answer = match.group(2).strip()
                
                # Create question
                question_text = f"What is {subject}?"
                
                # Generate distractors
                distractors = self._generate_distractors(answer, 3)
                
                if len(distractors) == 3:
                    options = distractors + [answer]
                    random.shuffle(options)
                    correct_idx = options.index(answer)
                    
                    return {
                        "question": question_text,
                        "type": "mcq",
                        "options": options,
                        "correct": correct_idx,
                        "explanation": fact,
                        "generated": True
                    }
        
        return None
    
    def _extract_questions_from_text(
        self,
        text: str,
        difficulty: str
    ) -> List[Dict]:
        """Extract potential questions from text content."""
        questions = []
        
        # Find formula definitions
        formula_pattern = r"(\w+)\s*=\s*([^.\n]+)"
        for match in re.finditer(formula_pattern, text):
            var_name = match.group(1).strip()
            formula = match.group(2).strip()
            
            if len(var_name) <= 3:  # Likely a formula variable
                question = {
                    "question": f"What is the formula for {var_name}?",
                    "type": "mcq",
                    "options": [
                        formula,
                        self._modify_formula(formula),
                        self._modify_formula(formula),
                        self._modify_formula(formula)
                    ],
                    "correct": 0,
                    "explanation": f"{var_name} = {formula}",
                    "generated": True
                }
                random.shuffle(question["options"])
                question["correct"] = question["options"].index(formula)
                questions.append(question)
        
        return questions
    
    def _generate_distractors(self, correct: str, num: int) -> List[str]:
        """Generate plausible wrong answers."""
        distractors = []
        
        # Check if it's a unit
        for unit, alternatives in self.common_units.items():
            if unit in correct:
                for alt in alternatives:
                    if alt != correct and len(distractors) < num:
                        distractors.append(correct.replace(unit, alt))
        
        # Check if it's a number
        number_match = re.search(r'(\d+\.?\d*)', correct)
        if number_match and len(distractors) < num:
            num_val = float(number_match.group(1))
            variations = [num_val * 2, num_val / 2, num_val + 10, num_val - 5]
            for var in variations:
                if var > 0 and len(distractors) < num:
                    new_val = str(int(var)) if var == int(var) else f"{var:.1f}"
                    distractor = correct.replace(number_match.group(1), new_val)
                    if distractor != correct:
                        distractors.append(distractor)
        
        # Add generic distractors if needed
        generic = [
            "Cannot be determined",
            "None of the above",
            "All of the above",
            "Not applicable"
        ]
        while len(distractors) < num:
            g = random.choice(generic)
            if g not in distractors:
                distractors.append(g)
        
        return distractors[:num]
    
    def _modify_formula(self, formula: str) -> str:
        """Create a modified (wrong) version of a formula."""
        modifications = [
            lambda f: f.replace('×', '+'),
            lambda f: f.replace('/', '×'),
            lambda f: f.replace('+', '-'),
            lambda f: f.replace('²', '³'),
            lambda f: f + ' + 1',
            lambda f: '2' + f,
        ]
        
        mod_func = random.choice(modifications)
        modified = mod_func(formula)
        
        # If modification didn't change anything, append random suffix
        if modified == formula:
            modified = formula + random.choice([' - 1', ' + 2', '/2', '×2'])
        
        return modified
    
    def create_fill_blank(self, sentence: str, key_term: str) -> Dict:
        """Create a fill-in-the-blank question."""
        blank_sentence = sentence.replace(key_term, "_____")
        
        return {
            "question": blank_sentence,
            "type": "fill_blank",
            "answer": key_term,
            "hint": f"First letter: {key_term[0]}",
            "generated": True
        }


def grade_mcq(question: Dict, selected_index: int) -> Tuple[bool, str]:
    """
    Grade an MCQ answer.
    
    Returns:
        Tuple of (is_correct, explanation)
    """
    correct = question.get("correct", 0)
    is_correct = selected_index == correct
    explanation = question.get("explanation", "")
    
    if not explanation:
        correct_answer = question["options"][correct]
        explanation = f"The correct answer is: {correct_answer}"
    
    return is_correct, explanation


def grade_fill_blank(question: Dict, answer: str) -> Tuple[bool, str]:
    """
    Grade a fill-in-the-blank answer.
    
    Returns:
        Tuple of (is_correct, explanation)
    """
    correct_answer = question.get("answer", "")
    
    # Case-insensitive comparison, trim whitespace
    is_correct = answer.strip().lower() == correct_answer.strip().lower()
    
    explanation = f"The correct answer is: {correct_answer}"
    
    return is_correct, explanation


# Singleton instance for easy import
question_generator = QuestionGenerator()
