import poplib
from typing import Iterator

import telegram
from logzero import logger

import settings

from .utils import parse_email_contents, pluralize


class Email:
    def __init__(self, id: int, contents: list[bytes], include_inbox=settings.INCLUDE_INBOX):
        logger.debug(f'Building email with id #{id}')
        self.id = id
        self.include_inbox = include_inbox
        self.inbox, self.from_name, self.from_email, self.subject, self.date = parse_email_contents(
            contents
        )

    @property
    def from_(self) -> str:
        if self.from_name is None:
            return self.from_email
        else:
            return f'{self.from_name} <{self.from_email}>'

    def __str__(self):
        return f'📥 {self.subject} ({self.from_email})'

    def as_markdown(self) -> str:
        md = f'''*From*: {self.from_}
*Subject*: {self.subject}
*Date*: {self.date.strftime('%c')}'''
        if self.include_inbox:
            md += f'\n*Inbox*: {self.inbox}'
        return md


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

    def fetch(self) -> Iterator[Email | None]:
        logger.info('👀 Fetching new emails')
        num_emails = len(self.server.list()[1])
        flag = '✨' if num_emails > 0 else '👎'
        logger.debug(f'{flag} {num_emails} new {pluralize("email", num_emails)}')
        for email_id in range(1, num_emails + 1):
            logger.debug(f'Retrieving content #{email_id} from server')
            contents = self.server.retr(email_id)[1]
            try:
                email = Email(email_id, contents)
            except ValueError as err:
                logger.error(f'🚨 {err}')
                yield None
            else:
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
            if email is None:
                logger.warning('Skipping this email')
                continue
            if inbox and email.inbox != inbox:
                logger.warning(f'Email inbox "{email.inbox}" is not set in settings')
                continue
            try:
                logger.info(email)
                if self.notify:
                    self.tgbot.send(telegram_chat_id, email.as_markdown())
            except Exception as err:
                logger.error(err)
            else:
                if self.delete:
                    self.server.delete(email)
