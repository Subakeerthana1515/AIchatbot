from django.shortcuts import redirect

class RestrictLoginAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if path.endswith('/techjays/login_view/'):
            came_from_welcome = request.session.get('came_from_welcome', False)
            if not came_from_welcome and not request.user.is_authenticated:
                return redirect('/techjays/')
            if request.user.is_authenticated:
                return redirect('/techjays/chatbot/')

        return self.get_response(request)
