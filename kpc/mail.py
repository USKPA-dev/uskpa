
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


User = get_user_model()


def edit_request_email_context(request, edit_request):
    """prepare context for rendering edit request notifications"""
    return {'edit_request': edit_request,
            'cert_url': request.build_absolute_uri(edit_request.certificate.get_absolute_url()),
            'home_url': request.build_absolute_uri('/'),
            'review_url': request.build_absolute_uri(edit_request.get_absolute_url())
            }


def _build_email(context, template_name):
    subject = render_to_string(f"mail/{template_name}_subject.txt", context)
    text = render_to_string(f"mail/{template_name}.txt", context)
    html = render_to_string(f"mail/{template_name}.html", context)
    return subject, text, html


def get_reviewer_emails():
    """Return list of Reviewer user's email addresses"""
    users = User.objects.filter(is_active=True, groups__name='Reviewer')
    return [user.email for user in users]


def notify_reviewers(request, edit_request):
    """Notify reviewers upon submission of a new EditRequest"""
    context = edit_request_email_context(request, edit_request)
    subject, text, html = _build_email(context, 'edit_request_submitted')
    msg = EmailMultiAlternatives(subject=subject, to=get_reviewer_emails(), body=text)
    msg.attach_alternative(html, "text/html")
    msg.send()


def notify_requester_of_completed_review(request, edit_request):
    context = edit_request_email_context(request, edit_request)
    subject, text, html = _build_email(context, 'edit_request_reviewed')
    msg = EmailMultiAlternatives(
        subject=subject, to=[edit_request.contact.email], body=text)
    msg.attach_alternative(html, "text/html")
    msg.send()
