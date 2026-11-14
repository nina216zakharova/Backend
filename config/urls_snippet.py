"""
Include these URL patterns in your config/urls.py file:
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/', include('projects.urls')),
    path('api/applications/', include('applications.urls')),
]

