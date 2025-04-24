import pytest
import base64
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
import smtplib
from unittest.mock import MagicMock

from ..context import controllably
from controllably.core.notification import Notifier, EmailNotifier

configs = {
    'message': {
        'headers': {
            'From': 'test_user@gmail.com',
            'To': ['test@example.com'],
            'Subject': 'Test Subject'
        }, 
        'attachment_name': 'test.zip',
        'content': 'Test message at {timestamp}'
    },
    'recipients': ['test@example.com'],
    'service': {
        'server': 'smtp.gmail.com', 
        'port': 587, 
        'tls': True
    },
    'credentials': {
        'username': 'test_user@gmail.com', 
        'keyfile': 'keyfile.txt'
    }
}


class TestNotifier:
    def test_init(self):
        configs['credentials']['keyfile'] = Path(configs['credentials']['keyfile'])
        notifier = Notifier(configs)
        assert notifier.configs == configs

    def test_from_file(self, monkeypatch):
        config_file = Path('config.json')
        monkeypatch.setattr('controllably.core.file_handler.read_config_file', lambda _: configs)
        notifier = Notifier.fromFile(config_file)
        assert notifier.configs == configs
    
    @pytest.mark.parametrize("keyfile_exists", [False, True])
    def test_notify(self, keyfile_exists, monkeypatch, tmp_path):
        keyfile = tmp_path / Path('keyfile.txt')
        keyfile.write_text(base64.b64encode(b'test_password').decode())
        filename = keyfile if keyfile_exists else 'unknown.txt'
        configs['credentials']['keyfile'] = Path(filename)
        if not keyfile_exists:
            monkeypatch.setattr('builtins.input', lambda _: str(keyfile))
        
        with Notifier(configs) as notifier:
            assert notifier._app_password == keyfile
            with pytest.raises(NotImplementedError):
                notifier.writeMessage({})
            with pytest.raises(NotImplementedError):
                notifier.sendMessage({}, '', None)
            notifier.writeMessage = MagicMock(return_value='Test message')
            notifier.sendMessage = MagicMock()
            notifier.notify()
            notifier.writeMessage.assert_called_once()
            notifier.sendMessage.assert_called_once()


class TestEmailNotifier:
    def test_init(self):
        configs['credentials']['keyfile'] = Path(configs['credentials']['keyfile'])
        notifier = EmailNotifier(configs)
        assert notifier.configs == configs
        
    def test_from_file(self, monkeypatch):
        config_file = Path('config.json')
        monkeypatch.setattr('controllably.core.file_handler.read_config_file', lambda _: configs)
        notifier = Notifier.fromFile(config_file)
        assert notifier.configs == configs
        
    def test_write_email(self, tmp_path):
        message_config = configs['message']
        placeholders = {'timestamp': datetime(2025, 3, 21, 10, 0, 0)}
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        email_message = EmailNotifier.writeEmail(
            message_config, placeholders=placeholders,
            attachments=[file1, file2], save_zip=False
        )
        assert isinstance(email_message, EmailMessage)
        assert email_message['From'] == 'test_user@gmail.com'
        assert email_message['To'] == 'test@example.com'
        assert email_message['Subject'] == 'Test Subject'
        simplest = email_message.get_body(preferencelist=('plain', 'html'))
        assert simplest.get_content() == 'Test message at 2025-03-21 10:00:00\n'
    
        now = datetime.now()
        email_message = EmailNotifier.writeMessage(
            message_config, attachments=[file1, file2], save_zip=False
        )
        simplest = email_message.get_body(preferencelist=('plain', 'html'))
        assert simplest.get_content() == f'Test message at {now.strftime("%Y-%m-%d %H:%M:%S")}\n'
        
    def test_send_email(self, monkeypatch, tmp_path):
        keyfile = tmp_path / configs['credentials']['keyfile']
        keyfile.write_text(base64.b64encode(b'test_password').decode())
        configs['credentials']['keyfile'] = keyfile
        
        email_message = EmailMessage()
        email_message['To'] = 'test@example.com'
        email_message.set_content('Test message')
        
        class Mock_Server:
            def __init__(self, server, port):
                pass
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_value, traceback):
                pass
            def starttls(self):
                assert True
            def login(self, username, password):
                assert username == 'test_user@gmail.com'
                assert password == 'test_password'
            def send_message(self, message):
                assert isinstance(message, EmailMessage)
        
        monkeypatch.setattr(smtplib, 'SMTP', lambda a,b: Mock_Server(a,b))
        with EmailNotifier(configs) as email_notifier:
            email_notifier.sendEmail(configs['service'], configs['credentials']['username'], email_message)

        with EmailNotifier(configs) as email_notifier:
            email_notifier._app_password = base64.b64encode(b'test_password')
            email_notifier.sendMessage(configs['service'], configs['credentials']['username'], email_message)
    