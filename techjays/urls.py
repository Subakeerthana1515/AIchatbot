from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),                     # Welcome page
    path('register/', views.register, name='register'),          # Signup page
    path('login_view/', views.login_view, name='login'),         # Login page
    path('logout_view/', views.logout_view, name='logout'),      # Logout functionality
    path('chatbot/', views.chatbot_view, name='chatbot'),        # Chatbot main page
   
    
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)