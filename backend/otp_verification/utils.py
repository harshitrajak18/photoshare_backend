from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task



@shared_task
def send_email_to_client(email,otp):
    
    subject="OTP for verification"
    message=f"Your otp for User verification is {otp}"
    from_email=settings.EMAIL_HOST_USER
    recipent_list=[email]
    send_mail(subject,message,from_email,recipent_list)  