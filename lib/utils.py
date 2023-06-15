import email.header
import re
from datetime import datetime

import logzero
import pytz

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
    cleaned_content = re.sub('\n', '', content)
    cleaned_content = re.sub(r'={2,}', '=', cleaned_content)
    payload = f'{CHEADER}{cleaned_content}{CFOOTER}'
    text, encoding = email.header.decode_header(payload)[0]
    return text.decode(encoding)


def pluralize(text: str, n: int) -> str:
    if n == 1:
        return text
    return text + 's'


def parse_date(date: str, to_tz=settings.TIMEZONE) -> datetime:
    d = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
    return d.astimezone(pytz.timezone(to_tz))
