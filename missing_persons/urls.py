from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views  # Make sure 'core' app is installed in settings.py

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register_missing_person, name='register_missing_person'),
    path('person/<int:pk>/', views.missing_person_detail, name='missing_person_detail'),
    path('process-video/', views.process_video_feed, name='process_video_feed'),
    path('verify-match/<int:match_report_id>/', views.verify_match, name='verify_match'),

    # Django built-in auth URLs (login, logout, password management)
    path('accounts/', include('django.contrib.auth.urls')),
]

# Media files (only in development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)