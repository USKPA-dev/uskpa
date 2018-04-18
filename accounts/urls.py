from django.urls import path
from django.contrib.auth import views as views
from .views import UserProfileView


urlpatterns = [
    path('profile/', UserProfileView.as_view(template_name='profile.html'), name='profile'),
    path('login/', views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('password_change/',
         views.PasswordChangeView.as_view(template_name='password_change.html'),
         name='password_change'),
    path('password_change/done/',
         views.PasswordChangeDoneView.as_view(template_name='password_change.html'),
         name='password_change_done'),
    path('password_reset/',
         views.PasswordResetView.as_view(template_name='reset.html'),
         name='password_reset'),
    path('password_reset/done/',
         views.PasswordResetDoneView.as_view(template_name='reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         views.PasswordResetConfirmView.as_view(template_name='reset_password_form.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         views.PasswordResetCompleteView.as_view(template_name='reset_complete.html'),
         name='password_reset_complete'),
]
