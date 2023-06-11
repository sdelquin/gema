import email.header as email_header
import poplib
import re
from typing import Iterator

import telegram
import yaml

import settings


class Email:
    def __init__(self, id: int, payload: str):
        self.id = id
        self.inbox = self.from_ = self.subject = self.date = None
        if m := re.search(r'^New message received at *(.*)\.', payload, re.MULTILINE):
            self.inbox = Email.decode_content(m[1])
        if m := re.search(r'^Sender: *(.*)', payload, re.MULTILINE):
            self.from_ = Email.decode_content(m[1])
        if m := re.search(r'^Subject: *(.*)', payload, re.MULTILINE):
            self.subject = Email.decode_content(m[1])
        if m := re.search(r'^Date: *(.*)', payload, re.MULTILINE):
            self.date = Email.decode_content(m[1])

    def __str__(self):
        return f'''From: {self.from_}
Subject: {self.subject}'''

    def as_markdown(self) -> str:
        return f'''*Inbox*: {self.inbox}
*Date*: {self.date}
*From*: {self.from_}
*Subject*: {self.subject}'''

    @staticmethod
    def decode_content(content: str) -> str:
        CHEADER = '=?UTF-8?Q?'
        CFOOTER = '?='
        payload = f'{CHEADER}{content}{CFOOTER}'
        text, encoding = email_header.decode_header(payload)[0]
        return text.decode(encoding)


class Pop3Server:
    def __init__(self, server_addr: str, username: str, password: str):
        self.server = poplib.POP3(server_addr)
        self.server.user(username)
        self.server.pass_(password)

    def fetch(self) -> Iterator[Email]:
        num_emails = len(self.server.list()[1])
        for email_id in range(1, num_emails + 1):
            email_content = self.server.retr(email_id)[1]
            payload = '\n'.join(c.decode('utf-8') for c in email_content[::-1])
            email = Email(email_id, payload)
            yield email

    def delete(self, email: Email) -> None:
        self.server.dele(email.id)

    def __del__(self):
        self.server.quit()


class TelegramBot:
    def __init__(self, token: str = settings.TELEGRAM_BOT_TOKEN):
        self.bot = telegram.Bot(token)

    def send(self, chat_id: str, text: str):
        self.bot.send_message(chat_id=chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)


class Email2Tg:
    def __init__(self, config_path: str = settings.CONFIG_PATH):
        self.config = yaml.load(open(config_path), Loader=yaml.FullLoader)
        self.tgbot = TelegramBot()

    def dispatch(self):
        for user_cfg in self.config['users']:
            server = Pop3Server(
                user_cfg['pop3']['addr'], user_cfg['pop3']['username'], user_cfg['pop3']['password']
            )
            for email in server.fetch():
                if (inbox := user_cfg.get('inbox')) is None or email.inbox == inbox:
                    try:
                        print(email)
                        self.tgbot.send(user_cfg['telegram_id'], email.as_markdown())
                    except Exception as err:
                        raise err
                    else:
                        server.delete(email)
