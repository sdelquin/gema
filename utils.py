import email.header
import re

import logzero

import settings


def init_logger():
    console_logformat = (
        '%(asctime)s '
        '%(color)s'
        '[%(levelname)-8s] '
        '%(end_color)s '
        '%(message)s '
        '%(color)s'
        '(%(filename)s:%(lineno)d)'
        '%(end_color)s'
    )
    # remove colors on logfile
    file_logformat = re.sub(r'%\((end_)?color\)s', '', console_logformat)

    console_formatter = logzero.LogFormatter(fmt=console_logformat)
    file_formatter = logzero.LogFormatter(fmt=file_logformat)
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
    payload = f'{CHEADER}{content}{CFOOTER}'
    text, encoding = email.header.decode_header(payload)[0]
    return text.decode(encoding)


def pluralize(text: str, n: int) -> str:
    if n == 1:
        return text
    return text + 's'
