"""
Text-to-Speech engine using pyttsx3.
Works completely offline without internet connection.
"""

import threading
from typing import Optional, Callable
import queue


class TTSEngine:
    """
    Offline Text-to-Speech engine using pyttsx3.
    Thread-safe implementation for use with Streamlit.
    """
    
    def __init__(self):
        self._engine = None
        self._lock = threading.Lock()
        self._speech_queue = queue.Queue()
        self._is_speaking = False
        self._current_voice = None
        self._rate = 150  # Default speech rate (words per minute)
        self._volume = 1.0  # Default volume (0.0 to 1.0)
    
    def _get_engine(self):
        """Get or create the TTS engine (lazy initialization)."""
        if self._engine is None:
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', self._rate)
                self._engine.setProperty('volume', self._volume)
            except Exception as e:
                print(f"TTS Engine initialization failed: {e}")
                return None
        return self._engine
    
    def get_available_voices(self):
        """Get list of available voices."""
        engine = self._get_engine()
        if engine is None:
            return []
        
        try:
            voices = engine.getProperty('voices')
            return [
                {
                    'id': voice.id,
                    'name': voice.name.split(' - ')[0] if ' - ' in voice.name else voice.name,
                    'language': getattr(voice, 'languages', ['en'])[0] if hasattr(voice, 'languages') else 'en'
                }
                for voice in voices
            ]
        except Exception:
            return []
    
    def set_voice(self, voice_id: str):
        """Set the voice to use."""
        engine = self._get_engine()
        if engine:
            try:
                engine.setProperty('voice', voice_id)
                self._current_voice = voice_id
            except Exception as e:
                print(f"Failed to set voice: {e}")
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute). Default is 150."""
        self._rate = max(50, min(300, rate))  # Clamp between 50 and 300
        engine = self._get_engine()
        if engine:
            engine.setProperty('rate', self._rate)
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))
        engine = self._get_engine()
        if engine:
            engine.setProperty('volume', self._volume)
    
    def speak(self, text: str, callback: Optional[Callable] = None):
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            callback: Optional callback when speech completes
        """
        engine = self._get_engine()
        if engine is None:
            print("TTS not available")
            if callback:
                callback()
            return
        
        def _speak_thread():
            with self._lock:
                self._is_speaking = True
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    print(f"TTS error: {e}")
                finally:
                    self._is_speaking = False
                    if callback:
                        callback()
        
        # Run in a separate thread to avoid blocking
        thread = threading.Thread(target=_speak_thread, daemon=True)
        thread.start()
    
    def speak_sync(self, text: str):
        """Speak text synchronously (blocking)."""
        engine = self._get_engine()
        if engine is None:
            return
        
        with self._lock:
            self._is_speaking = True
            try:
                engine.say(text)
                engine.runAndWait()
            finally:
                self._is_speaking = False
    
    def stop(self):
        """Stop any ongoing speech."""
        engine = self._get_engine()
        if engine:
            try:
                engine.stop()
            except Exception:
                pass
            self._is_speaking = False
    
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self._is_speaking
    
    def cleanup(self):
        """Clean up the TTS engine."""
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass
            self._engine = None


class TTSFallback:
    """
    Fallback TTS that generates audio files for browser playback.
    Used when pyttsx3 is not available or for web deployment.
    """
    
    def __init__(self):
        self.supported = False
        # Check if gTTS is available (requires internet but produces audio files)
        try:
            from gtts import gTTS
            self.supported = True
        except ImportError:
            pass
    
    def generate_audio_file(self, text: str, filepath: str, lang: str = 'en') -> bool:
        """
        Generate an audio file from text.
        
        Args:
            text: Text to convert to speech
            filepath: Path to save the audio file
            lang: Language code (default 'en')
        
        Returns:
            True if successful, False otherwise
        """
        if not self.supported:
            return False
        
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=lang)
            tts.save(filepath)
            return True
        except Exception as e:
            print(f"Audio generation failed: {e}")
            return False


# Singleton instances
tts_engine = TTSEngine()
tts_fallback = TTSFallback()


def speak_text(text: str, callback: Optional[Callable] = None):
    """Convenience function to speak text."""
    tts_engine.speak(text, callback)


def get_tts_settings():
    """Get current TTS settings for UI display."""
    return {
        'voices': tts_engine.get_available_voices(),
        'current_voice': tts_engine._current_voice,
        'rate': tts_engine._rate,
        'volume': tts_engine._volume,
        'is_speaking': tts_engine.is_speaking()
    }
