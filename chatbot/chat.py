import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import PyPDF2
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Gemini API endpoint
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# In-memory session storage
chat_sessions = {}
document_texts = {}
uploaded_files = {} 

@app.route("/new_chat", methods=["POST"])
def new_chat():
    data = request.get_json()
    session_id = data.get("session_id")
    chat_sessions[session_id] = []
    document_texts[session_id] = ""  # Initialize empty doc text
    return jsonify({"success": True})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    session_id = data.get("session_id")
    user_message = data.get("message")

    if session_id not in chat_sessions:
        return jsonify({"success": False, "error": "Invalid session ID"}), 400

    chat_sessions[session_id].append({"role": "user", "text": user_message})
    save_to_db(session_id, "user", user_message)
    
    # Combine uploaded document text with user query
    full_prompt = user_message
    if document_texts.get(session_id):
        full_prompt = f"{document_texts[session_id]}\n\nUser question: {user_message}"

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"parts": [{"text": full_prompt}]}
        ]
    }

    try:
        response = requests.post(GEMINI_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        model_text = response_data['candidates'][0]['content']['parts'][0]['text']

        chat_sessions[session_id].append({"role": "model", "text": model_text})
        save_to_db(session_id, "model", model_text)
        return jsonify({"success": True, "response": model_text})

    except Exception as e:
        print("Error connecting to Gemini API:", str(e))
        return jsonify({"success": False, "error": "Error connecting to Gemini API."})

@app.route("/upload", methods=["POST"])
def upload_file():
    session_id = request.form.get("session_id")
    if 'file' not in request.files or not session_id:
        return jsonify({"success": False, "error": "Missing file or session_id"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Extract text if it's a PDF
    if filename.lower().endswith('.pdf'):
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n".join([page.extract_text() or '' for page in reader.pages])
                document_texts[session_id] = text.strip()
        except Exception as e:
            return jsonify({"success": False, "error": f"Error reading PDF: {str(e)}"}), 500
    else:
        return jsonify({"success": False, "error": "Only PDF files are supported"}), 400

    return jsonify({"success": True, "message": "File uploaded and processed"})

@app.route("/get_history/<session_id>", methods=["GET"])
def get_history(session_id):
    import sqlite3
    conn = sqlite3.connect('chat_session.db')
    c = conn.cursor()
    c.execute('SELECT role, message FROM chat_history WHERE session_id = ?', (session_id,))
    rows = c.fetchall()
    conn.close()
    history = [{"role": role, "text": msg} for role, msg in rows]
    return jsonify(history)


@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    data = request.get_json()
    session_id = data.get("session_id")
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    if session_id in document_texts:
        del document_texts[session_id]
    return jsonify({"success": True})

import os

@app.route("/remove_document", methods=["POST"])
def remove_document():
    data = request.get_json()
    session_id = data.get("session_id")

    if session_id in document_texts:
        document_texts[session_id] = ""

        # Also remove file if stored
        if session_id in uploaded_files:
            filepath = uploaded_files[session_id]
            if os.path.exists(filepath):
                os.remove(filepath)
            del uploaded_files[session_id]

        return jsonify({"success": True, "message": "Document removed for session"})
    else:
        return jsonify({"success": False, "error": "Session not found"}), 400


def save_to_db(session_id, role, message):
    import sqlite3
    conn = sqlite3.connect('chat_session.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL
        )
    ''')
    c.execute('INSERT INTO chat_history (session_id, role, message) VALUES (?, ?, ?)',
              (session_id, role, message))
    conn.commit()
    conn.close()


if __name__ == "__main__":
  
    app.run(debug=True)