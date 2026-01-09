"""
Text summarization using extractive methods.
Uses TextRank algorithm for key sentence extraction.
Completely offline - no external API calls needed.
"""

import re
from typing import Dict, List, Tuple
from collections import defaultdict
import math


class TextSummarizer:
    """Extractive text summarizer using TextRank algorithm."""
    
    def __init__(self):
        # Common stop words to filter out
        self.stop_words = set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them',
            'their', 'we', 'us', 'our', 'he', 'him', 'his', 'she', 'her',
            'you', 'your', 'i', 'me', 'my', 'what', 'which', 'who', 'whom',
            'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'same', 'so', 'than', 'too', 'very', 'just', 'also'
        ])
        
        # Important markers that boost sentence importance
        self.importance_markers = [
            'important', 'key', 'main', 'primary', 'essential', 'fundamental',
            'formula', 'definition', 'defined as', 'means', 'example',
            'note', 'remember', 'always', 'never', 'must'
        ]
    
    def summarize(
        self,
        text: str,
        num_sentences: int = 5,
        as_bullets: bool = True
    ) -> str:
        """
        Generate a summary of the text.
        
        Args:
            text: Input text to summarize
            num_sentences: Number of sentences in summary
            as_bullets: Return as bullet points if True
        
        Returns:
            Summary string
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        if len(sentences) <= num_sentences:
            if as_bullets:
                return '\n'.join(f'• {s.strip()}' for s in sentences)
            return ' '.join(sentences)
        
        # Calculate sentence scores using TextRank
        scores = self._calculate_sentence_scores(sentences)
        
        # Get top sentences while maintaining order
        ranked = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)
        top_indices = sorted(ranked[:num_sentences])
        
        top_sentences = [sentences[i].strip() for i in top_indices]
        
        if as_bullets:
            return '\n'.join(f'• {s}' for s in top_sentences)
        return ' '.join(top_sentences)
    
    def extract_key_points(self, lesson: Dict, max_points: int = 7) -> List[str]:
        """
        Extract key points from a lesson.
        
        Args:
            lesson: Lesson dictionary with content
            max_points: Maximum number of key points
        
        Returns:
            List of key point strings
        """
        # First check if lesson has pre-defined key points
        if 'key_points' in lesson and lesson['key_points']:
            return lesson['key_points'][:max_points]
        
        # Otherwise, extract from content
        all_text = self._extract_all_text(lesson)
        
        # Get summary sentences
        sentences = self._split_sentences(all_text)
        scores = self._calculate_sentence_scores(sentences)
        
        # Boost sentences with importance markers
        for i, sent in enumerate(sentences):
            sent_lower = sent.lower()
            for marker in self.importance_markers:
                if marker in sent_lower:
                    scores[i] *= 1.5
                    break
        
        # Get top sentences
        ranked = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)
        
        key_points = []
        for i in ranked[:max_points]:
            point = sentences[i].strip()
            # Clean up the point
            point = self._clean_key_point(point)
            if point and len(point) > 10:
                key_points.append(point)
        
        return key_points
    
    def generate_topic_outline(self, lesson: Dict) -> Dict:
        """
        Generate a topic outline/structure from a lesson.
        
        Returns:
            Dictionary with main topic and subtopics
        """
        outline = {
            'title': lesson.get('title', 'Untitled'),
            'topics': []
        }
        
        content = lesson.get('content', {})
        sections = content.get('sections', [])
        
        for section in sections:
            topic = {
                'name': section.get('title', ''),
                'key_concepts': []
            }
            
            # Extract key concepts from section content
            text = section.get('content', '')
            concepts = self._extract_concepts(text)
            topic['key_concepts'] = concepts[:5]
            
            outline['topics'].append(topic)
        
        return outline
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle common abbreviations
        text = re.sub(r'(\d+)\.\s*(\d+)', r'\1<DOT>\2', text)  # Decimals
        text = re.sub(r'(Mr|Mrs|Dr|Prof|vs|etc|e\.g|i\.e)\.', r'\1<ABBR>', text)
        
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        
        # Restore abbreviations and decimals
        sentences = [s.replace('<DOT>', '.').replace('<ABBR>', '.').strip() 
                     for s in sentences if s.strip()]
        
        return sentences
    
    def _calculate_sentence_scores(self, sentences: List[str]) -> List[float]:
        """Calculate importance scores using simplified TextRank."""
        n = len(sentences)
        if n == 0:
            return []
        
        # Build word frequency map
        word_freq = defaultdict(int)
        sentence_words = []
        
        for sent in sentences:
            words = self._tokenize(sent)
            sentence_words.append(set(words))
            for word in words:
                word_freq[word] += 1
        
        # Calculate sentence similarity matrix
        similarity = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._sentence_similarity(
                    sentence_words[i],
                    sentence_words[j],
                    word_freq
                )
                similarity[i][j] = sim
                similarity[j][i] = sim
        
        # Run PageRank-style iteration
        scores = [1.0 / n] * n
        damping = 0.85
        
        for _ in range(10):  # 10 iterations usually enough
            new_scores = []
            for i in range(n):
                rank = (1 - damping) / n
                for j in range(n):
                    if i != j:
                        # Sum of similarities to other sentences
                        out_sum = sum(similarity[j])
                        if out_sum > 0:
                            rank += damping * (similarity[j][i] / out_sum) * scores[j]
                new_scores.append(rank)
            scores = new_scores
        
        return scores
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words, removing stop words."""
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in self.stop_words and len(w) > 2]
    
    def _sentence_similarity(
        self,
        words1: set,
        words2: set,
        word_freq: Dict[str, int]
    ) -> float:
        """Calculate similarity between two sentences."""
        if not words1 or not words2:
            return 0.0
        
        # Use weighted Jaccard similarity
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        
        # Weight by inverse document frequency
        weighted_intersection = sum(1 / (1 + word_freq.get(w, 1)) for w in intersection)
        weighted_union = sum(1 / (1 + word_freq.get(w, 1)) for w in union)
        
        return weighted_intersection / weighted_union if weighted_union > 0 else 0.0
    
    def _extract_all_text(self, lesson: Dict) -> str:
        """Extract all text content from a lesson."""
        texts = []
        
        content = lesson.get('content', {})
        for section in content.get('sections', []):
            texts.append(section.get('content', ''))
        
        return ' '.join(texts)
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concept terms from text."""
        concepts = []
        
        # Look for defined terms
        patterns = [
            r'\*\*([^*]+)\*\*',  # Bold text
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Title case phrases
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                term = match.strip()
                if len(term) > 2 and term.lower() not in self.stop_words:
                    if term not in concepts:
                        concepts.append(term)
        
        return concepts
    
    def _clean_key_point(self, text: str) -> str:
        """Clean up a key point for display."""
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # Remove bullet points
        text = re.sub(r'^[•\-\*]\s*', '', text)
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        return text.strip()


# Singleton instance
summarizer = TextSummarizer()
