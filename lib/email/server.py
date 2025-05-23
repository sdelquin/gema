import poplib
from typing import Iterator

from logzero import logger

import settings
from lib.email.user import Email
from lib.utils import pluralize


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
