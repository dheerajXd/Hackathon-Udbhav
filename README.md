🎤 Speech Analyzer Pro

An AI-powered speech analysis platform that evaluates speaking pace, filler words, clarity, persuasive language, and audience readability using automatic speech recognition and NLP techniques.

Built with Flask, Whisper AI, NLP libraries, and interactive visual dashboards.

🚀 Features
🎙 Speech-to-Text Transcription
Converts uploaded audio into text using OpenAI Whisper.
Supports:
MP3
WAV
M4A
⚡ Pacing Analysis
Calculates Words Per Minute (WPM)
Detects:
Slow speech
Ideal pacing
Fast speech
Includes:
Speedometer gauge
Pace history graph
🗣 Filler Word Detection

Detects common filler words such as:

um
uh
like
basically
you know

Provides:

Total filler count
Filler frequency breakdown
Highlighted transcript visualization
💬 Weak vs Persuasive Language Analysis
Weak Language

Examples:

maybe
I think
sort of
Persuasive Language

Examples:

definitely
effective
powerful

Helps improve confidence and communication quality.

📖 Readability & Audience Analysis
Computes readability grade level
Provides audience-specific feedback
Detects excessive jargon usage
📊 Interactive Analytics Dashboard

Visualizations include:

Doughnut charts
Bar graphs
Pace tracking graphs
Interactive transcript highlights
📈 Progress Tracking
Stores previous analysis reports using SQLite
Compares:
WPM improvement
Filler word reduction
Weak language reduction
🛠 Tech Stack
Frontend
HTML
Tailwind CSS
JavaScript
Chart.js
Backend
Python
Flask
AI / NLP
Whisper AI
NLTK
textstat
Database
SQLite
📂 Project Structure
Speech-Analyzer-Pro/
│
├── templates/
│   └── index.html
│
├── uploads/
│
├── app.py
├── presentations.db
├── requirements.txt
└── README.md
⚙️ Installation
1. Clone the Repository
git clone https://github.com/your-username/speech-analyzer-pro.git
cd speech-analyzer-pro
2. Create Virtual Environment
Windows
python -m venv venv
venv\Scripts\activate
Linux / Mac
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
pip install -r requirements.txt
▶️ Running the Project

Start the Flask server:

python app.py

The application will run on:

http://127.0.0.1:5000
📦 Required Python Libraries

Example dependencies:

flask
flask-cors
openai-whisper
nltk
textstat
pydub
torch
sqlite3
🧠 How It Works
User uploads an audio file
Whisper transcribes speech into text
NLP analysis is performed
Results are visualized on the dashboard
Reports are stored for future comparison
📸 Key Functionalities

✅ Speech Transcription
✅ Filler Word Analysis
✅ Speaking Pace Evaluation
✅ Word-Level Timing Detection
✅ Readability Analysis
✅ Progress Tracking
✅ Interactive Dashboard

🎯 Use Cases
Interview preparation
Public speaking practice
Presentation coaching
Debate training
Classroom communication analysis
Podcast speaking analysis
🔮 Future Improvements
Real-time live speech analysis
Emotion detection
AI-generated speaking suggestions
Multi-language support
Voice tone analysis
Speaker comparison mode
