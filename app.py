import os
import whisper
import nltk
import textstat
import sqlite3
import json
import time
import traceback
from collections import Counter
from flask import Flask, render_template, request, jsonify
from pydub import AudioSegment
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename # Moved import to top

# -----------------------------------------------------------------------------
# 1. DATABASE & A/B TEST FUNCTIONS
# -----------------------------------------------------------------------------

DB_FILE = 'presentations.db'

def init_db():
    print("[DB] Initializing database...")
    conn = sqlite3.connect(DB_FILE, check_same_thread=False) 
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            report_json TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("[DB] Database initialized.")

def save_report_to_db(report_data):
    print("[DB] Saving report...")
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    # IMPORTANT: Make sure we don't save the 'history' or 'ab_test' arrays back into the DB
    report_to_save = report_data.copy() # Create a copy
    if 'history' in report_to_save:
        del report_to_save['history'] # Remove history before saving
    if 'ab_test' in report_to_save:
         del report_to_save['ab_test'] # Remove comparison before saving

    report_json = json.dumps(report_to_save)
    c.execute("INSERT INTO reports (report_json) VALUES (?)", (report_json,))
    conn.commit()
    conn.close()
    print("[DB] Report saved (excluding history/ab_test).")

def get_last_report():
    print("[DB] Fetching last report...")
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports'")
    if not c.fetchone():
        print("[DB] No 'reports' table found.")
        conn.close()
        return None
        
    c.execute("SELECT report_json FROM reports ORDER BY timestamp DESC LIMIT 1")
    last_report_row = c.fetchone() 
    conn.close()
    
    if last_report_row:
        print("[DB] Found last report.")
        try:
            return json.loads(last_report_row[0]) 
        except json.JSONDecodeError as e:
             print(f"[DB] Error decoding last report JSON: {e}")
             return None
    print("[DB] No previous report found.")
    return None

def get_all_reports_history():
    """Fetches pacing history from ALL reports."""
    print("[DB] Fetching all reports for history chart...")
    history = [] 
    conn = None 
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row 
        c = conn.cursor()
        
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports'")
        if not c.fetchone():
            print("[DB] No 'reports' table found for history.")
            return [] 
            
        c.execute("SELECT timestamp, report_json FROM reports ORDER BY timestamp ASC")
        rows = c.fetchall()
        
        if rows is None:
             print("[DB] No rows fetched from database for history.")
             return []

        for row in rows:
             try:
                 if row and 'report_json' in row.keys() and row['report_json']:
                     report = json.loads(row['report_json'])
                     if (report and isinstance(report, dict) and 
                         'pacing' in report and isinstance(report['pacing'], dict) and 
                         'wpm' in report['pacing'] and 
                         isinstance(report['pacing']['wpm'], (int, float))):
                         
                         history.append({
                             "timestamp": row['timestamp'],
                             "wpm": report['pacing']['wpm']
                         })
                     else:
                          print(f"[DB] Skipping report {row['timestamp']} due to missing/invalid pacing data.")
                 else:
                      print("[DB] Skipping invalid row.")
             except json.JSONDecodeError as e:
                 print(f"[DB] Error decoding report JSON for history (Timestamp: {row.get('timestamp', 'N/A')}): {e}")
             except Exception as inner_e: 
                  print(f"[DB] Unexpected error processing row (Timestamp: {row.get('timestamp', 'N/A')}): {inner_e}")

        print(f"[DB] Found {len(history)} valid historical reports.")
        return history 

    except sqlite3.Error as db_e: 
        print(f"[DB] Database error fetching history: {db_e}")
        return [] 
    except Exception as e:
        print(f"[DB] General error fetching history: {e}")
        print(traceback.format_exc()) 
        return [] 
    finally:
        if conn:
            conn.close() 

# --- THIS FUNCTION HAS BEEN CORRECTED ---
def generate_ab_comparison(new_report, old_report):
    print("[A/B] Generating comparison...")
    if not old_report:
        print("[A-B] This is the first report.")
        return {"message": "This is your first report. No comparison available."}
    
    def get_stat(report, key, default=0):
        try:
            val = report
            for k in key.split('.'):
                val = val[k]
            return val if isinstance(val, (int, float)) else default
        except (KeyError, TypeError, AttributeError): 
            return default

    # *** FIX: Assign the results of get_stat to variables ***
    old_wpm = get_stat(old_report, 'pacing.wpm')
    new_wpm = get_stat(new_report, 'pacing.wpm')
    
    old_fillers = get_stat(old_report, 'fillers.total_count')
    new_fillers = get_stat(new_report, 'fillers.total_count')
    
    old_weak = get_stat(old_report, 'language.weak_word_count')
    new_weak = get_stat(new_report, 'language.weak_word_count')
    # *******************************************************

    comparison = {
        "pacing_change": new_wpm - old_wpm,
        "filler_words_change": new_fillers - old_fillers,
        "weak_words_change": new_weak - old_weak,
    }
    print("[A/B] Comparison generated.")
    return comparison

