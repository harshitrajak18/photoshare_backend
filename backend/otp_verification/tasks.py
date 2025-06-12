from celery import shared_task
from django.core.mail import send_mail
from django.core.mail import send_mail
from django.conf import settings
@shared_task
def send_otp_email(email, otp):
    send_mail(
        'Your OTP Code',
        f'Your OTP is {otp}',
        'tadkatrendy1@gmail.com',
        [email],
        fail_silently=False,
    )
