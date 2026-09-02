from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.users.forms import ThrottledAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('users/', include('apps.users.urls')),
    path('academics/', include('apps.academics.urls')),
    path('fees/', include('apps.fees.urls')),
    
    # Built-in Auth Routes
    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html',
        authentication_form=ThrottledAuthenticationForm,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
    template_name='users/password_change.html',
    success_url='/password-change/done/'
), name='password_change'),

path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
    template_name='users/password_change_done.html'
), name='password_change_done'),
]