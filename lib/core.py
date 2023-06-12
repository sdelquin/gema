import poplib
import re
from typing import Iterator

import telegram
import yaml
from logzero import logger

import settings

from .utils import decode_content, pluralize


class Email:
    def __init__(self, id: int, payload: list[bytes]):
        logger.debug(f'Building email with id #{id}')
        self.id = id
        self.parse_payload(payload)

    def parse_payload(self, payload: list[bytes]) -> None:
        logger.debug('Parsing payload')
        content = '\n'.join(c.decode('utf-8') for c in payload[::-1])
        if m := re.search(r'^New message received at *(.*)\.', content, re.MULTILINE):
            self.inbox = decode_content(m[1])
        else:
            self.inbox = None
            logger.warning('Inbox could not be parsed')
        if m := re.search(r'^Sender: *(.*) <(.*)>', content, re.MULTILINE):
            self.from_name = decode_content(m[1])
            self.from_email = m[2]
        else:
            self.from_name = None
            self.from_email = None
            logger.warning('From could not be parsed')
        if m := re.search(r'^Subject: *(.*)', content, re.MULTILINE):
            self.subject = decode_content(m[1])
        else:
            self.subject = None
            logger.warning('Subject could not be parsed')
        if m := re.search(r'^Date: *(.*)', content, re.MULTILINE):
            self.date = decode_content(m[1])
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
*Date*: {self.date}
*Inbox*: {self.inbox}'''


class Pop3Server:
    def __init__(self, server_addr: str, username: str, password: str):
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
            payload = self.server.retr(email_id)[1]
            email = Email(email_id, payload)
            yield email

    def delete(self, email: Email) -> None:
        logger.debug(f'✗ Deleting email #{email.id}')
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
    def __init__(
        self, config_path: str = settings.CONFIG_PATH, notify: bool = True, delete: bool = True
    ):
        logger.info(f'Loading config from {config_path}')
        self.config = yaml.load(open(config_path), Loader=yaml.FullLoader)
        self.tgbot = TelegramBot()
        self.notify = notify
        self.delete = delete

        if not self.notify:
            logger.warning('Disabled email notification')
        if not self.delete:
            logger.warning('Disabled email deletion after dispatching')

    def dispatch(self):
        for user_cfg in self.config['users']:
            logger.info(f'👤 Dispatching user {user_cfg["name"]}')
            server = Pop3Server(
                user_cfg['pop3']['addr'], user_cfg['pop3']['username'], user_cfg['pop3']['password']
            )
            for email in server.fetch():
                if (inbox := user_cfg.get('inbox')) is None or email.inbox == inbox:
                    try:
                        logger.info(email)
                        if self.notify:
                            self.tgbot.send(user_cfg['telegram_id'], email.as_markdown())
                    except Exception as err:
                        logger.error(err)
                    else:
                        if self.delete:
                            server.delete(email)
                else:
                    logger.warning('Email inbox is not set in config file')
