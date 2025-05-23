from datetime import datetime
from email import message_from_bytes
from email.header import decode_header

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


def parse_email_contents(contents: list[bytes]) -> tuple:
    """
    Parse email contents and return from, subject, date
    """

    def decode_header_value(header_value):
        if header_value:
            decoded_parts = decode_header(header_value)
            return ''.join(
                [
                    part.decode(charset or 'utf-8') if isinstance(part, bytes) else part
                    for part, charset in decoded_parts
                ]
            )
        return ''

    logger.debug('Parsing email contents')
    message = message_from_bytes(b'\n'.join(contents))
    return (
        decode_header_value(message['from']),
        decode_header_value(message['subject']),
        parse_date(message['date']),
    )


def pluralize(text: str, n: int) -> str:
    if n == 1:
        return text
    return text + 's'


def parse_date(date: str, to_tz=settings.TIMEZONE) -> datetime:
    d = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
    return d.astimezone(pytz.timezone(to_tz))
