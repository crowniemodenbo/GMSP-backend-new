from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta,datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, FormParser
from .firebase.firebase import db

import logging
import random


from .models import User,Pairing
from .serializers import (
    MentorRegisterSerializer,
    LoginSerializer,
    PasswordResetSerializer,
    UserSerializer
)


logger = logging.getLogger(__name__)

# --- Mentor Registration ---
class MentorRegisterView(generics.CreateAPIView):
    serializer_class = MentorRegisterSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        # Log the request content type and files
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request FILES: {request.FILES}")
        
        # Check if there's a file in the request
        if 'mentor_intro_video' in request.FILES:
            logger.info(f"Video file found in request: {request.FILES['mentor_intro_video']}")
            # Ensure the file is properly attached to the request data
            request.data._mutable = True
            request.data['mentor_intro_video'] = request.FILES['mentor_intro_video']
            request.data._mutable = False
        
        # Continue with the standard create view process
        return super().post(request, *args, **kwargs)


from rest_framework.exceptions import AuthenticationFailed

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        try:
            logger.debug(f"Received login request: {request.data}")

            # Deserialize the request data
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)  # This raises ValidationError if bad credentials

            # Get the authenticated user from serializer's validated data
            user = serializer.validated_data
            logger.debug(f"Authenticated user: {user.email} (role={user.role})")

            password_expired = False
            is_first_login = False

            # Logic specific to student accounts
            if user.role == 'student':
                # Check if password expired
                if user.password_expiry and timezone.now() > user.password_expiry:
                    password_expired = True

                # If the student is logging in for the first time, set is_first_login to True
                if not user.is_active:
                    is_first_login = True
                    user.is_active = True  # Mark as active after first login
                    user.save()
                    logger.info(f"Activated student account: {user.email}")

                # If password hasn't expired and account is active, clear the expiry date
                if user.is_active and not password_expired:
                    user.password_expiry = None
                    user.save()
                    logger.info(f"Cleared password expiry for: {user.email}")

            # For mentors, set 'is_first_time_login' to False once they log in
            if user.role == 'mentor' and user.is_active:
                user.is_first_time_login = False  # Update first-time login flag
                user.save()

            # Generate refresh and access tokens for the user
            refresh = RefreshToken.for_user(user)

            # Return response with tokens and user information
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'password_expired': password_expired,
                'is_first_login': is_first_login,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.first_name + user.last_name ,
                    'role': user.role,
                    'first_name':user.first_name,
                    'last_name':user.last_name, 
                    'title':user.title, 
                    'phone':user.phone,
                    'bio':user.bio,
                    'job_title':user.job_title, 
                    'institutional_affiliation':user.institutional_affiliation,
                    'nationality':user.nationality,
                    'city':user.city,
                }
            }, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            logger.warning(f"Validation error during login: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error in LoginView: {e}")
            return Response({"detail": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class VerifyOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        purpose = request.data.get('purpose', 'registration')  # default is 'registration'

        if not email or not otp:
            return Response({'error': 'Email and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)


        try:
            user = User.objects.get(email=email)

            # ✅ Check if OTP expired (valid for 10 minutes)
            if user.otp_created_at and timezone.now() > user.otp_created_at + timedelta(minutes=10):
                return Response({'error': 'OTP expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

            if user.email_otp != otp:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Correct OTP, Activate account
            if purpose == 'registration':
                user.is_active = True  # Only activate account during registration
            user.email_otp = None
            user.otp_created_at = None
            user.save()

            return Response({'message': f'Email verified successfully for {purpose}. You can now login.'})

        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)



class ResendOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({'error': 'Account is already active.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate a new OTP
            otp = str(random.randint(100000, 999999))
            user.email_otp = otp
            user.otp_created_at = timezone.now()  # 🆕 Save the time
            user.save()


            # Send the new OTP
            send_mail(
                subject="Your New GSMP Verification OTP",
                message=f"Your new OTP is {otp}",
                from_email="noreply@gsmp.com",
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({'message': 'New OTP sent to your email.'})
        
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)



# --- Password Reset Confirm ---

class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.password_expiry = None  # ✅ Clear password expiry

            # ✅ Only activate student accounts
            if user.role == 'student':
                user.is_active = True

            user.save()

            return Response({"message": "Password reset successful."})
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_students(request):
    students = User.objects.filter(role='student', is_active=True)
    serializer = UserSerializer(students, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def paired_users_view(request):
    user = request.user

    if user.role == 'mentor':
        students = [p.student for p in Pairing.objects.filter(mentor=user)]
        serializer = UserSerializer(students, many=True, context={'request': request})
        return Response({'paired_students': serializer.data})
    
    elif user.role == 'student':
        mentors = [p.mentor for p in Pairing.objects.filter(student=user)]
        serializer = UserSerializer(mentors, many=True, context={'request': request})
        return Response({'paired_mentors': serializer.data})
    
    return Response({'error': 'Invalid role'}, status=400)




class SendOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        purpose = request.data.get('purpose', 'registration')  # 'registration' or 'password_reset'

        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if purpose == 'registration' and user.is_active:
                return Response({'error': 'User already verified. Please log in.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            if purpose == 'password_reset':
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            # Create inactive user for registration
            user = User.objects.create(email=email, is_active=False)

        otp = str(random.randint(100000, 999999))
        user.email_otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        # You can customize this with templates or an email service
        send_mail(
            subject='Your OTP Code',
            message=f'Your OTP is: {otp}',
            from_email=None,
            recipient_list=[email],
             fail_silently=False,
        )

        return Response({'message': f'OTP sent to {email}.'}, status=status.HTTP_200_OK)
    
   

   # myproject/views/chat.py


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_view(request):
    data = request.data
    chat_id = data.get('chat_id')
    text = data.get('text')

    if not chat_id or not text:
        return Response({'error': 'chat_id and text are required'}, status=400)

    sender = request.user

    message = {
        'text': text.strip(),
        'senderId': sender.id,
        'senderName': sender.first_name + sender.last_name,
        'timestamp': datetime.utcnow(),
    }

    try:
        db.collection('chats').document(chat_id).collection('messages').add(message)
        return Response({'status': 'Message sent'})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# views.py
from firebase_admin import auth as firebase_auth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_firebase_token(request):
    user = request.user
    uid = f"user_{user.id}"  # Firebase UID must be unique and string

    # Optional custom claims (e.g., user role)
    additional_claims = {
        "full_name": user.first_name + user.last_name,
        "email": user.email,
        "first_name":user.first_name,
        "last_name":user.last_name
    }

    # Generate Firebase custom token
    firebase_token = firebase_auth.create_custom_token(uid, additional_claims)

    return Response({"firebase_token": firebase_token.decode('utf-8')})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)

    serializer = UserSerializer(user)
    return Response(serializer.data)