from django.urls import path
from . import  views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    #path('login/', views.user_login, name='login'),
    path('login/', views.AccountLoginView.as_view(), name='login'),
    path('logout/', views.AccountLogoutView.as_view(), name='logout'),
    path('password-change/', views.AccountPasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', views.AccountPasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password-reset/', views.AccountPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.AccountPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.AccountPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.AccountPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
    path('users/', views.user_list, name='user_list'),
    path('users/follow/', views.user_follow, name='user_follow'),
    path('users/<username>/', views.user_detail, name='user_detail'),
]