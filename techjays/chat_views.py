import json
import os
import requests
import uuid
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import ChatHistory, ChatMessage
import PyPDF2

# Load API Key from environment variable
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

@login_required
def chatbot_view(request):
    return render(request, 'chat.html')

@login_required
@csrf_exempt
def new_chat(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    session_id = str(uuid.uuid4())

    # Count existing chats for naming
    chat_count = ChatHistory.objects.filter(user=request.user).count()
    chat_name = f"Chat {chat_count + 1}"

    # Create ChatHistory with nice name
    ChatHistory.objects.create(user=request.user, session_id=session_id, name=chat_name)

    return JsonResponse({"session_id": session_id})



@login_required
def get_sessions(request):
    sessions = ChatHistory.objects.filter(user=request.user).order_by('-created_at')
    sessions_data = [
        {"session_id": s.session_id, "name": s.name}  # <-- USE s.name from DB
        for s in sessions
    ]
    return JsonResponse({"sessions": sessions_data})


@login_required
@csrf_exempt
def chat(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    data = json.loads(request.body)
    session_id = data.get("session_id")
    user_message = data.get("message")

    try:
        session = ChatHistory.objects.get(session_id=session_id, user=request.user)
    except ChatHistory.DoesNotExist:
        return JsonResponse({"success": False, "error": "Invalid session ID"}, status=400)

    # Save user message
    ChatMessage.objects.create(chat_history=session, sender='user', text=user_message)

    # Use document text if uploaded
    document_text = getattr(session, 'document_text', '') or ""
    full_prompt = f"{document_text}\n\nUser question: {user_message}" if document_text else user_message

    # Call Gemini API
    model_text = call_gemini_flash_api(full_prompt)

    # Save bot response
    ChatMessage.objects.create(chat_history=session, sender='bot', text=model_text)

    return JsonResponse({"success": True, "response": model_text})

@login_required
@csrf_exempt
def upload_file(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    session_id = request.POST.get("session_id")
    file = request.FILES.get('file')

    print(f"DEBUG: session_id={session_id}, file={file}")

    if not file or not session_id:
        return JsonResponse({"success": False, "error": "Missing file or session_id"}, status=400)

    try:
        session = ChatHistory.objects.get(session_id=session_id, user=request.user)
    except ChatHistory.DoesNotExist:
        return JsonResponse({"success": False, "error": "Invalid session ID"}, status=400)

    filename = file.name
    if not filename.lower().endswith('.pdf'):
        return JsonResponse({"success": False, "error": "Only PDF files are supported"}, status=400)

    filepath = default_storage.save(f"uploads/{filename}", ContentFile(file.read()))

    try:
        with default_storage.open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join([page.extract_text() or '' for page in reader.pages])
            session.document_text = text.strip()
            session.save()
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Error reading PDF: {str(e)}"}, status=500)

    return JsonResponse({"success": True, "message": "File uploaded and processed"})

@login_required
def get_history(request, session_id):
    try:
        session = ChatHistory.objects.get(session_id=session_id, user=request.user)
    except ChatHistory.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

    messages = ChatMessage.objects.filter(chat_history=session).order_by('timestamp')
    history = [
        {"role": m.sender, "text": m.text}
        for m in messages
    ]
    return JsonResponse(history, safe=False)

@login_required
@csrf_exempt
def delete_chat(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    data = json.loads(request.body)
    session_id = data.get("session_id")

    try:
        session = ChatHistory.objects.get(session_id=session_id, user=request.user)
        session.delete()
        return JsonResponse({"success": True})
    except ChatHistory.DoesNotExist:
        return JsonResponse({"success": False, "error": "Invalid session ID"}, status=400)

@login_required
@csrf_exempt
def remove_document(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    data = json.loads(request.body)
    session_id = data.get("session_id")

    try:
        session = ChatHistory.objects.get(session_id=session_id, user=request.user)
        session.document_text = ""
        session.save()
        return JsonResponse({"success": True, "message": "Document removed for session"})
    except ChatHistory.DoesNotExist:
        return JsonResponse({"success": False, "message": "Session ID not found"})

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
