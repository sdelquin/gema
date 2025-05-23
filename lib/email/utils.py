import re
from datetime import datetime
from email import message_from_bytes
from email.message import Message
from email.utils import parsedate_to_datetime

import pytz
from logzero import logger

import settings


def extract_body(msg: Message) -> str:
    # Si el mensaje es multipart, recorrer partes
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition'))

            # Saltar archivos adjuntos
            if 'attachment' in content_disposition:
                continue

            if content_type == 'text/plain':
                charset = part.get_content_charset() or 'utf-8'
                return part.get_payload(decode=True).decode(charset, errors='replace')  # type: ignore

        # Si no hay texto plano, buscar HTML como alternativa
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                charset = part.get_content_charset() or 'utf-8'
                return part.get_payload(decode=True).decode(charset, errors='replace')  # type: ignore

    else:
        # Si no es multipart, decodificar directamente
        content_type = msg.get_content_type()
        if content_type in ['text/plain', 'text/html']:
            charset = msg.get_content_charset() or 'utf-8'
            return msg.get_payload(decode=True).decode(charset, errors='replace')  # type: ignore

    return ''


def parse_date(date: str, to_tz=settings.TIMEZONE) -> datetime:
    d = parsedate_to_datetime(date)
    return d.astimezone(pytz.timezone(to_tz))


def parse_email_contents(contents: list[bytes], inbox=settings.INBOX) -> tuple:
    """
    Parse email contents and return from, subject, date
    """

    logger.debug('Parsing email contents')
    message = message_from_bytes(b'\n'.join(contents))
    if not (body := extract_body(message)):
        raise ValueError('No body found in email')
    if inbox not in body:
        raise ValueError(f'Inbox «{inbox}» not found in email body')
    try:
        from_ = re.search('Sender: *(.*)', body).group(1)  # type: ignore
        subject = re.search('Subject: *(.*)', body).group(1)  # type: ignore
    except AttributeError as err:
        raise ValueError('No sender or subject found in email body') from err
    date = parse_date(message['date'])
    return from_, subject, date
