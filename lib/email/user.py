from logzero import logger
from telegramtk.utils import escape_markdown

from lib.email.utils import parse_email_contents


class Email:
    def __init__(self, id: int, contents: list[bytes]):
        logger.debug(f'Building email with id #{id}')
        self.id = id
        self.from_, self.subject, self.date = parse_email_contents(contents)

    def __str__(self):
        return f'📥 {self.subject} ({self.from_})'

    def as_markdown(self) -> str:
        md = f"""*From*: {escape_markdown(self.from_)}
*Subject*: {escape_markdown(self.subject)}
*Date*: {self.date.strftime('%c')}"""
        return md
