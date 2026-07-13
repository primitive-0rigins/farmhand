from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Protocol
from urllib.parse import urlencode


class EmailSender(Protocol):
    """Delivers a login link. Kept behind an adapter like the other providers,
    so a real SMTP/transactional sender swaps in without touching auth logic."""

    def send_magic_link(self, email: str, token: str) -> None:
        ...


class ConsoleEmailSender:
    """Dev sender: prints the login token to the server log instead of emailing.

    The token never appears in an API response unless FARMHAND_DEV_AUTH is set.
    """

    def send_magic_link(self, email: str, token: str) -> None:
        print(f"[farmhand] magic-link login token for {email}: {token}")


class SmtpEmailSender:
    """Minimal TLS SMTP adapter for a configured production sender."""

    def __init__(self, host: str, port: int, sender: str, username: str | None, password: str | None, app_url: str) -> None:
        self.host = host
        self.port = port
        self.sender = sender
        self.username = username
        self.password = password
        self.app_url = app_url

    def send_magic_link(self, email: str, token: str) -> None:
        separator = "&" if "?" in self.app_url else "?"
        login_url = f"{self.app_url}{separator}{urlencode({'token': token})}"
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = email
        message["Subject"] = "Sign in to Farmhand"
        message.set_content(f"Use this one-time Farmhand sign-in link: {login_url}")
        with smtplib.SMTP(self.host, self.port) as client:
            client.starttls()
            if self.username and self.password:
                client.login(self.username, self.password)
            client.send_message(message)
