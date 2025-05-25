from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib import messages
from django.views.decorators.cache import never_cache, cache_control
import re
from django.core.exceptions import ValidationError
from .forms import ForgotPasswordForm, RegisterForm
from .models import UploadedFile, ChatHistory, ChatMessage
from django.utils.http import urlsafe_base64_decode
from .forms import ResetPasswordForm
from django import forms

def welcome(request):
    request.session['came_from_welcome'] = True
    return render(request, 'welcome.html')


def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            # Remove auto-login
            messages.success(request, "Registration successful! Please login to continue.")
            return redirect('techjays:login')  # Redirect to login page
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = CustomRegisterForm()
    return render(request, 'register.html', {'form': form})




def validate_password_strength(password):
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character.")

class CustomRegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        validate_password_strength(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data  # <--- Important!




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def login_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        password = request.POST.get('password')
        user = authenticate(request, full_name=full_name, password=password)

        if user:
            login(request, user)
            request.session.pop('came_from_welcome', None)
            return redirect('techjays:chatbot')
        else:
            messages.error(request, 'Invalid full_name or password')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('techjays:welcome')


def forget_password(request):
    form = ForgotPasswordForm()
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Email not registered")
                return redirect('techjays:forget_password')

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            subject = "Reset Your Password"
            message = render_to_string('techjays/reset_password_email.html', {
                'domain': domain,
                'uid': uid,
                'token': token,
            })

            send_mail(subject, message, 'noreply@techjays.com', [email])
            messages.success(request, 'Reset link sent to your email')
    return render(request, 'techjays/forget_password.html', {'form': form})


def reset_password(request, uidb64=None, token=None):
    if uidb64 is None or token is None:
        messages.error(request, "Invalid password reset link.")
        return redirect('techjays:forget_password')

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, "Password reset link is invalid or has expired.")
        return redirect('techjays:forget_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            messages.success(request, "Your password has been reset successfully. Please login.")
            return redirect('techjays:login')
    else:
        form = ResetPasswordForm()

    return render(request, 'techjays/reset_password.html', {'form': form})
