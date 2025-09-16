import csv
import random
import string
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from users.models import User

class Command(BaseCommand):
    help = 'Import students from a CSV file, generate random passwords, email them, and mark password as expired.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def generate_password(self, length=10):
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(characters) for _ in range(length))

    def handle(self, *args, **kwargs):
        file_path = kwargs['csv_file']

        try:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    email = row['email'].strip()
                    if User.objects.filter(email=email).exists():
                        self.stdout.write(self.style.WARNING(f"Skipping existing student: {email}"))
                        continue

                    temp_password = self.generate_password()

                    user = User.objects.create_user(
                        email=email,
                        password=temp_password,
                        full_name=row['full_name'],
                        id_number=row.get('id_number'),
                        phone=row.get('phone'),
                        dob=row.get('dob'),
                        nationality=row.get('nationality'),
                        city=row.get('city'),
                        role='student',
                        is_first_login=True,       
                        password_expiry=None    
                    )

                    try:
                        send_mail(
                            subject='Welcome to GSMP - Your Account Details',
                            message=f'''
Hello {user.full_name},

Your GSMP student account has been created!

Here are your login credentials:
Email: {user.email}
Temporary Password: {temp_password}

⚡ IMPORTANT: You must reset your password after first login.

Visit the login page:http://localhost:3000/login

Thanks,  
The GSMP Team
''',
                            from_email=None,  # Uses DEFAULT_FROM_EMAIL
                            recipient_list=[user.email],
                            fail_silently=False,
                        )
                        self.stdout.write(self.style.SUCCESS(f"Student {email} created and emailed successfully!"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"User created but failed to send email to {email}. Error: {str(e)}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"CSV file not found at: {file_path}"))
