# 🎤 **SPEECH ANALYZER PRO**

An AI-powered speech analysis platform that evaluates speaking pace, filler words, clarity, persuasive language, and audience readability using Automatic Speech Recognition (ASR) and Natural Language Processing (NLP).

Built with Flask, Whisper AI, NLP libraries, and interactive visual dashboards.

---

# 🚀 **FEATURES**

## 🎙 **SPEECH-TO-TEXT TRANSCRIPTION**
- Converts uploaded audio into text using OpenAI Whisper
- Supports:
  - MP3
  - WAV
  - M4A

---

## ⚡ **PACING ANALYSIS**
- Calculates Words Per Minute (WPM)
- Detects:
  - Slow speech
  - Ideal pacing
  - Fast speech
- Includes:
  - Speedometer-style gauge
  - Pace history tracking

---

## 🗣 **FILLER WORD DETECTION**

Detects common filler words such as:

- um
- uh
- like
- basically
- you know

Provides:
- Total filler count
- Filler frequency breakdown
- Highlighted transcript visualization

---

## 💬 **WEAK VS PERSUASIVE LANGUAGE ANALYSIS**

### **WEAK LANGUAGE EXAMPLES**
- maybe
- I think
- sort of
- kind of

### **PERSUASIVE LANGUAGE EXAMPLES**
- definitely
- effective
- powerful
- proven

Helps improve confidence and communication quality.

---

## 📖 **READABILITY & AUDIENCE ANALYSIS**
- Computes readability grade level
- Provides audience-specific feedback
- Detects excessive jargon usage

---

## 📊 **INTERACTIVE ANALYTICS DASHBOARD**

Visualizations include:
- Doughnut charts
- Bar graphs
- Pace tracking graphs
- Interactive transcript highlights

---

## 📈 **PROGRESS TRACKING**
- Stores previous analysis reports using SQLite
- Compares:
  - WPM improvement
  - Filler word reduction
  - Weak language reduction

---

# 🛠 **TECH STACK**

## **FRONTEND**
- HTML
- Tailwind CSS
- JavaScript
- Chart.js

## **BACKEND**
- Python
- Flask

## **AI / NLP**
- OpenAI Whisper
- NLTK
- textstat

## **DATABASE**
- SQLite

---

# 📂 **PROJECT STRUCTURE**

```bash
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
```

---

# ⚙️ **INSTALLATION**

## **1️⃣ CLONE THE REPOSITORY**

```bash
git clone https://github.com/your-username/speech-analyzer-pro.git
cd speech-analyzer-pro
```

---

## **2️⃣ CREATE VIRTUAL ENVIRONMENT**

### **WINDOWS**
```bash
python -m venv venv
venv\Scripts\activate
```

### **LINUX / MAC**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## **3️⃣ INSTALL DEPENDENCIES**

```bash
pip install -r requirements.txt
```

---

# ▶️ **RUNNING THE PROJECT**

Start the Flask server:

```bash
python app.py
```

The application will run on:

```bash
http://127.0.0.1:5000
```

---

# 📦 **REQUIRED PYTHON LIBRARIES**

Example dependencies:

```txt
flask
flask-cors
openai-whisper
nltk
textstat
pydub
torch
```

---

# 🧠 **HOW IT WORKS**

1. User uploads an audio file
2. Whisper transcribes speech into text
3. NLP analysis is performed
4. Results are visualized on the dashboard
5. Reports are stored for future comparison

---

# 📸 **KEY FUNCTIONALITIES**

✅ Speech Transcription  
✅ Filler Word Analysis  
✅ Speaking Pace Evaluation  
✅ Word-Level Timing Detection  
✅ Readability Analysis  
✅ Progress Tracking  
✅ Interactive Dashboard  

---

# 🎯 **USE CASES**

- Interview preparation
- Public speaking practice
- Presentation coaching
- Debate training
- Classroom communication analysis
- Podcast speaking analysis

---

# 🔮 **FUTURE IMPROVEMENTS**

- Real-time live speech analysis
- Emotion detection
- AI-generated speaking suggestions
- Multi-language support
- Voice tone analysis
- Speaker comparison mode

---

# 👨‍💻 **AUTHOR**

## **DHEERAJ D**
B.Tech CSE | IIIT Sri City

- LinkedIn: https://www.linkedin.com/in/dheeraj-d-0b27a0375

---

# ⭐ **CONTRIBUTING**

Contributions, issues, and feature requests are welcome!

Feel free to fork the repository and submit a pull request.

---

# 📜 **LICENSE**

This project is licensed under the MIT License.

---
