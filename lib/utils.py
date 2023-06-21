import email.header
import re
from datetime import datetime
from email import message_from_bytes

import logzero
import pytz
from logzero import logger

import settings


def init_logger():
    logformat = (
        '%(asctime)s '
        '%(color)s'
        '[%(levelname)-8s] '
        '%(end_color)s '
        '%(message)s '
        '%(color)s'
        '(%(filename)s:%(lineno)d)'
        '%(end_color)s'
    )

    console_formatter = logzero.LogFormatter(fmt=logformat)
    file_formatter = logzero.LogFormatter(fmt=logformat, color=False)
    logzero.setup_default_logger(formatter=console_formatter)
    logzero.logfile(
        settings.LOGFILE,
        maxBytes=settings.LOGFILE_SIZE,
        backupCount=settings.LOGFILE_BACKUP_COUNT,
        formatter=file_formatter,
    )
    return logzero.logger


def decode_content(content: str) -> str:
    CHEADER = '=?UTF-8?Q?'
    CFOOTER = '?='
    cleaned_content = re.sub('=?\n', '', content)
    cleaned_content = re.sub(r'={2,}', '=', cleaned_content)
    payload = f'{CHEADER}{cleaned_content}{CFOOTER}'
    text, encoding = email.header.decode_header(payload)[0]
    return text.decode(encoding)


def parse_email_contents(contents: list[bytes]) -> tuple[str | datetime | None, ...]:
    logger.debug('Parsing email contents')
    message = message_from_bytes(b'\n'.join(contents))
    payload = message.get_payload()
    logger.debug(payload)

    # INBOX
    if m := re.search(r'New message received at *(.*)\.', payload):
        inbox = decode_content(m[1])
    else:
        inbox = settings.UNPARSED_PLACEHOLDER
        logger.warning('Inbox could not be parsed')
    # FROM
    if m := re.search(r'Sender: *(.*) <(.*)>', payload):
        from_name = decode_content(m[1])
        from_email = m[2]
    elif m := re.search(r'Sender: *<(.*)>', payload):
        from_name = None
        from_email = m[1]
    elif m := re.search(r'Sender: *(.*)', payload):
        from_name = None
        from_email = m[1]
    else:
        from_name = from_email = settings.UNPARSED_PLACEHOLDER
        logger.warning('From could not be parsed')
    # SUBJECT
    if m := re.search(r'Subject: *(.*)', payload, re.DOTALL | re.MULTILINE):
        subject = decode_content(m[1])
    else:
        subject = settings.UNPARSED_PLACEHOLDER
        logger.warning('Subject could not be parsed')
    # DATE
    if m := re.search(r'.*\+\d+', message['Date']):
        date = parse_date(m[0])
    else:
        date = settings.UNPARSED_PLACEHOLDER
        logger.warning('Date could not be parsed')

    return inbox, from_name, from_email, subject, date


def pluralize(text: str, n: int) -> str:
    if n == 1:
        return text
    return text + 's'


def parse_date(date: str, to_tz=settings.TIMEZONE) -> datetime:
    d = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
    return d.astimezone(pytz.timezone(to_tz))
