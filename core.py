import poplib
import re
from typing import Iterator

import yaml

import settings


class Email:
    def __init__(self, payload: str):
        if m := re.search(r'^From: *(.*)$', payload, re.MULTILINE):
            self.from_ = m[1]
        if m := re.search(r'^Date: *(.*)$', payload, re.MULTILINE):
            self.date = m[1]
        if m := re.search(r'^Subject: *(.*)$', payload, re.MULTILINE):
            self.subject = m[1]

    def __str__(self):
        return f'''From: {self.from_}
Date: {self.date}
Subject: {self.subject}'''


class Pop3Server:
    def __init__(self, server_addr: str, username: str, password: str):
        self.server = poplib.POP3(server_addr)
        self.server.user(username)
        self.server.pass_(password)

    def fetch(self, delete_after_read: bool = True) -> Iterator[Email]:
        num_emails = len(self.server.list()[1])
        for email_id in range(1, num_emails + 1):
            email_content = self.server.retr(email_id)[1]
            payload = '\n'.join(c.decode('utf-8') for c in email_content)
            email = Email(payload)
            yield email
            if delete_after_read:
                self.server.dele(email_id)

    def __del__(self):
        self.server.quit()


class Email2Tg:
    def __init__(self, config_path: str = settings.CONFIG_PATH):
        self.config = yaml.load(open(config_path), Loader=yaml.FullLoader)

    def dispatch(self):
        for user_cfg in self.config['users']:
            server = Pop3Server(user_cfg['pop3'], user_cfg['username'], user_cfg['password'])
            for email in server.fetch():
                print(email)
