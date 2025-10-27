# tests/mocks/smtp_mock.py
from unittest.mock import Mock, MagicMock
import smtplib


class MockSMTP:
    """Mock для SMTP сервера"""

    def __init__(self, *args, **kwargs):
        self.sent_emails = []
        self.should_fail = False
        self.fail_on_login = False

    def starttls(self):
        if self.should_fail:
            raise smtplib.SMTPException("TLS failed")
        return True

    def login(self, username, password):
        if self.fail_on_login:
            raise smtplib.SMTPAuthenticationError(535, "Auth failed")
        return True

    def send_message(self, msg):
        if self.should_fail:
            raise smtplib.SMTPException("Send failed")

        self.sent_emails.append(
            {
                "to": msg["To"],
                "subject": msg["Subject"],
                "body": (
                    msg.get_payload()[0].get_payload()
                    if msg.is_multipart()
                    else msg.get_payload()
                ),
            }
        )
        return True

    def quit(self):
        return True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def create_smtp_mock():
    """Создает mock для smtplib.SMTP"""
    return MockSMTP()
