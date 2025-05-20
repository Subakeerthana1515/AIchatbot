from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from techjays import auth_views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('techjays/', include('techjays.urls')),
    path('', auth_views.welcome, name='welcome'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
