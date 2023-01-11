from payment_record.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

User = get_user_model()


# email for requesting admins approval
def send_pending_email(user, current_site, subject_heading, reason):
    subject = subject_heading + " REQUEST - MARGINS ID SYSTEM"
    recipients = []
    admins = User.objects.filter(is_staff=True)
    for i in admins:
        recipients.append(i.email)
    message = render_to_string('users/request_approval_email.html', {
        'user': user,
        'domain': current_site,
        'heading': subject_heading,
        'reason': reason
    })
    send_mail(subject, message, EMAIL_HOST_USER, recipients, fail_silently=False)


def send_pending_feedback_email(user, current_site, heading, admin, info, action):
    subject = "MARGINS ID SYSTEM"
    recipients = [user]
    message = render_to_string('pending_approvals/pending_request_action_taken_email.html', {
        'user': user,
        'domain': current_site,
        'heading': heading,
        'admin': admin,
        'info': info,
        'action': action
    })
    send_mail(subject, message, EMAIL_HOST_USER, recipients, fail_silently=False)