# -----------------------------------------------------------------------------
# 2. PRESENTATION ANALYSIS CORE
# -----------------------------------------------------------------------------

class PresentationAnalyzer:
    # --- No changes needed in this class ---
    def __init__(self, transcript):
        print("[ANALYZER] Initializing with new transcript...")
        if not transcript: self.transcript = " "
        else: self.transcript = transcript
        print("[ANALYZER] Tokenizing transcript...")
        try:
            self.words = [word.lower() for word in nltk.word_tokenize(self.transcript)]
            self.word_count = len(self.words)
            print(f"[ANALYZER] Tokenizing complete. Word count: {self.word_count}")
        except Exception as e:
            print(f"[ANALYZER] ERROR during NLTK tokenization: {e}")
            self.words = self.transcript.lower().split(); self.word_count = len(self.words)

    def analyze_pacing_and_fillers(self, audio_duration_seconds):
        print("[ANALYZER] Analyzing pacing and fillers...")
        if audio_duration_seconds > 0: wpm = self.word_count / (audio_duration_seconds / 60)
        else: wpm = 0
        pacing_feedback = ""
        if wpm < 120: pacing_feedback = "Your pacing is a bit slow. Try to speed up."
        elif wpm > 160: pacing_feedback = "Your pacing is very fast. Try to slow down."
        else: pacing_feedback = "Your pacing is excellent!"
        FILLER_WORDS = {'um', 'umm', 'uh', 'ah', 'er', 'like', 'you know', 'actually', 'basically', 'so', 'right', 'well'}
        found_fillers = [word for word in self.words if word in FILLER_WORDS]
        transcript_lower = self.transcript.lower()
        for phrase in FILLER_WORDS:
             if ' ' in phrase: 
                 # Assign count here explicitly if needed elsewhere, though not strictly necessary for this logic
                 phrase_count = transcript_lower.count(phrase) 
                 if phrase_count > 0:
                     found_fillers.extend([phrase] * phrase_count)
        filler_summary = dict(Counter(found_fillers))
        print("[ANALYZER] Pacing and filler analysis complete.")
        return { "pacing": { "wpm": round(wpm, 1), "feedback": pacing_feedback, "word_count": self.word_count, "duration_seconds": round(audio_duration_seconds, 1)}, "fillers": {"summary": filler_summary, "total_count": len(found_fillers)}}

    def analyze_word_pacing(self, whisper_result, audio_duration_sec):
        print("[ANALYZER] Analyzing word-level pacing...")
        words = [word for segment in whisper_result.get('segments', []) for word in segment.get('words', [])]
        if not words: print("[ANALYZER] No word-level timestamps found..."); return {"fast_words": [], "slow_words": [], "word_pacing_feedback": "Could not get word-level timestamps..."}
        word_durations = []
        for word in words:
            if 'start' in word and 'end' in word: duration = word['end'] - word['start']; word_durations.append(duration); word['duration'] = duration
        if not word_durations: return {"fast_words": [], "slow_words": [], "word_pacing_feedback": "Word duration calculation failed."}
        total_speech_time = sum(word_durations)
        if total_speech_time == 0: total_speech_time = audio_duration_sec
        wps = len(words) / total_speech_time; avg_duration = 1 / wps
        fast_threshold = avg_duration * 0.5; slow_threshold = avg_duration * 2.0
        fast_words = []; slow_words = []
        for word in words:
            word_text = word.get('word', '').strip('.,!?').lower()
            if not word_text or 'duration' not in word: continue
            if word['duration'] < fast_threshold: fast_words.append(word_text)
            elif word['duration'] > slow_threshold: slow_words.append(word_text)
        print("[ANALYZER] Word-level pacing analysis complete.")
        return {"fast_words": list(set(fast_words)), "slow_words": list(set(slow_words)), "word_pacing_feedback": f"Found {len(fast_words)} rushed words and {len(slow_words)} drawn-out words."}
        
    def analyze_language(self):
        print("[ANALYZER] Analyzing language (weak/persuasive)...")
        WEAK_WORDS = {"i think", "maybe", "sort of", "kind of", "i guess", "just", "perhaps", "a little", "might", "seems"}
        PERSUASIVE_WORDS = {"definitely", "proven", "guarantee", "consequently", "discover", "immediately", "results", "powerful", "effective", "essential"}
        found_weak = [word for word in self.words if word in WEAK_WORDS]
        found_persuasive = [word for word in self.words if word in PERSUASIVE_WORDS]
        transcript_lower = self.transcript.lower()
        for phrase in WEAK_WORDS | PERSUASIVE_WORDS:
             if ' ' in phrase: 
                 phrase_count = transcript_lower.count(phrase); # Assign count explicitly
                 if phrase_count > 0:
                     if phrase in WEAK_WORDS: found_weak.extend([phrase] * phrase_count)
                     else: found_persuasive.extend([phrase] * phrase_count)
        print("[ANALYZER] Language analysis complete.")
        return {"weak_word_summary": dict(Counter(found_weak)), "weak_word_count": len(found_weak), "persuasive_word_summary": dict(Counter(found_persuasive)), "persuasive_word_count": len(found_persuasive)}

    def analyze_audience(self, audience_type="general"):
        print("[ANALYZER] Analyzing audience readability...")
        try: grade_level = textstat.flesch_kincaid_grade(self.transcript)
        except Exception as e: print(f"[ANALYZER] ERROR during textstat analysis: {e}"); grade_level = 0
        readability_feedback = ""
        # Simplified feedback for brevity in code
        if audience_type == "novice" and grade_level > 9: readability_feedback = f"Grade Level {grade_level:.1f} might be complex for novices."
        elif audience_type == "general" and grade_level > 12: readability_feedback = f"Grade Level {grade_level:.1f} might be too academic."
        else: readability_feedback = f"Grade Level {grade_level:.1f} seems appropriate for '{audience_type}'."
        JARGON_LIST = {"synergy", "paradigm shift", "core competency", "leverage", "KPI", "monorepo", "blockchain", "big data"}
        found_jargon = [word for word in self.words if word in JARGON_LIST and audience_type in ["novice", "general"]]
        print("[ANALYZER] Audience analysis complete.")
        return {"grade_level": grade_level, "readability_feedback": readability_feedback, "found_jargon": dict(Counter(found_jargon)), "jargon_count": len(found_jargon)}

