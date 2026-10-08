#!/usr/bin/env python3
"""
Institutional Email Dispatcher via Gmail SMTP (TLS 587)
=========================================================
Dispatches rendered HTML research briefings, newsletters, and portfolio audits
to the configured recipient using credentials stored in `.env`.

Usage:
  python3 scripts/send_email.py --subject "Daily Market Intelligence" --html-file "docs/reports/Daily_Market_Intelligence_2026-09-27.html"
"""

import os
import sys
import argparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def load_env(env_path='.env'):
    """Load key-value pairs from .env into os.environ if present."""
    if not os.path.exists(env_path):
        # Try finding .env in parent directory
        parent_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
        if os.path.exists(parent_env):
            env_path = parent_env

    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v

def send_email_html(subject, html_content, recipient=None, text_fallback=None):
    """Send an HTML email via smtp.gmail.com:587 using GMAIL_USER and GMAIL_APP_PASSWORD."""
    load_env()

    gmail_user = os.getenv('GMAIL_USER') or os.getenv('GMAIL_ADDRESS') or os.getenv('EMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD') or os.getenv('GMAIL_PASSWORD') or os.getenv('EMAIL_PASSWORD')
    
    if not recipient:
        recipient = os.getenv('GMAIL_RECIPIENT') or 'rajasekharreddymekala732@gmail.com'

    if not gmail_user or not gmail_password:
        raise ValueError("Missing GMAIL_USER or GMAIL_APP_PASSWORD in environment / .env file.")

    # Remove any internal spaces in 16-character app passwords if present (e.g. 'abcd efgh ijkl mnop')
    gmail_password = gmail_password.replace(" ", "")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"Portfolio Research Desk <{gmail_user}>"
    msg['To'] = recipient

    if not text_fallback:
        text_fallback = f"Please view this email in an HTML-compatible email client to read the complete research briefing: {subject}."

    part1 = MIMEText(text_fallback, 'plain', 'utf-8')
    part2 = MIMEText(html_content, 'html', 'utf-8')

    msg.attach(part1)
    msg.attach(part2)

    # Try SSL (port 465) first, then fallback to STARTTLS (port 587)
    sent = False
    try:
        print(f"Connecting to smtp.gmail.com:465 (SSL) as {gmail_user}...", flush=True)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [recipient], msg.as_string())
        sent = True
    except Exception as ssl_err:
        print(f"Port 465 SSL failed ({ssl_err}), trying port 587 STARTTLS...", flush=True)
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [recipient], msg.as_string())
        sent = True

    if sent:
        print(f"✅ Successfully dispatched email '{subject}' to {recipient} via Gmail SMTP.")
        return True

def main():
    parser = argparse.ArgumentParser(description="Dispatch HTML email via Gmail SMTP.")
    parser.add_argument('--subject', required=True, help="Email Subject line")
    parser.add_argument('--html-file', required=True, help="Path to HTML newsletter/report file")
    parser.add_argument('--recipient', default=None, help="Recipient email address (defaults to .env or rajasekharreddymekala732@gmail.com)")
    
    args = parser.parse_args()

    if not os.path.exists(args.html_file):
        print(f"❌ Error: HTML file '{args.html_file}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(args.html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    try:
        send_email_html(args.subject, html_content, recipient=args.recipient)
    except Exception as e:
        print(f"❌ Failed to send email: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
