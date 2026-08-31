from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('academics/', include('apps.academics.urls')),
    path('fees/', include('apps.fees.urls')),
]