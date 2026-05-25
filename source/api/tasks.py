from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
@shared_task()
def send_email(name, sender,subject , message, receiver, file=None):
    message = EmailMessage(
        subject=subject,
    body=message,
    from_email=sender,
    to=receiver,
    )
    if file:
        message.attach(
            filename=file.name,
        content=file.read(),
        mimetype=file.content_type,
)
    message.send()
    return
