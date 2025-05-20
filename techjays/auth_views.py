import uuid
import json
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .forms import ForgotPasswordForm, RegisterForm
from .models import UploadedFile, ChatHistory, ChatMessage  # your models
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site 
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib import messages


def welcome(request):
    return render(request, 'welcome.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            login(request, user)
            # After registration, redirect to login page (or you can redirect elsewhere)
            return redirect('techjays:login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to your chatbot or home page after login
            return redirect('techjays:chatbot')
  # Ensure chatbot app has this URL name
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    # Redirect to login page after logout, include namespace if needed
    return redirect('techjays:login')

def forget_password(request):
  form = ForgotPasswordForm()
  if request.method == 'POST':
        #form 
   form = ForgotPasswordForm(request.POST)
   if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            #send email to reset password
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request)
            domain = current_site.domain
            subject = "Reset Password Requested"
            message = render_to_string('techjays/reset_password_email.html', {
                'domain': domain,
                'uid': uid,
                'token': token
            })

            send_mail(subject, message, 'noreply@techjays.com', [email])
            messages.success(request, 'Email has been sent')
  return render(request,'techjays/forget_password.html',{'form': form})

def reset_password(request):
    pass