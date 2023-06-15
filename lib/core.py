import poplib
import re
from email import message_from_bytes
from typing import Iterator

import telegram
from logzero import logger

import settings

from .utils import decode_content, parse_date, pluralize


class Email:
    def __init__(self, id: int, contents: list[bytes]):
        logger.debug(f'Building email with id #{id}')
        self.id = id
        self.parse_contents(contents)

    def parse_contents(self, contents: list[bytes]) -> None:
        logger.debug('Parsing payload')
        message = message_from_bytes(b'\n'.join(contents))
        payload = message.get_payload()
        logger.debug(payload)
        if m := re.search(r'^New message received at *(.*)\.', payload):
            self.inbox = decode_content(m[1])
        else:
            self.inbox = None
            logger.warning('Inbox could not be parsed')
        if m := re.search(r'Sender: *(.*) <(.*)>', payload):
            self.from_name = decode_content(m[1])
            self.from_email = m[2]
        else:
            self.from_name = None
            self.from_email = None
            logger.warning('From could not be parsed')
        if m := re.search(r'Subject: *(.*)', payload, re.DOTALL | re.MULTILINE):
            self.subject = decode_content(m[1])
        else:
            self.subject = None
            logger.warning('Subject could not be parsed')
        if m := re.search(r'.*\+\d+', message['Date']):
            self.date = parse_date(m[0])
        else:
            self.date = None
            logger.warning('Date could not be parsed')

    @property
    def from_(self) -> str:
        return f'{self.from_name} <{self.from_email}>'

    def __str__(self):
        return f'📥 {self.subject} ({self.from_email})'

    def as_markdown(self) -> str:
        return f'''*From*: {self.from_}
*Subject*: {self.subject}
*Date*: {self.date.strftime('%c')}
*Inbox*: {self.inbox}'''


class Pop3Server:
    def __init__(
        self,
        server_addr: str = settings.POP3_SERVER,
        username: str = settings.POP3_USERNAME,
        password: str = settings.POP3_PASSWORD,
    ):
        logger.debug(f'Building pop3 server at {server_addr}')
        self.server = poplib.POP3(server_addr)
        self.server.user(username)
        self.server.pass_(password)

    def fetch(self) -> Iterator[Email]:
        logger.info('👀 Fetching new emails')
        num_emails = len(self.server.list()[1])
        flag = '✨' if num_emails > 0 else '👎'
        logger.debug(f'{flag} {num_emails} new {pluralize("email", num_emails)}')
        for email_id in range(1, num_emails + 1):
            logger.debug(f'Retrieving content #{email_id} from server')
            contents = self.server.retr(email_id)[1]
            email = Email(email_id, contents)
            yield email

    def delete(self, email: Email) -> None:
        logger.debug(f'✗ Deleting email #{email.id} from pop3 server')
        self.server.dele(email.id)

    def __del__(self):
        logger.debug('Quitting pop3 server')
        self.server.quit()


class TelegramBot:
    def __init__(self, token: str = settings.TELEGRAM_BOT_TOKEN):
        logger.debug('Building Telegram Bot')
        self.bot = telegram.Bot(token)

    def send(self, chat_id: str, text: str):
        logger.debug(f'Sending message to chat id {chat_id} through Telegram Bot')
        self.bot.send_message(chat_id=chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)


class GobCanEmailAlarm:
    def __init__(self, notify: bool = True, delete: bool = True):
        self.server = Pop3Server()
        self.tgbot = TelegramBot()
        self.notify = notify
        self.delete = delete

        if not self.notify:
            logger.warning('Disabled email notification')
        if not self.delete:
            logger.warning('Disabled email deletion after dispatching')

    def dispatch(self, inbox: str = settings.INBOX, telegram_chat_id=settings.TELEGRAM_CHAT_ID):
        logger.info(f'👤 Dispatching inbox {inbox}')
        for email in self.server.fetch():
            if inbox is None or email.inbox == inbox:
                try:
                    logger.info(email)
                    if self.notify:
                        self.tgbot.send(telegram_chat_id, email.as_markdown())
                except Exception as err:
                    logger.error(err)
                else:
                    if self.delete:
                        self.server.delete(email)
            else:
                logger.warning(f'Email inbox "{inbox}" is not set in settings')
