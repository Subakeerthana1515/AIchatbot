import json
import os
import sqlite3
import requests
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import PyPDF2
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import uuid



# Load API Key
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

# In-memory storage (use DB or cache in production)
chat_sessions = {}
document_texts = {}
uploaded_files = {}

@login_required  # Optional: remove if no login required
def chatbot_view(request):
    # Render the chatbot UI template
    return render(request, 'chat.html')

@csrf_exempt
def new_chat(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")
    
    # Generate a new unique session ID
    session_id = str(uuid.uuid4())

    # Initialize empty session data
    chat_sessions[session_id] = []
    document_texts[session_id] = ""

    # Return the session_id to the client
    return JsonResponse({"session_id": session_id})

@csrf_exempt
def chat(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")
    data = json.loads(request.body)
    session_id = data.get("session_id")
    user_message = data.get("message")

    if session_id not in chat_sessions:
        return JsonResponse({"success": False, "error": "Invalid session ID"}, status=400)

    chat_sessions[session_id].append({"role": "user", "text": user_message})
    save_to_db(session_id, "user", user_message)

    full_prompt = user_message
    if document_texts.get(session_id):
        full_prompt = f"{document_texts[session_id]}\n\nUser question: {user_message}"

    model_text = call_gemini_flash_api(full_prompt)

    chat_sessions[session_id].append({"role": "model", "text": model_text})
    save_to_db(session_id, "model", model_text)

    return JsonResponse({"success": True, "response": model_text})

@csrf_exempt
def upload_file(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")
    session_id = request.POST.get("session_id")
    file = request.FILES.get('file')

    if not file or not session_id:
        return JsonResponse({"success": False, "error": "Missing file or session_id"}, status=400)

    filename = file.name
    filepath = default_storage.save(f"uploads/{filename}", ContentFile(file.read()))
    uploaded_files[session_id] = default_storage.path(filepath)

    if filename.lower().endswith('.pdf'):
        try:
            with default_storage.open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n".join([page.extract_text() or '' for page in reader.pages])
                document_texts[session_id] = text.strip()
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error reading PDF: {str(e)}"}, status=500)
    else:
        return JsonResponse({"success": False, "error": "Only PDF files are supported"}, status=400)

    return JsonResponse({"success": True, "message": "File uploaded and processed"})

def get_history(request, session_id):
    # Convert UUID object to string if needed
    if hasattr(session_id, 'hex'):
        session_id = str(session_id)

    conn = sqlite3.connect('chat_session.db')
    c = conn.cursor()
    c.execute('SELECT role, message FROM chat_history WHERE session_id = ?', (session_id,))
    rows = c.fetchall()
    conn.close()
    
    history = [{"role": role, "text": msg} for role, msg in rows]
    return JsonResponse(history, safe=False)


@csrf_exempt
def delete_chat(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")
    data = json.loads(request.body)
    session_id = data.get("session_id")
    chat_sessions.pop(session_id, None)
    document_texts.pop(session_id, None)
    return JsonResponse({"success": True})

@csrf_exempt
def remove_document(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    data = json.loads(request.body)
    session_id = data.get("session_id")

    if session_id in document_texts:
        document_texts[session_id] = ""
        filepath = uploaded_files.get(session_id)
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            uploaded_files.pop(session_id, None)
        return JsonResponse({"success": True, "message": "Document removed for session"})
    else:
        return JsonResponse({"success": False, "message": "Session ID not found"})

def save_to_db(session_id, role, message):
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

def call_gemini_flash_api(prompt_text):
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"parts": [{"text": prompt_text}]}
        ]
    }

    try:
        response = requests.post(GEMINI_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        model_text = response_data['candidates'][0]['content']['parts'][0]['text']
        return model_text

    except Exception as e:
        print("Error connecting to Gemini API:", str(e))
        return "Sorry, I couldn't process your request right now."
