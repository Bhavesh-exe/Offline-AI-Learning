# 📚 Offline AI Learning Platform

An **offline-capable** educational app designed for rural students with limited connectivity. Built with Python, Streamlit, and PWA support.

## 🌟 Features

| Feature | Description |
|---------|-------------|
| **📖 Offline Content** | Works completely without internet after first load |
| **📝 AI Quiz Generator** | Auto-generated MCQs from lesson content |
| **🔄 Smart Sync** | Syncs progress when online |
| **📊 Progress Tracking** | Track lessons, quizzes, and achievements |

## 🚀 Quick Start

### Option 1: Static HTML (Recommended for Offline)
Simply open `index.html` in a browser - works offline after first load!

### Option 2: Streamlit Server
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📚 Content Included

5 Physics lessons with quizzes:
1. Motion and Speed
2. Force and Laws of Motion
3. Gravitation
4. Work, Energy and Power
5. Sound

## 🔧 Tech Stack

- **Frontend**: Streamlit + stlite (WebAssembly)
- **PWA**: Service Worker + Manifest
- **AI**: Rule-based NLP for quiz generation
- **TTS**: pyttsx3 (offline capable)

## 📊 Metrics

- **App Size**: < 1 MB (core files)
- **RAM**: Optimized for 8 GB devices
- **Offline**: ✅ Full functionality

## 📁 Project Structure

```
├── index.html          # PWA entry point (offline-capable)
├── app.py              # Streamlit server version
├── sw.js               # Service Worker
├── manifest.json       # PWA manifest
├── components/         # UI components
├── ai/                 # AI modules
├── data/lessons/       # Lesson content
└── static/             # CSS and icons
```

## 🏆 Hackathon Submission

Built for the "Offline AI Learning Platform for Rural Students" challenge.

**Evaluation Criteria:**
- ✅ Offline Functionality (40%)
- ✅ Device Optimization (25%)
- ✅ Feature Completeness (20%)
- ✅ Innovation & UX (15%)

## 📝 License

MIT License - Free for educational use
