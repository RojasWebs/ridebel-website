from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.test import Client, TestCase, override_settings

from .models import ContactRateLimit


@override_settings(
    SECURE_SSL_REDIRECT=False,
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_HOST='smtp.example.com',
    DEFAULT_FROM_EMAIL='website@example.com',
    CONTACT_RECIPIENT_EMAIL='inbox@example.com',
)
class ContactTests(TestCase):
    def setUp(self):
        self.data = {
            'name': 'Test Visitor', 'email': 'visitor@example.com',
            'phone': '', 'organization': '', 'reason': 'general',
            'message': 'A general question about RideBEL.', 'website': '',
        }

    def test_home_and_static_references(self):
        response = self.client.get('/')
        self.assertContains(response, '/static/images/logo.png')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_delivery_and_redirect_prevents_resubmission(self):
        response = self.client.post('/', self.data)
        self.assertRedirects(response, '/?sent=1#contact')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].reply_to, ['visitor@example.com'])
        self.assertEqual(mail.outbox[0].from_email, 'website@example.com')
        self.assertEqual(mail.outbox[0].to, ['inbox@example.com'])
        self.assertIn(self.data['message'], mail.outbox[0].body)

    def test_invalid_values_never_send(self):
        for changes in ({'email': 'invalid'}, {'reason': 'invalid'}, {'message': 'x' * 5001}):
            response = self.client.post('/', {**self.data, **changes})
            self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_does_not_send(self):
        response = self.client.post('/', {**self.data, 'website': 'spam'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_csrf_is_required(self):
        response = Client(enforce_csrf_checks=True).post('/', self.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)

    def test_smtp_failure_preserves_input_without_error_details(self):
        with patch('transportation.views.EmailMessage.send', side_effect=SMTPException('private details')):
            response = self.client.post('/', self.data)
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, self.data['message'], status_code=503)
        self.assertNotContains(response, 'private details', status_code=503)

    @override_settings(EMAIL_HOST='')
    def test_unconfigured_delivery_never_claims_success(self):
        response = self.client.post('/', self.data)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(len(mail.outbox), 0)

    def test_rate_limit_is_shared_and_expires(self):
        for _ in range(5):
            self.assertEqual(self.client.post('/', self.data).status_code, 302)
        self.assertEqual(self.client.post('/', self.data).status_code, 429)
        self.assertEqual(len(mail.outbox), 5)
        from django.utils import timezone
        ContactRateLimit.objects.update(expires_at=timezone.now())
        self.assertEqual(self.client.post('/', self.data).status_code, 302)

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_https_redirect(self):
        self.assertEqual(self.client.get('/').status_code, 301)
