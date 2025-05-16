from django.urls import path
from . import auth_views, chat_views
from techjays.chat_views import get_history

app_name = 'techjays'

urlpatterns = [
    path('', auth_views.welcome, name='welcome'),
    path('welcome/', auth_views.welcome, name='welcome'),
    path('register/', auth_views.register, name='register'),
    path('login_view/', auth_views.login_view, name='login'),
    path('logout_view/', auth_views.logout_view, name='logout'),

    # Chatbot only accessible after login
    path('chatbot/', chat_views.chatbot_view, name='chatbot'),
    path('chatbot/new_chat/', chat_views.new_chat, name='new_chat'),
    path('chatbot/chat/', chat_views.chat, name='chat'),
    path('chatbot/upload/', chat_views.upload_file, name='upload_file'),
    path('chatbot/get_history/<str:session_id>/', get_history),
    path('chatbot/get_sessions/', chat_views.get_sessions, name='get_sessions'),  # <-- Added this line
    path('chatbot/delete/', chat_views.delete_chat, name='delete_chat'),
    path('chatbot/remove_document/', chat_views.remove_document, name='remove_document'),
    path('chatbot/gemini/', chat_views.call_gemini_flash_api, name='call_gemini'),
]