# -----------------------------------------------------------------------------
# 3. FLASK WEB APPLICATION
# -----------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)
print("[SERVER] CORS enabled for all routes.")

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("[SERVER] Loading Whisper model (this may take a moment)...")
try:
    whisper_model = whisper.load_model("tiny")
    print("[SERVER] Whisper model loaded successfully.")
except Exception as e:
    print(f"[SERVER] FATAL ERROR: Could not load Whisper model: {e}")
    traceback.print_exc() 
    whisper_model = None

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    print(f"[SERVER] ERROR: File uploaded is too large (>{app.config['MAX_CONTENT_LENGTH']} bytes).")
    return jsonify({"error": f"File is too large. Please upload a file under 30MB."}), 413

@app.route("/")
def home():
    print("[SERVER] GET / - Serving index.html")
    return render_template('index.html')


@app.route("/analyze", methods=['POST'])
def analyze_speech():
    print("\n" + "="*50)
    print(f"[SERVER] POST /analyze - New request received at {time.ctime()}")
    start_time = time.time() 
    
    final_report = {
        "transcript": "Error during processing.",
        "pacing": {"wpm": 0, "feedback": "N/A", "word_count": 0, "duration_seconds": 0},
        "fillers": {"summary": {}, "total_count": 0},
        "word_pacing": {"fast_words": [], "slow_words": [], "word_pacing_feedback": "N/A"},
        "language": {"weak_word_summary": {}, "weak_word_count": 0, "persuasive_word_summary": {}, "persuasive_word_count": 0},
        "audience": {"grade_level": 0, "readability_feedback": "N/A", "found_jargon": {}, "jargon_count": 0},
        "ab_test": {"message": "Analysis failed, comparison unavailable."},
        "history": [] 
    }

    try:
        if not whisper_model:
             print("[SERVER] FATAL ERROR: Whisper model was not loaded.")
             final_report["error"] = "Server error: Whisper model not loaded."
             return jsonify(final_report), 500 

        if 'audio_file' not in request.files:
            print("[SERVER] ERROR: 'audio_file' not in request.files")
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['audio_file']
        
        if not file or file.filename == '':
            print("[SERVER] ERROR: No selected file (filename is empty or file object is missing)")
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        if not filename: 
             filename = f"upload_{int(time.time())}.audio" 

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"[SERVER] Saving file to: {filepath}")
        file.save(filepath)
        print("[SERVER] File saved.")
        
        print("[SERVER] Step 1: Loading audio with pydub...")
        audio = AudioSegment.from_file(filepath)
        audio_duration_sec = len(audio) / 1000.0
        print(f"[SERVER] Step 1 OK. Duration: {audio_duration_sec:.2f}s")

        print(f"[SERVER] Step 2: Transcribing with Whisper...")
        transcribe_result = whisper_model.transcribe(filepath, fp16=False, word_timestamps=True)
        transcript = transcribe_result.get('text', '')
        if not transcript:
             print("[SERVER] WARNING: Whisper returned an empty transcript.")

        print("[SERVER] Step 2 OK. Transcription complete.")
        final_report["transcript"] = transcript 

        print("[SERVER] Step 3: Running all analyses...")
        analyzer = PresentationAnalyzer(transcript)
        
        pacing_and_fillers = analyzer.analyze_pacing_and_fillers(audio_duration_sec)
        word_pacing_report = analyzer.analyze_word_pacing(transcribe_result, audio_duration_sec)
        language_report = analyzer.analyze_language()
        audience_report = analyzer.analyze_audience(audience_type="general")
        print("[SERVER] Step 3 OK. All analyses complete.")

        final_report["pacing"] = pacing_and_fillers.get('pacing', final_report["pacing"])
        final_report["fillers"] = pacing_and_fillers.get('fillers', final_report["fillers"])
        final_report["word_pacing"] = word_pacing_report
        final_report["language"] = language_report
        final_report["audience"] = audience_report

        print("[SERVER] Step 4: Fetching historical pace data...")
        history = get_all_reports_history()
        current_wpm = final_report.get("pacing", {}).get("wpm", 0)
        history.append({
            "timestamp": "Current", 
            "wpm": current_wpm
        })
        final_report['history'] = history 
        print("[SERVER] Step 4 OK. History fetched and added to response report.")

        print("[SERVER] Step 5: Running A/B test...")
        report_for_comparison = final_report.copy()
        if 'history' in report_for_comparison: del report_for_comparison['history']
        # Also remove ab_test itself before comparison if it exists from defaults
        if 'ab_test' in report_for_comparison: del report_for_comparison['ab_test']


        last_report = get_last_report()
        ab_comparison = generate_ab_comparison(report_for_comparison, last_report)
        final_report['ab_test'] = ab_comparison
        print("[SERVER] Step 5 OK. A/B test complete and added to response report.")
        
        print("[SERVER] Step 6: Saving core report to database...")
        save_report_to_db(final_report) 
        print(f"[SERVER] Step 6 OK. Core report saved.")

        try:
             print(f"[SERVER] Cleaning up uploaded file: {filepath}")
             os.remove(filepath)
             print("[SERVER] Cleanup successful.")
        except OSError as e:
             print(f"[SERVER] Error removing uploaded file {filepath}: {e}")

        end_time = time.time()
        print(f"[SERVER] --- Request finished successfully in {end_time - start_time:.2f} seconds ---")
        
        return jsonify(final_report)

    except Exception as e:
        print("\n" + "!"*50)
        print("[SERVER] --- FATAL ERROR CAUGHT in /analyze ---")
        print("An exception occurred:")
        print(traceback.format_exc()) 
        print("!"*50 + "\n")
        
        error_message = f"An unexpected server error occurred: {str(e)}"
        try:
             final_report["error"] = error_message
             final_report["details"] = "Check server console for full traceback."
             return jsonify(final_report), 500
        except Exception as json_e:
             print(f"[SERVER] Error creating JSON response for error: {json_e}")
             return f"Internal Server Error: {error_message}. Check server logs.", 500


# This is the main entry point
if __name__ == "__main__":
    init_db()  
    app.run(debug=True, host='0.0.0.0', port=5000)

