from django.urls import path
from .views import (
    MentorRegisterView,
    VerifyOTPView,
    LoginView,
    PasswordResetView,
    SendOTPView,
    list_students,
    paired_users_view,
    send_message_view,
    get_firebase_token,
    get_user,
)

urlpatterns = [
    path('register/mentor/', MentorRegisterView.as_view(), name='mentor-register'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('students/', list_students, name='list_students'),
    path('pairings/', paired_users_view, name='paired-users'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('send-message/', send_message_view,name='send-mrssage'),
    path('firebase-token/', get_firebase_token),
    path('users/<int:user_id>/', get_user, name='get-user'),



    # path('request-password-reset-otp/', RequestPasswordResetOTPView.as_view(), name='request-password-reset-otp'),
    # path('verify-reset-otp/', VerifyResetOTPView.as_view(), name='verify-reset-otp'),

    

]


