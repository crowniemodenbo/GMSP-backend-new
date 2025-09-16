from rest_framework import serializers
from .models import User
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
import random, os
from django.core.mail import send_mail
from django.contrib.auth.hashers import check_password


# --- Mentor Registration ---
class MentorRegisterSerializer(serializers.ModelSerializer):
    mentor_intro_video = serializers.FileField(required=False)
    
    class Meta:
        model = User
        fields = ('id','email', 'first_name','last_name', 'title', 'dob','id_number', 'phone','bio' ,'job_title', 'institutional_affiliation','nationality', 'city','mentor_intro_video')

    def validate(self, data):
        # Validate video file if provided
        video = data.get('mentor_intro_video')
        if video:
            # Check file size (limit to 50MB)
            if video.size > 50 * 1024 * 1024:  # 50MB in bytes
                raise serializers.ValidationError({"mentor_intro_video": "Video file too large. Maximum size is 50MB."})
                
            # Check file type (optional)
            valid_types = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-ms-wmv']
            if video.content_type not in valid_types:
                raise serializers.ValidationError({"mentor_intro_video": "Unsupported video format. Please upload MP4, MOV, AVI, or WMV."})
        return data

    def create(self, validated_data):
        # Auto-generate a random password
        import string
        import random
        import logging
        
        logger = logging.getLogger(__name__)

        video_file = validated_data.pop('mentor_intro_video', None)
        
        # Generate a random password with 10 characters including letters, digits, and special characters
        password_characters = string.ascii_letters + string.digits + "!@#$%^&*()"
        auto_password = ''.join(random.choice(password_characters) for i in range(10))
        
        # Set mentor role and inactive status
        validated_data['role'] = 'mentor'
        validated_data['is_active'] = False
        
        # Log if video is in the data
        if 'mentor_intro_video' in validated_data:
            logger.info(f"Video file received: {validated_data['mentor_intro_video']}, type: {type(validated_data['mentor_intro_video'])}")
        else:
            logger.info("No video file in validated_data")
            
        # Create user with auto-generated password
        user = User.objects.create_user(password=auto_password, **validated_data)

        
        # Ensure the video is saved properly
        if video_file:
            ext = os.path.splitext(video_file.name)[1]  # keep original extension (.mp4, .mov, etc.)
            safe_name = f"{user.first_name.lower()}_{user.last_name.lower()}_intro{ext}"
            user.mentor_intro_video.save(safe_name, video_file, save=True)
            logger.info(f"Saved user with video: {user.mentor_intro_video}")

        

        # Send confirmation email to mentor
        send_mail(
            subject="AIMS GMSP Mentor Application",
            message="Thank You for applying as a mentor to the AIMS GMSP.\nWe will reach out to you via email once you're selected.",
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user
    
    



# --- Login Serializer ---


User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")

        if user.role == 'student':
            if not check_password(password, user.password):
                raise serializers.ValidationError("Invalid credentials.")

            if not user.is_active:
                # Student must reset password before activation
                raise serializers.ValidationError({"is_first_login": True})

            if user.password_expiry and timezone.now() > user.password_expiry:
                raise serializers.ValidationError("Your password has expired. Please reset your password.")

            return user

        # Mentor or other roles
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        return user


# --- Password Reset (Confirm) ---
    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

# --- Optional: Password Expiry Check ---
class PasswordExpiryCheckSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UserSerializer(serializers.ModelSerializer):
    mentor_intro_video = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'mentor_intro_video']
    
    def get_mentor_intro_video(self, obj):
        if obj.mentor_intro_video and hasattr(obj.mentor_intro_video, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.mentor_intro_video.url)
            return obj.mentor_intro_video.url
        return None


