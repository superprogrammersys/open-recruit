from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Application
from api.tasks import send_email


@receiver(post_save, sender=Application)
def notify_stage_change(instance, **kwargs):
    send_email.delay(
        name=instance.candidate_full_name,
        sender=None,  # يستخدم DEFAULT_FROM_EMAIL من settings.py
        subject=f'Update Regarding Your Application - {instance.job.title}',
        message=(
            f'Hello {instance.candidate_full_name},\n\n'
            f'Your application for "{instance.job.title}" '
            f'has been updated to stage: {instance.get_stage_display()}.'
        ),
        receiver=[instance.candidate_email],
    )
