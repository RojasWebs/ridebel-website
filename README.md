# RideBEL

Django website for BEL Transportation NYC LLC. Existing launch notice, blue branding, and artwork are preserved. Transportation services remain described as planned.

## Local development

Use Python 3.12 or newer. Create a virtual environment and install `requirements.txt`. Copy `.env.example` to `.env`, generate a unique `DJANGO_SECRET_KEY`, set `DJANGO_DEBUG=true` and `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` for local development. Keep `.env` private (mode 600). Run:

```
python manage.py migrate
python manage.py test
python manage.py runserver
```

SQLite is sufficient for this small single-server site when stored on durable disk. Its migrations support Django admin/sessions and a shared contact rate limit. Contact messages are emailed and are not saved in the database. Rate limits retain a keyed address hash for up to one hour and expire on subsequent submissions. Back up the database securely before production migrations; do not replace an existing production database with the local file.

## Contact delivery

Set `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, and `CONTACT_RECIPIENT_EMAIL` in the private environment. SMTP providers that use API keys normally accept the key as `EMAIL_HOST_PASSWORD`; follow the selected provider's SMTP settings and verify the sender domain. Use TLS on port 587 or set `EMAIL_USE_SSL=true` and `EMAIL_USE_TLS=false` for port 465. Never commit credentials or use a console email backend in production. The app reports success only after the mail backend accepts the message; actual inbox delivery must be checked separately. Delivery failures preserve input with a generic error.

The form uses CSRF protection, bounded validated fields, a honeypot, and a database-backed limit of five valid submission attempts per address per hour. For the supplied trusted Nginx configuration, set `DJANGO_TRUST_PROXY=true`: Nginx overwrites forwarded headers, and Gunicorn binds to loopback. Do not enable this setting for an app directly exposed to untrusted clients. Shared networks may share the contact rate limit.

## Production deployment

The files under `deploy/` are templates for a single Linux server, not a record of the live server configuration. Adapt their account and installation path to the existing server. Inspect existing services and take a private backup before changing them. Keep all infrastructure inventory and credentials outside this repository.

1. Install dependencies in the server environment. Preserve the existing private environment and database; add the email settings and disable debug. Ensure the service account can write the SQLite database and its parent folder. Restrict database files to the service account.
2. Run `python manage.py migrate --check` to inspect pending migrations, back up the database using SQLite's backup facility, then run `python manage.py migrate`.
3. Run `python manage.py test`, `python manage.py check --deploy`, `python manage.py collectstatic --noinput`, and `gunicorn --check-config ridebel.wsgi:application`. Ensure Nginx can read the collected static files. Never serve the project directory, private environment, or database as static content.
4. Adapt/install the service and Nginx templates, run `nginx -t`, then restart Gunicorn and reload Nginx. Restrict inbound traffic to HTTP/HTTPS and administrative access. Publicly reject unknown host names in the server's default Nginx virtual host.
5. Point the domain and www DNS to the verified server, removing conflicting old Google Sites/forwarding records. Check both A and AAAA records; publish IPv6 only if configured. Preserve mail-related DNS records. Obtain a certificate covering both names, configure HTTPS and HTTP redirects, and verify automatic renewal. `certbot --nginx -d ridebel.com -d www.ridebel.com` can configure the certificate after DNS resolves correctly. Run `certbot renew --dry-run`.
6. Check both names over HTTPS, HTTP redirects, contact CSRF/error/success behavior, actual receipt of a general test inquiry, and CSS/logo/hero URLs. Confirm the app is served by the intended deployment and that private files return no content. Test desktop and mobile layouts. Keep the existing deployment available for rollback until these checks pass.

Production defaults enforce HTTPS and secure cookies. The deployment check intentionally warns about HSTS on all subdomains and preload: these are not enabled until every subdomain's HTTPS support is known. Application logging does not record request payloads, credentials, or tracebacks. Configure any external monitoring to record only sanitized status/counts; never form data or private environment values.
