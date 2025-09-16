

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('mentor', 'Mentor'),
        ('student', 'Student'),
    )
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.full_name or self.username
   

    email = models.EmailField(unique=True)
    email_otp = models.CharField(max_length=6, blank=True, null=True)  # NEW FIELD
    otp_created_at = models.DateTimeField(blank=True, null=True)

    title = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # mentor/student fields
    id_number = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    bio= models.CharField(max_length=500, blank=True, null=True)
    job_title=models.CharField(max_length=100, blank=True, null=True)
    institutional_affiliation= models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    mentor_intro_video = models.FileField(upload_to='mentor_videos/', blank=True, null=True)
    password_expiry = models.DateTimeField(blank=True, null=True)  # For students
    is_first_login = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Pairing(models.Model):
    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'mentor'},
        related_name='paired_students'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='paired_mentors'
    )

    class Meta:
        unique_together = ('mentor', 'student')

    def __str__(self):
        return f"{self.mentor.full_name} ↔ {self.student.full_name}"
