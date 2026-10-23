from datetime import timedelta
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from .forms import ContactForm
from .models import ContactRateLimit


def allow_contact(request):
    now = timezone.now()
    address = request.META.get('REMOTE_ADDR', '')
    if settings.TRUST_PROXY:
        address = request.META.get('HTTP_X_REAL_IP', address)
    key = salted_hmac('contact-rate', address).hexdigest()
    ContactRateLimit.objects.filter(expires_at__lte=now).delete()
    with transaction.atomic():
        ContactRateLimit.objects.get_or_create(
            key=key, defaults={'expires_at': now + timedelta(hours=1)}
        )
        return bool(ContactRateLimit.objects.filter(key=key, count__lt=5).update(count=F('count') + 1))


@sensitive_post_parameters()
@require_http_methods(['GET', 'POST'])
def home(request):
    form = ContactForm(request.POST if request.method == 'POST' else None)
    status = 200
    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data['website']:
            return redirect(reverse('home') + '?sent=1#contact')
        if not allow_contact(request):
            form.add_error(None, 'Too many messages. Please try again in an hour.')
            status = 429
        elif not all([settings.EMAIL_HOST, settings.DEFAULT_FROM_EMAIL, settings.CONTACT_RECIPIENT_EMAIL]):
            form.add_error(None, 'Messaging is temporarily unavailable. Please try again later.')
            status = 503
        else:
            data = form.cleaned_data
            body = '\n'.join([
                f"Name: {data['name']}", f"Email: {data['email']}",
                f"Phone: {data['phone']}", f"Organization: {data['organization']}",
                f"Reason: {dict(form.fields['reason'].choices)[data['reason']]}",
                '', data['message'],
            ])
            try:
                sent = EmailMessage(
                    subject='RideBEL website inquiry', body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.CONTACT_RECIPIENT_EMAIL], reply_to=[data['email']],
                ).send(fail_silently=False)
            except (SMTPException, OSError, ValueError):
                sent = 0
            if sent == 1:
                return redirect(reverse('home') + '?sent=1#contact')
            form.add_error(None, 'Your message could not be sent. Please try again later.')
            status = 503
    elif request.method == 'POST':
        status = 400
    response = render(request, 'index.html', {
        'form': form, 'sent': request.method == 'GET' and request.GET.get('sent') == '1',
    }, status=status)
    response['Cache-Control'] = 'no-store'
    return response


@require_http_methods(['GET', 'HEAD'])
def privacy(request):
    return render(request, 'privacy.html')
