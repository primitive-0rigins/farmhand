from __future__ import annotations

from typing import Protocol


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
